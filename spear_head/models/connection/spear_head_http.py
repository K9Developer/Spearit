# main.py
from datetime import datetime, timezone, timedelta
import threading
from typing import Any, Dict
from fastapi import Body, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy import text

from constants.constants import TOKEN_VALIDITY_DURATION_HOURS, SPEAR_HEAD_API_PORT
from databases.engine import SessionMaker
from models.events.types import campaign
from models.logger import Logger
from models.managers.campaign_manager import CampaignManager
from models.managers.device_manager import DeviceManager
from models.managers.event_manager import EventManager
from models.managers.heartbeat_manager import HeartbeatManager
from models.managers.notification_manager import NotificationManager
from models.managers.user_manager import UserManager
from spear_head import PUBLIC_SPEAR_HEAD_DATA
from utils.https_utils import ensure_self_signed_cert
from utils.jwt_utils import decode_user_token, make_user_token
from utils.permission_utils import ActionTarget, UserAction, UserPermissionResponse, check_user_permission, from_json_permissions, verify_token_validity
import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
class HTTPResponse():

    @staticmethod
    def ok(response: Response, message: str, data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        response.status_code = 200
        res: Dict[str, Any] = {"status": "ok", "message": message}
        if data is not None:
            res["data"] = data
        return res
    
    @staticmethod
    def error(response: Response, message: str) -> Dict[str, Any]:
        return {"status": "error", "message": message}

    @staticmethod
    def permission_denied(response: Response) -> Dict[str, Any]:
        response.status_code = 403
        return {"status": "error", "message": "Permission denied"}    
    
    @staticmethod
    def token_error(response: Response) -> Dict[str, Any]:
        response.status_code = 401
        return {"status": "error", "message": "Invalid or expired session token"}


def has_permission(token: str, action: UserAction, target: ActionTarget) -> UserPermissionResponse:
    return check_user_permission(token, action, target)

def permission_error_to_http_response(perm_response: UserPermissionResponse, response: Response) -> Dict[str, Any]:
    if perm_response == UserPermissionResponse.ALLOWED:
        return HTTPResponse.ok(response, "Permission granted")
    if perm_response == UserPermissionResponse.DENIED:
        return HTTPResponse.permission_denied(response)
    return HTTPResponse.error(response, "Invalid session")

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/")
def root():
    return {"ok": True, "message": "hello"}

@app.post("/users")
def create_new_user(
        request: Request,
        response: Response,
        name: str = Body(...),
        email: str = Body(...),
        password: str = Body(...),
        permissions: list[Any] = Body(...),
        token: str = Body(...)
    ):
    if (res := check_user_permission(token, UserAction.CREATE_USER, ActionTarget.none())) != UserPermissionResponse.ALLOWED:
        return permission_error_to_http_response(res, response)

    res = UserManager.create_user(name, email, password, from_json_permissions(permissions))
    if res is None:
        return HTTPResponse.error(response, "Failed to create user")
    
    return HTTPResponse.ok(response, "User created successfully", {"session": res.token})

@app.post("/users/login_user_credentials")
def login_user_credentials(
        response: Response,
        email: str = Body(...),
        password: str = Body(...),
    ):
    user = UserManager.get_user_by_email(email)
    if user is None or user.user_id is None:
        Logger.warn(f"Login failed for email: {email}")
        return HTTPResponse.error(response, "Invalid email or password")
    if not UserManager.verify_user_password(user.user_id, password):
        Logger.warn(f"Login failed for email (password): {email}")
        return HTTPResponse.error(response, "Invalid email or password")
    
    tkn = UserManager.get_user_token(user.user_id)
    if tkn is None:
        Logger.error(f"Failed to generate token for user_id: {user.user_id}")
        return HTTPResponse.error(response, "Failed to generate session token")
    return HTTPResponse.ok(response, "Login successful", {"token": tkn, "user": {"id": user.user_id, "fullname": user.full_name, "email": user.email}})

@app.post("/users/login_user_token")
def login_user_token(
        request: Request,
        response: Response,
        token: str = Body(..., embed=True) 
    ):
    # if token is None:
    #     Logger.warn("Login failed: No session token provided")
    #     return HTTPResponse.error(response, "No session token provided")
    
    user_info = decode_user_token(token)
    if user_info is None:
        Logger.warn(f"Login failed for token: {token}")
        return HTTPResponse.token_error(response)
    user = UserManager.get_user_by_id(user_info.user_id)
    if user is None or user.user_id is None:
        return HTTPResponse.error(response, "User not found")
    tkn = UserManager.get_user_token(user.user_id)
    if tkn is None:
        Logger.error(f"Failed to generate token for user_id: {user.user_id}")
        return HTTPResponse.error(response, "Failed to generate session token")
    return HTTPResponse.ok(response, "Login successful", {"token": tkn, "user": {"id": user.user_id, "fullname": user.full_name, "email": user.email}})

@app.post("/overview")
def overview(
    response: Response,
    token: str = Body(..., embed=True) 
):
    if not verify_token_validity(token)[0]:
        Logger.warn(f"Overview access with invalid/expired token: {token}")
        return HTTPResponse.token_error(response)
    data = {
        "registered_devices": 0,
        "alerts_24h": 0,
        "critical_campaigns": 0,
        "baseline_deviations": 0,
        "rule_violations_ph": 0, # per hour
        "active_campaigns": [],
        "alerts": [],
        "event_stats": {
            "top_noisy_devices": [],
            "10_min_interval_counts": []
        },
        "recently_changed_rules": [],
        "system_health": {
            "spearhead_status": "OK",
            "wrappers_connected_precentage": -1,
            "last_heartbeat_age": -1
        }
    }
    
    user_info = decode_user_token(token)
    if user_info is None:
        Logger.warn(f"Overview access failed for token: {token}")
        return HTTPResponse.error(response, "Invalid token")
    devices_under_user = list(DeviceManager.get_devices_by_handler(user_info.user_id))

    data["registered_devices"] = len(devices_under_user)
    data["alerts_24h"] = len(list(NotificationManager.get_notifications_for_user_dated(
        user_info.user_id,
        datetime.now(timezone.utc) - timedelta(hours=24),
        datetime.now(timezone.utc)
    )))

    campaigns = CampaignManager.get_all_campaigns_for_user(user_info.user_id)
    data["critical_campaigns"] = len([c for c in campaigns if c.severity == campaign.CampaignSeverity.HIGH])
    data["active_campaigns"] = [c.to_json() for c in campaigns if c.status == campaign.CampaignStatus.ONGOING]
    # TODO: Baselines
    data["alerts"] = [n.to_json() for n in NotificationManager.get_unread_notifications_for_user(user_info.user_id)]
    # top 5
    device_event_counts: Dict[tuple[int, str], int] = {}
    for device in devices_under_user:
        if device.device_id is None: continue
        for _ in EventManager.get_events_by_device_id(device.device_id):
            device_event_counts[(device.device_id, device.device_name)] = device_event_counts.get((device.device_id, device.device_name), 0) + 1
    top_noisy_devices = sorted(device_event_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    data["event_stats"]["top_noisy_devices"] = [{"device_id": device_id, "device_name": device_name, "event_count": count} for (device_id, device_name), count in top_noisy_devices] # type: ignore
    data["event_stats"]["10_min_interval_counts"] = EventManager.get_event_counts_in_intervals(datetime.now(timezone.utc) - timedelta(days=1), datetime.now(timezone.utc), 10) # type: ignore
    
    with SessionMaker() as session:
        recent_rules = session.execute(
            text("SELECT rule_id, rule_name, last_updated FROM rules WHERE last_updated >= :time"),
            {"time": datetime.now(timezone.utc) - timedelta(hours=48)}
        ).fetchall()
        data["recently_changed_rules"] = [{"rule_id": r[0], "name": r[1], "last_updated": r[2].isoformat()} for r in recent_rules] # type: ignore
    
    last_hb_time = HeartbeatManager.get_last_heartbeat_time()
    if last_hb_time is not None and last_hb_time.tzinfo is None:
        last_hb_time = last_hb_time.replace(tzinfo=timezone.utc)
    data["system_health"]["last_heartbeat_age"] = int((datetime.now(timezone.utc) - last_hb_time).total_seconds()) if last_hb_time else -1 # type: ignore
    total_device_count = DeviceManager.get_device_count()
    data["system_health"]["wrappers_connected_precentage"] = PUBLIC_SPEAR_HEAD_DATA.wrappers_connected / total_device_count * 100 if total_device_count > 0 else 0 # type: ignore
    return HTTPResponse.ok(response, "Overview data retrieved successfully", data)


@app.get("/ping")
def ping():
    return HTTPResponse.ok(Response(), "pong")

def run():
    def _run():
        cert_file, key_file = ensure_self_signed_cert()
        uvicorn.run(
            "models.connection.spear_head_http:app",
            host="0.0.0.0",
            port=SPEAR_HEAD_API_PORT, # type: ignore
            ssl_certfile=cert_file,
            ssl_keyfile=key_file,
        )
    threading.Thread(target=_run, daemon=True).start()

if __name__ == "__main__":
    run()

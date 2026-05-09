# main.py
from datetime import datetime, timezone, timedelta
import threading
from typing import Any, Dict
from fastapi import Body, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy import text
from models.events.types.event import EventKind
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
from models.managers.group_manager import GroupManager
from models.users.permission import get_description_permissions
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
    if (res := check_user_permission(token, UserAction.CONTROL_USERS, ActionTarget.none())) != UserPermissionResponse.ALLOWED:
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
    return HTTPResponse.ok(response, "Login successful", {"token": tkn, "user": {"id": user.user_id, "fullname": user.full_name, "email": user.email, "permissions": [perm.to_json() for perm in user.permissions]}})

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
    return HTTPResponse.ok(response, "Login successful", {"token": tkn, "user": {"id": user.user_id, "fullname": user.full_name, "email": user.email, "permissions": [perm.to_json() for perm in user.permissions]}})

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
    data["critical_campaigns"] = 0
    data["active_campaigns"] = []
    for c in campaigns:
        if c.status == campaign.CampaignStatus.ONGOING:
            data["active_campaigns"].append(c.to_json())
            if c.severity == campaign.CampaignSeverity.HIGH:
                data["critical_campaigns"] += 1

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
        data["system_health"]["last_heartbeat_age"] = last_hb_time.timestamp() * 1000 if last_hb_time else -1 # type: ignore
    total_device_count = DeviceManager.get_device_count()
    data["system_health"]["wrappers_connected_precentage"] = PUBLIC_SPEAR_HEAD_DATA.wrappers_connected / total_device_count * 100 if total_device_count > 0 else 0 # type: ignore

    data["rule_violations_ph"] = len(list(EventManager.get_events_date_range(datetime.now(timezone.utc) - timedelta(hours=1), datetime.now(timezone.utc)))) # type: ignore

    return HTTPResponse.ok(response, "Overview data retrieved successfully", data)

@app.post("/users/metadata")
def get_user_metadata(
        response: Response,
        token: str = Body(..., embed=True) 
    ):
    usr, succ = verify_token_validity(token)
    if not succ or usr is None:
        Logger.warn(f"User metadata access with invalid/expired token: {token}")
        return HTTPResponse.token_error(response)
    
    res = {
        "permission_types": get_description_permissions(),
        "group_ids": {g.group_id: g.group_name for g in GroupManager.get_groups_handled_by_user(usr.user_id)}, # type: ignore
        "device_ids": {d.device_id: d.device_name for d in DeviceManager.get_devices_by_handler(usr.user_id)} # type: ignore
    }
    return HTTPResponse.ok(response, "User metadata retrieved successfully", res)

@app.post("/users/list")
def list_users(
        response: Response,
        token: str = Body(..., embed=True) 
    ):
    if (res := check_user_permission(token, UserAction.CONTROL_USERS, ActionTarget.none())) != UserPermissionResponse.ALLOWED:
        return permission_error_to_http_response(res, response)

    users = []
    for user in UserManager.get_all_users():
        users.append({
            "id": user.user_id,
            "fullname": user.full_name,
            "email": user.email,
            "permissions": [perm.to_json() for perm in user.permissions]
        })
    return HTTPResponse.ok(response, "Users listed successfully", {"users": users})

@app.post("/users/set_password")
def set_user_password(
        response: Response,
        token: str = Body(..., embed=True) ,
        user_id: int = Body(...),
        new_password: str = Body(...)
    ):
    if (res := check_user_permission(token, UserAction.CONTROL_USERS, ActionTarget.none())) != UserPermissionResponse.ALLOWED:
        return permission_error_to_http_response(res, response)

    if not UserManager.set_user_password(user_id, new_password):
        return HTTPResponse.error(response, "Failed to set user password")
    return HTTPResponse.ok(response, "User password updated successfully")

@app.post("/users/update_permissions")
def update_user_permissions(
        response: Response,
        token: str = Body(..., embed=True) ,
        user_id: int = Body(...),
        permissions: list[Any] = Body(...)
    ):
    if (res := check_user_permission(token, UserAction.CONTROL_USERS, ActionTarget.none())) != UserPermissionResponse.ALLOWED:
        return permission_error_to_http_response(res, response)

    # disallow removing own CONTROL_USERS, ROOT permissions
    # only allow adding permissions to other users when the current user has them / is root
    usr, _ = verify_token_validity(token)
    if usr is None:
        return HTTPResponse.error(response, "Invalid session token")
    
    other_usr = UserManager.get_user_by_id(user_id)
    if other_usr is None:
        return HTTPResponse.error(response, "User not found")
    
    parsed_perms = from_json_permissions(permissions)
    if usr.user_id == user_id:
        for perm in parsed_perms:
            print(perm.type_)
        has_control_users = any(perm.type_ == UserAction.CONTROL_USERS for perm in parsed_perms)
        has_root = any(perm.type_ == UserAction.ROOT for perm in parsed_perms)
        if not has_control_users or not has_root:
            return HTTPResponse.error(response, "Cannot remove own CONTROL_USERS or ROOT permissions")

    assigning_usr_perms = set(perm.type_ for perm in usr.permissions)
    if UserAction.ROOT not in assigning_usr_perms:
        for perm in parsed_perms:
            if perm.type_ not in assigning_usr_perms:
                return HTTPResponse.error(response, f"Cannot assign permission {perm.type_.name} that the current user does not have")

    if not UserManager.set_user_permissions(user_id, permissions):
        return HTTPResponse.error(response, "Failed to update user permissions")
    return HTTPResponse.ok(response, "User permissions updated successfully")

@app.post("/users/create")
def create_user(
        response: Response,
        email: str = Body(...),
        temporary_password: str = Body(...),
        permissions: list[Any] = Body(...),
        token: str = Body(...)
    ):
    if (res := check_user_permission(token, UserAction.CONTROL_USERS, ActionTarget.none())) != UserPermissionResponse.ALLOWED:
        return permission_error_to_http_response(res, response)

    res = UserManager.create_user(email, email, temporary_password, from_json_permissions(permissions))
    if res is None:
        return HTTPResponse.error(response, "Failed to create user")
    
    return HTTPResponse.ok(response, "User created successfully", {"session": res.token})

@app.post("/users/delete")
def delete_user(
        response: Response,
        token: str = Body(..., embed=True),
        user_id: int = Body(...)
    ):
    if (res := check_user_permission(token, UserAction.CONTROL_USERS, ActionTarget.none())) != UserPermissionResponse.ALLOWED:
        return permission_error_to_http_response(res, response)

    data = decode_user_token(token)
    if not data or user_id == data.user_id:
        return HTTPResponse.error(response, "Cannot delete own user account")

    if not UserManager.delete_user_by_id(user_id):
        return HTTPResponse.error(response, "Failed to delete user")
    return HTTPResponse.ok(response, "User deleted successfully")

@app.post("/devices/list")
def list_devices(
        response: Response,
        token: str = Body(..., embed=True) 
    ):
    usr, succ = verify_token_validity(token)
    if not succ or usr is None or usr.user_id is None:
        Logger.warn(f"Device list access with invalid/expired token: {token}")
        return HTTPResponse.token_error(response)

    devices = []
    for device in DeviceManager.get_devices_by_handler(usr.user_id):
        devices.append(device.to_json())
    return HTTPResponse.ok(response, "Devices listed successfully", {"devices": devices})

@app.post("/devices/details")
def device_details(
        response: Response,
        token: str = Body(..., embed=True) ,
        device_id: int = Body(...)
    ):
    usr, succ = verify_token_validity(token)
    if not succ or usr is None or usr.user_id is None:
        Logger.warn(f"Device details access with invalid/expired token: {token}")
        return HTTPResponse.token_error(response)

    device = DeviceManager.get_device_by_id(device_id)
    managed_devices = set(d.device_id for d in DeviceManager.get_devices_by_handler(usr.user_id) if d.device_id is not None) # type: ignore
    if device is None or device.device_id not in managed_devices:
        Logger.warn(f"Device details access denied for device_id: {device_id} with token: {token}")
        return HTTPResponse.permission_denied(response)
    
    # TODO: REMOVE FILTER
    print([e.to_json() for e in EventManager.get_events_by_device_id(device_id)]) # type: ignore
    events = list(filter(lambda e: e.event_type == EventKind.PACKET, EventManager.get_events_by_device_id(device_id))) # type: ignore
    data = {
        "device": device.to_json(),
        "events": [e.to_json() for e in events],
        "campaigns": [c.to_json() for c in CampaignManager.get_campaigns_by_device_id(device_id)],
    }
    
    return HTTPResponse.ok(response, "Device details retrieved successfully", data)

@app.post("/devices/update")
def update_device(
        response: Response,
        token: str = Body(..., embed=True) ,
        device_id: int = Body(...),
        device_name: str = Body(...),
        groups: list[int] = Body(...),
        handlers: list[int] = Body(...)
    ):
    if (res := check_user_permission(token, UserAction.CONTROL_DEVICES, ActionTarget.device(device_id))) != UserPermissionResponse.ALLOWED:
        return permission_error_to_http_response(res, response)
    
    device = DeviceManager.get_device_by_id(device_id)
    if device is None:
        return HTTPResponse.error(response, "Device not found")
    if not DeviceManager.update_device(device_id, device_name, groups, handlers):
        return HTTPResponse.error(response, "Failed to update device")
    return HTTPResponse.ok(response, "Device updated successfully")

@app.post("/devices/communication_map")
def device_communication_map(
        response: Response,
        token: str = Body(..., embed=True)
        ):
    usr, succ = verify_token_validity(token)
    if not succ or usr is None or usr.user_id is None:
        Logger.warn(f"Communication map access with invalid/expired token: {token}")
        return HTTPResponse.token_error(response)

    devices_under_user = list(DeviceManager.get_devices_by_handler(usr.user_id))
    device_ids_under_user = set(d.device_id for d in devices_under_user if d.device_id is not None) # type: ignore
    tmp_communication_map: dict[int, tuple[int, int]] = {} # src -> (dst, count)
    for device in devices_under_user:
        if device.device_id is None: continue
        heartbeats = HeartbeatManager.get_heartbeats_for_device(device.device_id)
        for hb in heartbeats:
            contacted_devices = hb.network_details.get_contacted_devices()
            for contacted_device_id, count in contacted_devices.items():
                if contacted_device_id in device_ids_under_user:
                    key = (device.device_id, contacted_device_id) # type: ignore
                    if key not in tmp_communication_map:
                        tmp_communication_map[key] = (device.device_id, contacted_device_id, count) # type: ignore
                    else:
                        existing = tmp_communication_map[key]
                        tmp_communication_map[key] = (existing[0], existing[1], existing[2] + count) # type: ignore
    communication_map = [{"from_device_id": v[0], "to_device_id": v[1], "count": v[2]} for v in tmp_communication_map.values()] # type: ignore

    return HTTPResponse.ok(response, "Device communication map retrieved successfully", {"connections": communication_map})

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

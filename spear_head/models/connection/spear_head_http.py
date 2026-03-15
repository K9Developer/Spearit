# main.py
import threading
from typing import Any, Dict
from fastapi import Body, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from constants.constants import TOKEN_VALIDITY_DURATION_HOURS, SPEAR_HEAD_API_PORT
from models.logger import Logger
from models.managers.user_manager import UserManager
from utils.https_utils import ensure_self_signed_cert
from utils.jwt_utils import decode_user_token, make_user_token
from utils.permission_utils import ActionTarget, UserAction, UserPermissionResponse, check_user_permission, from_json_permissions
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
        response.status_code = 400
        return {"status": "error", "message": message}

    @staticmethod
    def permission_denied(response: Response) -> Dict[str, Any]:
        response.status_code = 403
        return {"status": "error", "message": "Permission denied"}    


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
        return HTTPResponse.error(response, "Invalid token")
    user = UserManager.get_user_by_id(user_info.user_id)
    if user is None or user.user_id is None:
        return HTTPResponse.error(response, "User not found")
    tkn = UserManager.get_user_token(user.user_id)
    if tkn is None:
        Logger.error(f"Failed to generate token for user_id: {user.user_id}")
        return HTTPResponse.error(response, "Failed to generate session token")
    return HTTPResponse.ok(response, "Login successful", {"token": tkn, "user": {"id": user.user_id, "fullname": user.full_name, "email": user.email}})

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

# main.py
import threading
from typing import Any, Dict
from fastapi import Body, FastAPI, Request, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from constants.constants import TOKEN_VALIDITY_DURATION_HOURS, SPEAR_HEAD_API_PORT
from models.logger import Logger
from models.managers.user_manager import UserManager
from utils.jwt_utils import make_user_token
from utils.permission_utils import ActionTarget, UserAction, check_user_permission, from_json_permissions

class HTTPResponse():

    @staticmethod
    def ok(response: Response, message: str, data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        response.status_code = 200
        res = {"status": "ok", "message": message}
        if data is not None:
            res.update(data)
        return res
    
    @staticmethod
    def error(response: Response, message: str) -> Dict[str, Any]:
        response.status_code = 400
        return {"status": "error", "message": message}

    @staticmethod
    def permission_denied(response: Response, ) -> Dict[str, Any]:
        response.status_code = 403
        return {"status": "error", "message": "Permission denied"}    
    
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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
    ):
    session_token = request.cookies.get("session")
    if session_token is None: return HTTPResponse.error(response, "No session token provided")
    if not check_user_permission(session_token, UserAction.CREATE_USER, ActionTarget.none()):
        return HTTPResponse.permission_denied(response)

    res = UserManager.create_user(name, email, password, from_json_permissions(permissions))
    if res is None:
        return HTTPResponse.error(response, "Failed to create user")
    
    return HTTPResponse.ok(response, "User created successfully", {"session": res.token})

@app.post("/users/login")
def login_user(
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
    
    user.token = make_user_token(user.user_id)
    user.update_db()
    response.set_cookie(key="session", value=user.token, httponly=True, samesite="lax", max_age=60*60*TOKEN_VALIDITY_DURATION_HOURS)
    return HTTPResponse.ok(response, "Login successful", {"session": user.token})
    
def run():
    def _run():
        uvicorn.run("models.connection.spear_head_http:app", host="0.0.0.0", port=SPEAR_HEAD_API_PORT) # type: ignore
    threading.Thread(target=_run, daemon=True).start()

if __name__ == "__main__":
    run()

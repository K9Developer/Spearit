# main.py
from typing import Any, Dict
from fastapi import Body, FastAPI, Request, Request, Response
import uvicorn

from constants.constants import TOKEN_VALIDITY_DURATION_HOURS
from models.managers.user_manager import UserManager
from utils.jwt_utils import make_user_token
from utils.permission_utils import ActionTarget, UserAction, check_user_permission, from_json_permissions

class HTTPResponse():

    @staticmethod
    def ok(message: str, data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        res = {"status": "ok", "message": message}
        if data is not None:
            res.update(data)
        return res
    
    @staticmethod
    def error(message: str) -> Dict[str, Any]:
        return {"status": "error", "message": message}

    @staticmethod
    def permission_denied() -> Dict[str, Any]:
        return {"status": "error", "message": "Permission denied"}    
    
app = FastAPI()

@app.get("/")
def root():
    return {"ok": True, "message": "hello"}

@app.post("/users")
def create_new_user(
        request: Request,
        name: str = Body(...),
        email: str = Body(...),
        password: str = Body(...),
        permissions: list[Any] = Body(...),
    ):
    session_token = request.cookies.get("session")
    if session_token is None: return HTTPResponse.error("No session token provided")
    if not check_user_permission(session_token, UserAction.CREATE_USER, ActionTarget.none()):
        return HTTPResponse.permission_denied()

    res = UserManager.create_user(name, email, password, from_json_permissions(permissions))
    if res is None:
        return HTTPResponse.error("Failed to create user")
    
    return HTTPResponse.ok("User created successfully", {"session": res.token})

@app.post("/users/login")
def login_user(
        response: Response,
        email: str = Body(...),
        password: str = Body(...),
    ):
    user = UserManager.get_user_by_email(email)
    if user is None or user.user_id is None:
        print(f"Login failed for email: {email}")
        return HTTPResponse.error("Invalid email or password")
    if not UserManager.verify_user_password(user.user_id, password):
        print(f"Login failed for email (password): {email}")
        return HTTPResponse.error("Invalid email or password")
    
    user.token = make_user_token(user.user_id)
    user.update_db()
    response.set_cookie(key="session", value=user.token, httponly=True, samesite="lax", max_age=60*60*TOKEN_VALIDITY_DURATION_HOURS)
    return HTTPResponse.ok("Login successful", {"session": user.token})
    
def run():
    uvicorn.run("models.connection.spear_head_http:app", host="0.0.0.0", port=80, reload=True) # type: ignore

if __name__ == "__main__":
    run()

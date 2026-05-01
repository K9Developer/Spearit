from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from models.users.user import User

from datetime import datetime, timezone
from enum import Enum

from typing import Any

from models.users.permission import ActionTarget, ActionTargetType, Permission, UserAction

from utils.jwt_utils import decode_user_token

def from_json_permissions(json_perms: list[Any]) -> list[Permission]:
    permissions: list[Permission] = []
    for perm in json_perms:
        permission = Permission(
            type_=UserAction(perm.get("type", perm.get("type_"))), # type: ignore
            affected_groups=perm.get("affected_groups", []),
            affected_devices=perm.get("affected_devices", []),
        )
        if len(permission.affected_groups) == 0 and len(permission.affected_devices) == 0 and permission.type_ != UserAction.ROOT and permission.type_ != UserAction.CONTROL_USERS and permission.type_ != UserAction.CONTROL_GROUPS:
            continue
        permissions.append(permission)
    return permissions

class UserPermissionResponse(Enum):
    ALLOWED = 0
    DENIED = 1
    INVALID_SESSION = 2


def verify_token_validity(token: str) -> tuple["User | None", bool]:
    from models.managers.user_manager import UserManager
    user_info = decode_user_token(token)
    if user_info is None: return None, False
    if user_info.expiry < datetime.now(timezone.utc): return None, False
    user = UserManager.get_user_by_id(user_info.user_id)
    if user is None: return None, False
    if user.token != token: return None, False
    return user, True

def check_user_permission(session_token: str, action: UserAction, target: ActionTarget) -> UserPermissionResponse:
    user, valid = verify_token_validity(session_token)
    if not valid or user is None:
        return UserPermissionResponse.INVALID_SESSION

    for perm in user.permissions:
        if perm.type_ == UserAction.ROOT: return UserPermissionResponse.ALLOWED
        if perm.type_ != action: continue
        if target.target_type == ActionTargetType.NONE: return UserPermissionResponse.ALLOWED
        if target.target_type == ActionTargetType.DEVICE and (target.target_id in perm.affected_devices):
            return UserPermissionResponse.ALLOWED
        if target.target_type == ActionTargetType.GROUP and (target.target_id in perm.affected_groups):
            return UserPermissionResponse.ALLOWED
        
    return UserPermissionResponse.DENIED
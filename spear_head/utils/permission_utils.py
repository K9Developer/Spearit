from datetime import datetime, timezone
from enum import Enum

from typing import Any

from models.users.permission import ActionTarget, ActionTargetType, Permission, UserAction
from utils.jwt_utils import decode_user_token

def from_json_permissions(json_perms: list[Any]) -> list[Permission]:
    permissions: list[Permission] = []
    for perm in json_perms:
        permission = Permission(
            type_=UserAction(perm["type_"]),
            affected_groups=perm.get("affected_groups", []),
            affected_devices=perm.get("affected_devices", []),
        )
        if len(permission.affected_groups) == 0 and len(permission.affected_devices) == 0:
            continue
        permissions.append(permission)
    return permissions

class UserPermissionResponse(Enum):
    ALLOWED = 0
    DENIED = 1
    INVALID_SESSION = 2

def check_user_permission(session_token: str, action: UserAction, target: ActionTarget) -> UserPermissionResponse:
    from models.managers.user_manager import UserManager
    user_tok_data = decode_user_token(session_token)
    if user_tok_data is None: return UserPermissionResponse.INVALID_SESSION
    if user_tok_data.expiry < datetime.now(timezone.utc): return UserPermissionResponse.INVALID_SESSION
    user_id = user_tok_data.user_id
    user = UserManager.get_user_by_id(user_id)
    if user is None: return UserPermissionResponse.INVALID_SESSION
    if user.token != session_token: return UserPermissionResponse.INVALID_SESSION


    for perm in user.permissions:
        if perm.type_ == UserAction.ROOT: return UserPermissionResponse.ALLOWED
        if perm.type_ != action: continue
        if target.target_type == ActionTargetType.NONE: return UserPermissionResponse.ALLOWED
        if target.target_type == ActionTargetType.DEVICE and (target.target_id in perm.affected_devices):
            return UserPermissionResponse.ALLOWED
        if target.target_type == ActionTargetType.GROUP and (target.target_id in perm.affected_groups):
            return UserPermissionResponse.ALLOWED
        
    return UserPermissionResponse.DENIED
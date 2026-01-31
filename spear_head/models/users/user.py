
from typing import Any
from databases.db_types.users.user_db import UserDB
from databases.engine import SessionMaker
from utils.permission_utils import Permission, from_json_permissions


class User:

    def __init__(self, username: str, email: str, password_hash: str, permissions: list[Permission]) -> None:
        self.full_name: str = username
        self.email: str = email
        self.password_hash: str = password_hash
        self.salt: str = ""
        self.permissions: list[Permission] = permissions

        self.token: str | None = None

        self.user_id: int | None = None

    @staticmethod
    def from_db(user_db: UserDB) -> "User":
        user = User(
            username=user_db.full_name,  # type: ignore
            email=user_db.email,  # type: ignore
            password_hash=user_db.password_hash,  # type: ignore
            permissions=from_json_permissions(user_db.permissions),  # type: ignore
        )
        user.permissions = from_json_permissions(user_db.permissions)  # type: ignore
        user.user_id = user_db.user_id  # type: ignore
        user.token = user_db.token  # type: ignore
        user.salt = user_db.salt  # type: ignore
        return user
    
    def _permissions_to_db(self) -> list[dict[Any, Any]]:
        perms: list[Any] = []
        for perm in self.permissions:
            perms.append({
                "type_": perm.type_.value,
                "affected_groups": perm.affected_groups,
                "affected_devices": perm.affected_devices,
            })
        return perms
    
    def to_db(self) -> UserDB:
        return UserDB(
            full_name=self.full_name,
            email=self.email,
            password_hash=self.password_hash,
            salt=self.salt,
            permissions=self._permissions_to_db(),
            token=self.token,
        )
    
    def update_db(self):
        user_id = self.user_id
        user_db = self.to_db()
        with SessionMaker() as session:
            if user_id is None:
                session.add(user_db)
                session.commit()
                session.refresh(user_db)
                user_id = user_db.user_id
            else:
                user_db.user_id = user_id  # type: ignore
                session.merge(user_db)
                session.commit()

        self.user_id = user_id  # type: ignore
    
    

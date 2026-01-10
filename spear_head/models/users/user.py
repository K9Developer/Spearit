
from databases.db_types.users.user_db import UserDB
from databases.engine import SessionMaker
from models.users.permission import Permission


class User:

    def __init__(self, username: str, email: str, password_hash: str) -> None:
        self.full_name: str = username
        self.email: str = email
        self.password_hash: str = password_hash
        self.permissions: list[Permission] = []

        self.user_id: int | None = None

    @staticmethod
    def from_db(user_db: UserDB) -> "User":
        user = User(
            username=user_db.full_name,  # type: ignore
            email=user_db.email,  # type: ignore
            password_hash=user_db.password_hash,  # type: ignore
        )
        user.permissions = user_db.permissions  # type: ignore
        user.user_id = user_db.user_id  # type: ignore
        return user
    
    def _permissions_to_db(self) -> dict[str, dict[str, list[int]]]:
        perms_dict = {}
        for perm in self.permissions:
            perms_dict[perm.type_] = {
                "groups": perm.affected_groups,
                "devices": perm.affected_devices,
            }
        return perms_dict
    
    def to_db(self) -> UserDB:
        return UserDB(
            full_name=self.full_name,
            email=self.email,
            password_hash=self.password_hash,
            permissions=self._permissions_to_db(),
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
    
    

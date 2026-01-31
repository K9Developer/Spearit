from typing import Generator, TYPE_CHECKING

from utils.user_utils import validate_password, validate_username, validate_email
if TYPE_CHECKING:
    from utils.permission_utils import Permission
from databases.db_types.users.user_db import UserDB
from databases.engine import SessionMaker
from models.users.user import User
from utils.jwt_utils import make_user_token
from utils.password_utils import hash_raw_password


class UserManager:
    
    # ------------------ Public Methods ------------------

    @staticmethod
    def get_all_users() -> Generator[User, None, None]:
        with SessionMaker() as session:
            user_dbs = session.query(UserDB).all()
            for user_db in user_dbs:
                user = User.from_db(user_db)
                yield user

    @staticmethod
    def get_user_by_id(user_id: int) -> User | None:
        with SessionMaker() as session:
            user_db = session.get(UserDB, user_id)
            if user_db is None:
                return None
            return User.from_db(user_db)
        
    @staticmethod
    def get_users_by_substring(substring: str) -> Generator[User, None, None]:
        with SessionMaker() as session:
            user_dbs = session.query(UserDB).filter(
                (UserDB.full_name.contains(substring)) | 
                (UserDB.email.contains(substring))
            ).all()
            for user_db in user_dbs:
                user = User.from_db(user_db)
                yield user

    @staticmethod
    def delete_user_by_id(user_id: int) -> bool:
        with SessionMaker() as session:
            user_db = session.get(UserDB, user_id)
            if user_db is None:
                return False
            session.delete(user_db)
            session.commit()
            return True
        
    @staticmethod
    def get_user_by_email(email: str) -> User | None:
        with SessionMaker() as session:
            user_db = session.query(UserDB).filter_by(email=email).first()
            if user_db is None:
                return None
            return User.from_db(user_db)
        
    @staticmethod
    def get_user_by_fullname(fullname: str) -> User | None:
        with SessionMaker() as session:
            user_db = session.query(UserDB).filter_by(full_name=fullname).first()
            if user_db is None:
                return None
            return User.from_db(user_db)
        
    @staticmethod
    def set_user_permissions(user_id: int, permissions: dict[str, dict[str, list[int]]]) -> bool:
        with SessionMaker() as session:
            user_db = session.get(UserDB, user_id)
            if user_db is None:
                return False
            user_db.permissions = permissions  # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def create_user(username: str, email: str, raw_password: str, permissions: list['Permission']) -> User | None:
        if UserManager.get_user_by_email(email) is not None:
            return None
        
        #TODO: return specific error messages
        if not validate_email(email): return None
        if not validate_username(username): return None
        if not validate_password(raw_password): return None

        hashed, salt = hash_raw_password(raw_password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed,
            permissions=permissions,
        )
        user.salt = salt

        with SessionMaker() as session:
            user_db = user.to_db()
            session.add(user_db)
            session.commit()
            user.user_id = user_db.user_id  # type: ignore

        if user.user_id:
            user.token = make_user_token(user.user_id)
            user.update_db()
        else:
            return None

        return user
    
    @staticmethod
    def verify_user_password(user_id: int, raw_password: str) -> bool:
        user = UserManager.get_user_by_id(user_id)
        if user is None:
            return False
        return hash_raw_password(raw_password, user.salt)[0] == user.password_hash
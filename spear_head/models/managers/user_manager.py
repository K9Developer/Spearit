from typing import Generator
from databases.db_types.users.user_db import UserDB
from databases.engine import SessionMaker
from models.users.user import User
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
    def create_user(username: str, email: str, raw_password: str) -> User | None:
        if UserManager.get_user_by_email(email) is not None:
            return None
        
        user = User(
            username=username,
            email=email,
            password_hash=hash_raw_password(raw_password),
        )
        
        with SessionMaker() as session:
            user_db = user.to_db()
            session.add(user_db)
            session.commit()
            user.user_id = user_db.user_id  # type: ignore

        return user
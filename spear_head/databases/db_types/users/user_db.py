from sqlalchemy import Column, Integer, String, JSON
from databases.base import Base

class UserDB(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    full_name = Column(String(128), nullable=False)
    email = Column(String(256), nullable=False, unique=True, index=True)
    password_hash = Column(String(256), nullable=False)
    salt = Column(String(64), nullable=False)

    token = Column(String(512), nullable=True)

    """
    like so:
    [
        {
            "type_": "CREATE_USERS",
            "affected_groups": [1, 2, 3],
            "affected_devices": [4, 5, 6],
        },
    ]
    """
    permissions = Column(JSON, nullable=False, default={})

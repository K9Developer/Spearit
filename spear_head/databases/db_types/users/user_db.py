from sqlalchemy import Column, Integer, String, JSON
from databases.base import Base

class UserDB(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    full_name = Column(String(128), nullable=False)
    # Explicit index for efficient lookups in get_user_by_email
    email = Column(String(256), nullable=False, unique=True, index=True)
    password_hash = Column(String(256), nullable=False)

    """
    like so:
    {
        "permission_name": {
            "groups": [list of group ids],
            "devices": [list of device ids]
        },
    }
    """
    permissions = Column(JSON, nullable=False, default={})

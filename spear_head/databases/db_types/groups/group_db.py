
from sqlalchemy import JSON, Column, DateTime, Integer, String, func
from databases.base import Base

class GroupDB(Base):
    __tablename__ = "device_groups"

    group_id = Column(Integer, primary_key=True)
    group_name = Column(String(32), nullable=False, unique=True)
    description = Column(String(250), nullable=True)
    handlers = Column(JSON, nullable=True)  # list of user ids
    device_ids = Column(JSON, nullable=True)  # list of device ids
    created_at = Column(DateTime(timezone=True), server_default=func.now())
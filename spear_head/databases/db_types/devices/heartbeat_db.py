from sqlalchemy import Column, Integer, ForeignKey, DateTime, JSON, func
from databases.base import Base

class HeartbeatDB(Base):
    __tablename__ = "heartbeats"

    heartbeat_id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.device_id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    contacted_devices = Column(JSON, nullable=True)
    system_metrics = Column(JSON, nullable=True)
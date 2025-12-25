"""

class EventDB(Base):
    __tablename__ = "events"

    event_id = Column(BigInteger, primary_key=True)
    
    device_id = Column(BigInteger, ForeignKey("devices.device_id"), nullable=False)
    rule_id = Column(BigInteger, ForeignKey("rules.rule_id"), nullable=False)
    campaign_id = Column(BigInteger, ForeignKey("campaigns.campaign_id"), nullable=True)
    
    event_type = Column(String(32), nullable=False)
    event_data = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    responses_taken = Column(JSON, nullable=True)
"""

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, JSON, func
from databases.base import Base

class DeviceDB(Base):
    __tablename__ = "devices"

    device_id = Column(Integer, primary_key=True)

    device_name = Column(String(32), nullable=True)
    operating_system_details = Column(String(32), nullable=True)
    last_known_ip_address = Column(String(38), nullable=True) # support ipv6 length (38)
    mac_address = Column(String(17), nullable=False, unique=True)

    # TODO: Group, heartbeat

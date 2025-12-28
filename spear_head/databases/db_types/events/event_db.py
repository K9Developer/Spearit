from sqlalchemy import Column, BigInteger, Integer, ForeignKey, String, DateTime, JSON, func
from databases.base import Base


class EventDB(Base):
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True)
    
    device_id = Column(BigInteger, ForeignKey("devices.device_id"), nullable=False)
    rule_id = Column(BigInteger, ForeignKey("rules.rule_id"), nullable=False)
    campaign_id = Column(BigInteger, ForeignKey("campaigns.campaign_id"), nullable=True)
    
    event_type = Column(String(32), nullable=False)
    event_data = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    response_taken = Column(String, nullable=True)
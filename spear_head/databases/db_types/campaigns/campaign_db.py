from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, JSON, func
from databases.base import Base

class CampaignDB(Base):
    __tablename__ = "campaigns"

    campaign_id = Column(Integer, primary_key=True)
    parent_campaign_id = Column(Integer, ForeignKey("campaigns.campaign_id"), nullable=True)

    name = Column(String(32), nullable=True)
    description = Column(String(512), nullable=True)
    detailed_description = Column(String(512), nullable=True)
    start = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(16), nullable=False) # ONGOING, COMPLETED, ABORTED
    severity = Column(String(16), nullable=False) # LOW, MEDIUM, HIGH
    involved_devices = Column(JSON, nullable=True)  # list of device IDs


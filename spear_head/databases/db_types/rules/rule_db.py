from sqlalchemy import Boolean, Column, Integer, String, DateTime, JSON, func
from databases.base import Base

class RuleDB(Base):
    __tablename__ = "rules"

    rule_id = Column(Integer, primary_key=True)
    rule_order = Column(Integer, nullable=False)
    rule_type = Column(String(32), nullable=False)
    event_types = Column(JSON, nullable=False)
    conditions = Column(JSON, nullable=False)
    responses = Column(JSON, nullable=False)
    disabled_for_groups = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=1)
    # author = Column(ForeignKey("users.user_id"), nullable=False) # TODO
    rule_name = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    priority = Column(Integer, nullable=False, default=0)

from sqlalchemy import JSON, Column, DateTime, Integer, String, func
from databases.base import Base

class NotificationDB(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True)
    for_users = Column(JSON, nullable=False)  # list of user ids
    message = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False)  # "info", "warning", "danger"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_by = Column(JSON, nullable=False)  # list of user ids who have read the notification
    # TODO: relative link when clicking on notification
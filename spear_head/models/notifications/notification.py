
from enum import Enum
from datetime import datetime
from databases.db_types.notifications.notification_db import NotificationDB
from databases.engine import SessionMaker

class NotificationType(Enum):
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"

class Notification:
    
    def __init__(self, for_users: list[int], message: str, created_at: datetime, type: NotificationType = NotificationType.INFO) -> None:
        self.for_users: list[int] = for_users
        self.message: str = message
        self.type: NotificationType = type
        self.created_at: datetime = created_at
        self.read_by: list[int] = []

        self.notification_id: int | None = None

    @staticmethod
    def from_db(notification_db: "NotificationDB") -> "Notification":
        notification = Notification(
            for_users=notification_db.for_users,  # type: ignore
            message=notification_db.message,  # type: ignore
            type=NotificationType(notification_db.type),  # type: ignore
            created_at=notification_db.created_at,  # type: ignore
        )
        notification.read_by = notification_db.read_by or []  # type: ignore
        notification.notification_id = notification_db.notification_id  # type: ignore
        return notification
    
    def to_db(self) -> "NotificationDB":
        return NotificationDB(
            for_users=self.for_users,
            message=self.message,
            type=self.type.value,
            created_at=self.created_at,
            read_by=self.read_by,
        )
    
    def update_db(self):
        notification_id = self.notification_id
        notification_db = self.to_db()
        with SessionMaker() as session:
            if notification_id is None:
                session.add(notification_db)
                session.commit()
                session.refresh(notification_db)
                notification_id = notification_db.notification_id
            else:
                notification_db.notification_id = notification_id  # type: ignore
                session.merge(notification_db)
                session.commit()

        self.notification_id = notification_id  # type: ignore

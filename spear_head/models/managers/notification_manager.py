import datetime
from typing import Generator
from databases.engine import SessionMaker
from databases.db_types.notifications.notification_db import NotificationDB
from models.notifications.notification import Notification
from datetime import datetime

class NotificationManager:
    
    # -------------------- public methods --------------------
    @staticmethod
    def get_all_notifications_for_user(user_id: int) -> Generator[Notification, None, None]:
        with SessionMaker() as session:
            notification_dbs = session.query(NotificationDB).filter(
                NotificationDB.for_users.contains([user_id])
            ).all()

        for notification_db in notification_dbs:
            yield Notification.from_db(notification_db)

    @staticmethod
    def mark_notification_as_read(notification_id: int, user_id: int) -> None:
        with SessionMaker() as session:
            notification_db = session.query(NotificationDB).filter(
                NotificationDB.notification_id == notification_id
            ).first()
            if notification_db is None:
                return

            if user_id not in notification_db.read_by:
                notification_db.read_by.append(user_id)
                session.merge(notification_db)
                session.commit()

    @staticmethod
    def get_notifications_for_user_dated(user_id: int, start_date: datetime, end_date: datetime) -> Generator[Notification, None, None]:
        with SessionMaker() as session:
            notification_dbs = session.query(NotificationDB).filter(
                NotificationDB.for_users.contains([user_id]),
                NotificationDB.created_at >= start_date,
                NotificationDB.created_at <= end_date
            ).all()

        for notification_db in notification_dbs:
            yield Notification.from_db(notification_db)
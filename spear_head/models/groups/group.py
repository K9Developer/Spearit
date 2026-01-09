"""
group_id = Column(Integer, primary_key=True)
    group_name = Column(String(32), nullable=False, unique=True)
    description = Column(String(250), nullable=True)
    handlers = Column(JSON, nullable=True)  # list of user ids
    device_ids = Column(JSON, nullable=True)  # list of device ids
    created_at = Column(DateTime(timezone=True), server_default=func.now())
"""

from datetime import datetime

from databases.db_types.groups.group_db import GroupDB
from databases.engine import SessionMaker


class Group:

    def __init__(self, group_name: str, description: str, handler_ids: list[int], device_ids: list[int], created_at: datetime) -> None:
        self.group_name: str = group_name
        self.description: str = description
        self.handlers: list[int] = handler_ids
        self.device_ids: list[int] = device_ids
        self.created_at: datetime = created_at

        self.group_id: int | None = None

    @staticmethod
    def from_db(group_db: GroupDB) -> "Group":
        group = Group(
            group_name=group_db.group_name,  # type: ignore
            description=group_db.description or "",  # type: ignore
            handler_ids=group_db.handlers or [],  # type: ignore
            device_ids=group_db.device_ids or [],  # type: ignore
            created_at=group_db.created_at,  # type: ignore
        )
        group.group_id = group_db.group_id  # type: ignore
        return group

    def to_db(self) -> GroupDB:
        return GroupDB(
            group_name=self.group_name,
            description=self.description,
            handlers=self.handlers,
            device_ids=self.device_ids,
            created_at=self.created_at,
        )
    
    def update_db(self):
        group_id = self.group_id
        group_db = self.to_db()
        with SessionMaker() as session:
            if group_id is None:
                session.add(group_db)
                session.commit()
                session.refresh(group_db)
                group_id = group_db.group_id
            else:
                group_db.group_id = group_id  # type: ignore
                session.merge(group_db)
                session.commit()

        self.group_id = group_id  # type: ignore

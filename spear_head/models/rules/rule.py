import datetime
from typing import Any

from databases.db_types.rules.rule_db import RuleDB
from databases.engine import SessionMaker


class Rule:
    def __init__(self, name: str, author_id: int):
        self.rule_id: int | None = None
        self.rule_order: int = 0
        self.rule_type: str = ""
        self.event_types: list[str] = []
        self.conditions: list[dict[Any, Any]] = []
        self.responses: list[str] = []
        self.disabled_for_groups: list[int] = []
        self.is_active: bool = True
        self.priority: int = 0
        self.created_at: datetime.datetime = datetime.datetime.now()
        self.name = name
        self.author = author_id

        self.handlers: list[int] = []
        self.description: str = ""
    
    def to_db(self) -> RuleDB:
        return RuleDB(
            rule_order=self.rule_order,
            rule_type=self.rule_type,
            event_types=self.event_types,
            conditions=self.conditions,
            responses=self.responses,
            disabled_for_groups=self.disabled_for_groups,
            is_active=self.is_active,
            rule_name=self.name,
            priority=self.priority,
            created_at=self.created_at,
            handlers=self.handlers,
            description=self.description,
        )
   
    def update_db(self):
        rule_id = self.rule_id
        rule_db = self.to_db()
        with SessionMaker() as session:
            if rule_id is None:
                session.add(rule_db)
                session.commit()
                session.refresh(rule_db)
                rule_id = rule_db.rule_id
            else:
                rule_db.rule_id = rule_id  # type: ignore
                session.merge(rule_db)
                session.commit()

        self.rule_id = rule_id  # type: ignore
from typing import Any
from databases.db_types.rules.rule_db import RuleDB
from databases.engine import SessionMaker
import json

class RuleManager:

    @staticmethod
    def _rule_db_to_raw(rule_db: RuleDB) -> dict[str, Any]:
        return {
            "id": int(rule_db.rule_id), # type: ignore
            "order": int(rule_db.rule_order), # type: ignore
            "name": rule_db.rule_name,
            "enabled": bool(rule_db.is_active),
            "priority": int(rule_db.priority), # type: ignore
            "event_types": rule_db.event_types,
            "conditions": rule_db.conditions,
            "responses": rule_db.responses,
        }

    @staticmethod
    def get_raw_rules_json() -> str:
        rules = []
        with SessionMaker() as session:
            rules = session.query(RuleDB).filter(RuleDB.is_active == True).all()
        
        raw_rules = [RuleManager._rule_db_to_raw(rule) for rule in rules]
        return json.dumps(raw_rules)

from databases.db_types.rules.rule_db import RuleDB
import json
from sqlalchemy import func
from databases.engine import SessionMaker
from models.managers.group_manager import GroupManager
from models.rules.rule import Rule
from typing import Any, Generator
from models.devices.device import Device

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

    # -------------------- Public Methods --------------------

    @staticmethod
    def get_all_rules() -> Generator[Rule, None, None]:
        with SessionMaker() as session:
            rule_dbs = session.query(RuleDB).all()
            for rule_db in rule_dbs:
                rule = Rule.from_db(rule_db)
                yield rule

    @staticmethod
    def get_all_active_rules() -> Generator[Rule, None, None]:
        with SessionMaker() as session:
            rule_dbs = session.query(RuleDB).filter(RuleDB.is_active == True).all()
            for rule_db in rule_dbs:
                rule = Rule.from_db(rule_db)
                yield rule

    @staticmethod
    def get_rule_by_id(rule_id: int) -> Rule | None:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return None
            return Rule.from_db(rule_db)
        
    @staticmethod
    def delete_rule_by_id(rule_id: int) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            session.delete(rule_db)
            session.commit()
            return True
        
    @staticmethod
    def update_rule_description(rule_id: int, new_description: str) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            rule_db.description = new_description # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def update_rule_conditions(rule_id: int, new_conditions: list[dict[Any, Any]]) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            rule_db.conditions = new_conditions # type: ignore # TODO: Check if this works (giving list / dict to JSON column)
            session.commit()
            return True
        
    @staticmethod
    def update_rule_responses(rule_id: int, new_responses: list[str]) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            rule_db.responses = new_responses # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def update_rule_is_active(rule_id: int, is_active: bool) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            rule_db.is_active = is_active # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def update_rule_priority(rule_id: int, new_priority: int) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            rule_db.priority = new_priority # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def update_rule_name(rule_id: int, new_name: str) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            rule_db.rule_name = new_name # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def update_rule_event_types(rule_id: int, new_event_types: list[str]) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            rule_db.event_types = new_event_types # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def update_rule_type(rule_id: int, new_type: str) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            rule_db.rule_type = new_type # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def update_rule_order(rule_id: int, new_order: int) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            rule_db.rule_order = new_order # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def create_rule(
        rule_order: int,
        rule_type: str,
        event_types: list[str],
        conditions: list[dict[Any, Any]],
        responses: list[dict[Any, Any]],
        rule_name: str,
        priority: int = 0,
        description: str = "",
        active_for_groups: list[int] | None = None,
        handlers: list[int] | None = None,
        is_active: bool = True
    ) -> Rule:
        with SessionMaker() as session:
            rule_db = RuleDB(
                rule_order=rule_order,
                rule_type=rule_type,
                event_types=event_types,
                conditions=conditions,
                responses=responses,
                rule_name=rule_name,
                priority=priority,
                description=description,
                active_for_groups=active_for_groups,
                handlers=handlers,
                is_active=is_active
            )
            session.add(rule_db)
            session.commit()
            session.refresh(rule_db)
            rule = Rule.from_db(rule_db)
            return rule
        
    @staticmethod
    def update_rule_active_for_groups(rule_id: int, active_for_groups: list[int]) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            rule_db.active_for_groups = active_for_groups # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def update_rule_handlers(rule_id: int, handlers: list[int]) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            rule_db.handlers = handlers # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def add_handler_to_rule(rule_id: int, handler_user_id: int) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            if handler_user_id in rule_db.handlers:
                return False
            rule_db.handlers.append(handler_user_id) # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def remove_handler_from_rule(rule_id: int, handler_user_id: int) -> bool:
        with SessionMaker() as session:
            rule_db = session.get(RuleDB, rule_id)
            if rule_db is None:
                return False
            if handler_user_id not in rule_db.handlers:
                return False
            rule_db.handlers.remove(handler_user_id) # type: ignore
            session.commit()
            return True
    
    @staticmethod
    def get_rules_handled_by_user(user_id: int) -> Generator[Rule, None, None]:
        with SessionMaker() as session:
            rule_dbs = session.query(RuleDB).filter(func.json_contains(RuleDB.handlers, f'[ {user_id} ]')).all()
            for rule_db in rule_dbs:
                yield Rule.from_db(rule_db)

    @staticmethod
    def get_rules_matching_device(device: Device) -> Generator[Rule, None, None]:
        if device.device_id is None: return 
        with SessionMaker() as session:
            groups = GroupManager.get_groups_for_device(device.device_id)
            group_ids = [group.group_id for group in groups if group.group_id is not None]
            rule_dbs = session.query(RuleDB).filter(
                RuleDB.is_active == True,
                func.or_(
                    RuleDB.active_for_groups == None,
                    func.json_overlaps(RuleDB.active_for_groups, group_ids)
                )
            ).all()
            for rule_db in rule_dbs:
                yield Rule.from_db(rule_db)
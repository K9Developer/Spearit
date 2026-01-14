# pyright: reportArgumentType=false
from typing import Any, Generator

from sqlalchemy import func

from databases.db_types.events.event_db import EventDB
from databases.engine import SessionMaker
from models.events.types.event import BaseEvent, EventKind
from models.events.types.packet_event import PacketEvent
from models.events.types.event_type import EventType_

class EventManager:
    # ------------------------ Public Methods ----------------------- #

    @staticmethod
    def get_all_events() -> Generator[EventType_, None, None]:
        with SessionMaker() as session:
            event_dbs = session.query(EventDB).order_by(EventDB.timestamp).all()
            for event_db in event_dbs:
                if event_db.event_type == EventKind.to_str(EventKind.PACKET): # type: ignore
                    event = PacketEvent.from_db(event_db)
                else:
                    event = BaseEvent.from_db(event_db)
                
                yield event
    
    @staticmethod
    def get_event_by_id(event_id: int) -> EventType_ | None:
        with SessionMaker() as session:
            event_db = session.query(EventDB).filter(EventDB.event_id == event_id).first()
            if event_db is None:
                return None
            
            if event_db.event_type == EventKind.to_str(EventKind.PACKET): # type: ignore
                event = PacketEvent.from_db(event_db)
            else:
                event = BaseEvent.from_db(event_db)
            
            return event
    
    @staticmethod
    def delete_event_by_id(event_id: int) -> bool:
        with SessionMaker() as session:
            event_db = session.query(EventDB).filter(EventDB.event_id == event_id).first()
            if event_db is None:
                return False
            
            session.delete(event_db)
            session.commit()
            return True
    
    @staticmethod
    def filter_event_by_json_data(filter_path: str, value: Any) -> Generator[EventType_, None, None]:
        with SessionMaker() as session:
            query = session.query(EventDB).where(func.json_extract(EventDB.event_data, filter_path) == value)
            event_dbs = query.all()
            for event_db in event_dbs:
                yield BaseEvent.from_db(event_db)
    
    @staticmethod
    def get_events_by_kind(event_kind: EventKind) -> Generator[EventType_, None, None]:
        with SessionMaker() as session:
            event_dbs = session.query(EventDB).filter(EventDB.event_type == EventKind.to_str(event_kind)).all()
            for event_db in event_dbs:
                if event_db.event_type == EventKind.to_str(EventKind.PACKET): # type: ignore
                    event = PacketEvent.from_db(event_db)
                else:
                    event = BaseEvent.from_db(event_db)
                
                yield event
    
    @staticmethod
    def get_events_by_campaign_id(campaign_id: int) -> Generator[EventType_, None, None]:
        with SessionMaker() as session:
            event_dbs = session.query(EventDB).filter(EventDB.campaign_id == campaign_id).all()
            for event_db in event_dbs:
                if event_db.event_type == EventKind.to_str(EventKind.PACKET): # type: ignore
                    event = PacketEvent.from_db(event_db)
                else:
                    event = BaseEvent.from_db(event_db)
                
                yield event
    
    @staticmethod
    def get_events_by_rule_id(rule_id: int) -> Generator[EventType_, None, None]:
        with SessionMaker() as session:
            event_dbs = session.query(EventDB).filter(EventDB.rule_id == rule_id).all()
            for event_db in event_dbs:
                if event_db.event_type == EventKind.to_str(EventKind.PACKET): # type: ignore
                    event = PacketEvent.from_db(event_db)
                else:
                    event = BaseEvent.from_db(event_db)
                
                yield event

    @staticmethod
    def get_events_by_device_id(device_id: int) -> Generator[EventType_, None, None]:
        with SessionMaker() as session:
            event_dbs = session.query(EventDB).filter(EventDB.device_id == device_id).all()
            for event_db in event_dbs:
                if event_db.event_type == EventKind.to_str(EventKind.PACKET): # type: ignore
                    event = PacketEvent.from_db(event_db)
                else:
                    event = BaseEvent.from_db(event_db)
                
                yield event
    
    @staticmethod
    def get_total_event_count() -> int:
        with SessionMaker() as session:
            count = session.query(func.count(EventDB.event_id)).scalar()
            return count if count is not None else 0
            
    

# pyright: reportArgumentType=false
import base64
from queue import Empty, Queue
from typing import Any, Generator

from sqlalchemy import func

from databases.db_types.events.event_db import EventDB
from databases.engine import SessionMaker
from models.managers.device_manager import DeviceManager
from models.managers.campaign_manager import CampaignManager
from models.events.types.event import BaseEvent, EventKind, ViolationResponse
from models.events.types.packet_event import PacketDeviceInfo, PacketDirection, PacketEvent, PacketPayload, ProcessInfo
from models.events.types.event_type import EventType_
from utils.parser import protocol_entry_from_id


class EventManager:

    event_queue: Queue[EventType_] = Queue()

    @staticmethod
    def _submit_packet_event(json_event: dict[str, str | dict[str, str]]):
        packet_event = PacketEvent(
            timestamp_ns=json_event["timestamp_ns"], 
            violated_rule_id=json_event["violated_rule_id"],
            violation_type=json_event["violation_type"],
            violation_response=ViolationResponse.from_str(json_event["violation_response"]),
            protocol=protocol_entry_from_id(json_event["protocol"]),
            is_connection_establishing=json_event["is_connection_establishing"],
            direction=PacketDirection.from_str(json_event["direction"]),

            process=ProcessInfo(
                process_id=json_event["process"]["pid"],
                name=json_event["process"]["name"]
            ),

            source=PacketDeviceInfo(
                ip=json_event["ip"]["src_ip"],
                port=json_event["ip"]["src_port"],
                mac=json_event["src_mac"]
            ),

            dest=PacketDeviceInfo(
                ip=json_event["ip"]["dst_ip"],
                port=json_event["ip"]["dst_port"],
                mac=json_event["dst_mac"]
            ),

            payload=PacketPayload(
                full_size=json_event["payload"]["full_size"],
                data=bytearray(base64.b64decode(json_event["payload"]["data"]))
            )
        )
        EventManager.event_queue.put(packet_event)
        DeviceManager._update_device_from_packet_event(packet_event)

    @staticmethod
    def _process_event():
        try:
            curr_event = EventManager.event_queue.get(block = False)
            curr_event.update_db()
            CampaignManager._process_event(curr_event)

        except Empty:
            return
        
    @staticmethod
    def _submit_event(json_event: dict[str, str | dict[str, str]], type_: EventKind) -> bool:
        # try:
            if type_ == EventKind.PACKET:
                EventManager._submit_packet_event(json_event)
            else:
                raise Exception("Unknown event type")
            
            return True
        # except Exception as e:
        #     Logger.error(f"Failed to submit event: {e}")
        #     return False

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
            
    

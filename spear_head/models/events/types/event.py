from enum import Enum
from dataclasses import dataclass

from databases.db_types.events.event_db import EventDB
from databases.db_types.devices.device import get_or_create_device_db
from databases.engine import SessionMaker
from models.devices.device import Device
from models.managers.device_manager import DeviceManager

class ViolationType(Enum):
    PACKET = 0
    CONNECTION = 1

class EventKind(Enum):
    PACKET = 0

    @staticmethod
    def from_str(s: str) -> 'EventKind':
        if s == "packet": return EventKind.PACKET
        return EventKind.PACKET
    
    @staticmethod
    def to_str(kind: 'EventKind') -> str:
        if kind == EventKind.PACKET: return "packet"
        return "packet"

class ViolationResponse(Enum):
    AIR_GAP = 0
    KILL = 1
    ISOLATE = 2
    ALERT = 3
    RUN = 4

    @staticmethod
    def from_str(s: str) -> 'ViolationResponse':
        if s == "air_gap": return ViolationResponse.AIR_GAP
        if s == "kill": return ViolationResponse.KILL
        if s == "isolate": return ViolationResponse.ISOLATE
        if s == "alert": return ViolationResponse.ALERT
        if s == "run": return ViolationResponse.RUN
        return ViolationResponse.ALERT

@dataclass(slots=True, init=False)
class BaseEvent:
    timestamp_ns: int
    violated_rule_id: int
    violation_type: ViolationType
    violation_response: ViolationResponse
    event_type: EventKind
    device: Device
    event_id: int | None = None
    campaign_id: int | None = None

    def __init__(
        self,
        timestamp_ns: int,
        violated_rule_id: int,
        violation_type: ViolationType,
        violation_response: ViolationResponse,
        event_type: EventKind,
        device_mac: str
    ) -> None:
        self.violated_rule_id = violated_rule_id
        self.violation_type = violation_type
        self.violation_response = violation_response
        self.event_type = event_type
        self.timestamp_ns = timestamp_ns
        dvc = DeviceManager.get_device_by_mac(device_mac) 
        if dvc is None:
            dvc = DeviceManager._create_device(mac_address=device_mac)
        self.device = dvc
        self.event_id = None
        self.campaign_id = None
    
    def to_db(self) -> EventDB:
        """
        Convert this BaseEvent model instance to an EventDB instance.
        
        Returns:
            EventDB: The corresponding EventDB instance.
        """
        return EventDB(
            device_id = get_or_create_device_db(self.device)[1],
            rule_id = self.violated_rule_id,
            campaign_id = None,
            event_type = self.event_type.name,
            event_data = {},
            timestamp = self.timestamp_ns,
            response_taken = None
        )
    
    def update_db(self):
        event_id = self.event_id
        event_db = self.to_db()
        with SessionMaker() as session:
            if event_id is None:
                session.add(event_db)
                session.commit()
                session.refresh(event_db)
                event_id = event_db.event_id
            else:
                event_db.event_id = event_id  # type: ignore
                session.merge(event_db)
                session.commit()

        self.event_id = event_id  # type: ignore

    @staticmethod
    def from_db(event_db: EventDB) -> 'BaseEvent':
        """
        Create a BaseEvent instance from an EventDB instance.
        
        Args:
            event_db (EventDB): The EventDB instance to convert.

        Returns:
            BaseEvent: The corresponding BaseEvent instance.
        """ 

        device = DeviceManager.get_device_by_id(event_db.device_id) # type: ignore
        if device is None:
            raise ValueError(f"Device with ID {event_db.device_id} not found.")
        
        event = BaseEvent(
            timestamp_ns=event_db.timestamp, # type: ignore
            violated_rule_id=event_db.rule_id, # type: ignore
            violation_type=ViolationType.PACKET,
            violation_response=ViolationResponse.from_str(event_db.response_taken) if event_db.response_taken is not None else ViolationResponse.ALERT, # type: ignore
            event_type=EventKind.from_str(event_db.event_type), # type: ignore
            device_mac=device.mac_address # type: ignore
        )

        event.event_id = event_db.event_id # type: ignore
        event.campaign_id = event_db.campaign_id # type: ignore
        event.device = device

        return event
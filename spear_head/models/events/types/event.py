from enum import Enum
from attr import dataclass

from databases.db_types.events.event_db import EventDB
from databases.db_types.devices.device import get_or_create_device_db
from models.devices.device import Device

class ViolationType(Enum):
    PACKET = 0
    CONNECTION = 1

class EventType(Enum):
    PACKET = 0

    @staticmethod
    def from_str(s: str) -> 'EventType':
        if s == "packet": return EventType.PACKET
        return EventType.PACKET

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
    event_type: EventType
    device: Device

    def __init__(
        self,
        timestamp_ns: int,
        violated_rule_id: int,
        violation_type: ViolationType,
        violation_response: ViolationResponse,
        event_type: EventType,
        device_mac: str
    ) -> None:
        self.violated_rule_id = violated_rule_id
        self.violation_type = violation_type
        self.violation_response = violation_response
        self.event_type = event_type
        self.timestamp_ns = timestamp_ns
        self.device = Device(
            device_name="unknown",
            os_details="unknown",
            ip_address="unknown",
            mac_address=device_mac,
            group=None,
            last_heartbeat=None
        )
    
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
            responses_taken = None
        )
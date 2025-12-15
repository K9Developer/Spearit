from enum import Enum
from attr import dataclass

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

@dataclass(slots=True)
class BaseEvent:
    timestamp: int
    violated_rule_id: int
    violation_type: ViolationType
    violation_response: ViolationResponse
    event_type: EventType
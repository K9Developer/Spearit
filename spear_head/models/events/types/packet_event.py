import base64
import datetime
from enum import Enum
from typing import Any
from attr import dataclass

from databases.db_types.devices.device import get_or_create_device_db
from databases.db_types.events.event_db import EventDB
from models.events.types.event import BaseEvent, EventType, ViolationResponse, ViolationType

class PacketDirection(Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"

    @staticmethod
    def from_str(s: str) -> 'PacketDirection':
        if s.lower() == "inbound": return PacketDirection.INBOUND
        if s.lower() == "outbound": return PacketDirection.OUTBOUND
        return PacketDirection.INBOUND

@dataclass(slots=True)
class ProcessInfo:
    process_id: int
    name: str

@dataclass(slots=True)
class PacketDeviceInfo:
    ip: str | None
    port: int | None
    mac: str

@dataclass(slots=True)
class PacketPayload:
    full_size: int
    data: bytearray

@dataclass
class ProtocolInfoEntry:
    libc_name: str
    name: str

@dataclass(slots=True, init=False)
class PacketEvent(BaseEvent):
    protocol: ProtocolInfoEntry
    is_connection_establishing: bool
    direction: PacketDirection
    process: ProcessInfo

    source: PacketDeviceInfo
    dest: PacketDeviceInfo

    payload: PacketPayload

    def __init__(
        self,
        timestamp_ns: int,
        violated_rule_id: int,
        violation_type: ViolationType,
        violation_response: ViolationResponse,
        protocol: ProtocolInfoEntry,
        is_connection_establishing: bool,
        direction: PacketDirection,
        process: ProcessInfo,
        source: PacketDeviceInfo,
        dest: PacketDeviceInfo,
        payload: PacketPayload,
    ) -> None:
        super().__init__(
            timestamp_ns=timestamp_ns,
            violated_rule_id=violated_rule_id,
            violation_type=violation_type,
            violation_response=violation_response,
            event_type=EventType.PACKET,
            device_mac="ff:ff:ff:ff:ff:ff" # TODO: when the wrapper also attaches a mac
        )

        self.protocol = protocol
        self.is_connection_establishing = is_connection_establishing
        self.direction = direction
        self.process = process
        self.source = source
        self.dest = dest
        self.payload = payload

    def __str__(self) -> str:
        src = (
            f"{self.source.ip}:{self.source.port}"
            if self.source.ip else "N/A"
        )
        dst = (
            f"{self.dest.ip}:{self.dest.port}"
            if self.dest.ip else "N/A"
        )

        return (
            f"[{self.protocol.name}] "
            f"{src} [{self.source.mac}] → "
            f"{dst} [{self.dest.mac}] "
            f"proc={self.process.name}({self.process.process_id}) "
            f"payload={self.payload.full_size}/{len(self.payload.data)}B "
            f"establishing={self.is_connection_establishing}"
        )
    
    def to_json(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol.name,
            "is_connection_establishing": self.is_connection_establishing,
            "direction": self.direction.value,
            "process": {
                "process_id": self.process.process_id,
                "name": self.process.name
            },
            "source": {
                "ip": self.source.ip,
                "port": self.source.port,
                "mac": self.source.mac
            },
            "dest": {
                "ip": self.dest.ip,
                "port": self.dest.port,
                "mac": self.dest.mac
            },
            "payload": {
                "full_size": self.payload.full_size,
                "data": base64.b64encode(self.payload.data).decode('utf-8')
            }
        }

    def to_db(self) -> EventDB:
        """
        Convert this PacketEvent model instance to an EventDB instance.
        Returns:
            EventDB: The corresponding EventDB instance.
        """
        return EventDB(
            device_id = get_or_create_device_db(self.device)[1],
            rule_id = self.violated_rule_id,
            campaign_id = None,
            event_type = self.event_type.name,
            event_data = self.to_json(),
            timestamp = datetime.datetime.fromtimestamp(
                self.timestamp_ns / 1_000_000_000,
                tz=datetime.timezone.utc,
            ),
            responses_taken = self.violation_response.name
        )

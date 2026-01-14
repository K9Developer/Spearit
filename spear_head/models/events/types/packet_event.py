import base64
import datetime
from enum import Enum
from typing import Any
from dataclasses import dataclass

from databases.db_types.devices.device import get_or_create_device_db
from databases.db_types.events.event_db import EventDB
from databases.engine import SessionMaker
from models.events.types.event import BaseEvent, EventKind, ViolationResponse, ViolationType
from utils.types import ProtocolInfoEntry

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

@dataclass(init=False)
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
            event_type=EventKind.PACKET,
            device_mac=source.mac if direction == PacketDirection.OUTBOUND else dest.mac,
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
    
    def __repr__(self) -> str:
        return (
            f"PacketEvent(timestamp_ns={self.timestamp_ns}, "
            f"violated_rule_id={self.violated_rule_id}, "
            f"violation_type={self.violation_type}, "
            f"violation_response={self.violation_response}, "
            f"protocol={self.protocol}, "
            f"is_connection_establishing={self.is_connection_establishing}, "
            f"direction={self.direction}, "
            f"process={self.process}, "
            f"source={self.source}, "
            f"dest={self.dest}, "
            f"payload=\"{bytes(self.payload.data).decode('utf-8', errors='ignore')}\""
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

    # TODO: This func is hella sus, check if this works
    @staticmethod
    def from_db(event_db: EventDB) -> 'PacketEvent':
        event_data = event_db.event_data # TODO: Check if this works

        packet_event = PacketEvent(
            timestamp_ns=int(event_db.timestamp.timestamp() * 1_000_000_000),
            violated_rule_id=event_db.rule_id, # type: ignore
            violation_type=ViolationType(event_data.get("violation_type", 0)), # type: ignore
            violation_response=ViolationResponse.from_str(event_data.get("violation_response", "NONE")),
            protocol=ProtocolInfoEntry(
                libc_name=event_data["protocol_libc_name"],  # type: ignore
                name=event_data["protocol_name"] # type: ignore
            ),
            is_connection_establishing=event_data["is_connection_establishing"], # type: ignore
            direction=PacketDirection.from_str(event_data["direction"]), # type: ignore
            process=ProcessInfo(
                process_id=event_data["process"]["process_id"], # type: ignore
                name=event_data["process"]["name"] # type: ignore
            ),
            source=PacketDeviceInfo(
                ip=event_data["source"]["ip"], # type: ignore
                port=event_data["source"]["port"], # type: ignore
                mac=event_data["source"]["mac"] # type: ignore
            ),
            dest=PacketDeviceInfo(
                ip=event_data["dest"]["ip"], # type: ignore
                port=event_data["dest"]["port"], # type: ignore
                mac=event_data["dest"]["mac"] # type: ignore
            ),
            payload=PacketPayload(
                full_size=event_data["payload"]["full_size"], # type: ignore
                data=bytearray(base64.b64decode(event_data["payload"]["data"])) # type: ignore
            )
        )

        packet_event.event_id = event_db.event_id  # type: ignore
        packet_event.campaign_id = event_db.campaign_id  # type: ignore

        return packet_event

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
            response_taken = self.violation_response.name
        )
    
    def update_db(self):
        event_db = self.to_db()
        with SessionMaker() as session:
            session.add(event_db)
            session.commit()
            session.refresh(event_db)
        self.event_id = int(event_db.event_id) # type: ignore


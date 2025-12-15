from enum import Enum
from attr import dataclass

from spear_head.models.events.types.event import BaseEvent

class PacketDirection(Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"

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

@dataclass(slots=True)
class PacketEvent(BaseEvent):
    protocol: ProtocolInfoEntry
    is_connection_establishing: bool
    direction: PacketDirection
    process: ProcessInfo

    source: PacketDeviceInfo
    dest: PacketDeviceInfo

    payload: PacketPayload

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

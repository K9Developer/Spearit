from __future__ import annotations
from re import L
from typing import TYPE_CHECKING

from models.managers.heartbeat_manager import HeartbeatManager
if TYPE_CHECKING: from models.heartbeats.heartbeat import Heartbeat  # type-only

from dataclasses import dataclass, field

from databases.db_types.devices.device_db import DeviceDB
from databases.engine import SessionMaker


@dataclass(slots=True)
class Device:
    device_name: str
    os_details: str
    ip_address: str
    mac_address: str
    groups: list[int]
    last_heartbeat: Heartbeat | None
    handlers: list[int] = field(default_factory=list)
    note: str = ""

    device_id: int | None = None

    def __str__(self) -> str:
        groups = self.groups if self.groups else "ungrouped"
        heartbeat = (
            self.last_heartbeat
            if self.last_heartbeat is not None
            else "never"
        )

        return (
            f"Device("
            f"name={self.device_name}, "
            f"os={self.os_details}, "
            f"ip={self.ip_address}, "
            f"mac={self.mac_address}, "
            f"groups={groups}, "
            f"last_heartbeat={heartbeat}"
            f")"
        )
    
    @staticmethod
    def from_db(device_db: DeviceDB) -> "Device":
        return Device(
            device_name=device_db.device_name or "Unknown Device", # type: ignore
            os_details=device_db.operating_system_details or "Unknown OS", # type: ignore
            ip_address=device_db.last_known_ip_address or "0.0.0.0", # type: ignore
            mac_address=device_db.mac_address, # type: ignore
            groups=device_db.groups, # type: ignore
            last_heartbeat=HeartbeatManager.get_heartbeat_by_id(device_db.last_heartbeat_id), # type: ignore
            handlers=device_db.handlers or [], # type: ignore
            note=device_db.note or "", # type: ignore 
            device_id=device_db.device_id, # type: ignore
        )

    def to_db(self) -> DeviceDB:
        """
        Convert this Device model instance to a DeviceDB instance.
        
        Returns:
            DeviceDB: The corresponding DeviceDB instance.
        """

        return DeviceDB(
            device_name=self.device_name,
            operating_system_details=self.os_details,
            last_known_ip_address=self.ip_address,
            mac_address=self.mac_address,
            handlers=self.handlers,
            note=self.note,
            groups=self.groups,
            last_heartbeat_id=self.last_heartbeat.heartbeat_id if self.last_heartbeat else None
        )

    def update_db(self):
        device_id = self.device_id
        device_db = self.to_db()
        with SessionMaker() as session:
            if device_id is None:
                session.add(device_db)
                session.commit()
                session.refresh(device_db)
                device_id = device_db.device_id
            else:
                device_db.device_id = device_id # type: ignore
                session.merge(device_db)
                session.commit()

    @staticmethod
    def default() -> "Device":
        return Device(
            device_name="Unknown Device",
            os_details="Unknown OS",
            ip_address="0.0.0.0",
            mac_address="00:00:00:00:00:00",
            groups=[],
            last_heartbeat=None
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Device): return False

        if self.device_id is not None and other.device_id is not None:
            return self.device_id == other.device_id
    
        return str(self.mac_address).lower() == str(other.mac_address).lower()
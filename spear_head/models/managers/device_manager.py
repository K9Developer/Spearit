from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING: from models.events.types.packet_event import PacketEvent  # type-only

from models.logger import Logger
from databases.engine import SessionMaker
from databases.db_types.devices.device_db import DeviceDB

class HeartbeatDeviceInformation:
    def __init__(self, device_name: str, os_details: str, ip_address: str, mac_address: str) -> None:
        self.device_name = device_name
        self.os_details = os_details
        self.ip_address = ip_address
        self.mac_address = mac_address
    
    @staticmethod
    def default() -> 'HeartbeatDeviceInformation':
        return HeartbeatDeviceInformation(
            device_name="",
            os_details="",
            ip_address="",
            mac_address=""
        )

class DeviceManager:
    
    # TODO: This feels slow
    @staticmethod
    def submit_device_info(device_info: HeartbeatDeviceInformation) -> int:
        with SessionMaker() as session:
            existing_device = session.query(DeviceDB).filter_by(mac_address=device_info.mac_address).first()
            if existing_device is None:
                new_device = DeviceDB(
                    device_name=device_info.device_name or "Unknown Device",
                    operating_system_details=device_info.os_details or "Unknown OS",
                    last_known_ip_address=device_info.ip_address or "0.0.0.0",
                    mac_address=device_info.mac_address,
                    handlers=[],
                    note="",
                )
                session.add(new_device)
                session.commit()
                Logger.debug(f"Added new device (MAC: {device_info.mac_address}) - {new_device.device_name}")
                return new_device.device_id  # type: ignore
            else:
                existing_device.device_name = device_info.device_name or existing_device.device_name  # type: ignore
                existing_device.operating_system_details = device_info.os_details or existing_device.operating_system_details  # type: ignore
                existing_device.last_known_ip_address = device_info.ip_address or existing_device.last_known_ip_address  # type: ignore
                session.commit()
                return existing_device.device_id  # type: ignore
    
    @staticmethod
    def update_device_from_packet_event(event: PacketEvent):
        hdi1 = HeartbeatDeviceInformation.default()
        hdi1.mac_address = event.source.mac
        hdi1.ip_address = event.source.ip or "0.0.0.0"
        DeviceManager.submit_device_info(hdi1)

        hdi2 = HeartbeatDeviceInformation.default()
        hdi2.mac_address = event.dest.mac
        hdi2.ip_address = event.dest.ip or "0.0.0.0"
        DeviceManager.submit_device_info(hdi2)

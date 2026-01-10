from __future__ import annotations

from typing import TYPE_CHECKING, Generator

from models.managers.callback_manager import CallbackEvent, CallbackManager
if TYPE_CHECKING: from models.events.types.packet_event import PacketEvent  # type-only

from models.devices.device import Device
from models.devices.device import Device
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
    def _submit_device_info(device_info: HeartbeatDeviceInformation) -> int:
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
                CallbackManager.trigger_event(CallbackEvent.NEW_DEVICE, Device.from_db(new_device)) # type: ignore
                return new_device.device_id  # type: ignore
            else:
                existing_device.device_name = device_info.device_name or existing_device.device_name  # type: ignore
                existing_device.operating_system_details = device_info.os_details or existing_device.operating_system_details  # type: ignore
                existing_device.last_known_ip_address = device_info.ip_address or existing_device.last_known_ip_address  # type: ignore
                session.commit()
                return existing_device.device_id  # type: ignore
    
    @staticmethod
    def _update_device_from_packet_event(event: PacketEvent):
        hdi1 = HeartbeatDeviceInformation.default()
        hdi1.mac_address = event.source.mac
        hdi1.ip_address = event.source.ip or "0.0.0.0"
        DeviceManager._submit_device_info(hdi1)

        hdi2 = HeartbeatDeviceInformation.default()
        hdi2.mac_address = event.dest.mac
        hdi2.ip_address = event.dest.ip or "0.0.0.0"
        DeviceManager._submit_device_info(hdi2)

    @staticmethod
    def _create_device(mac_address: str) -> Device:
        with SessionMaker() as session:
            new_device_db = DeviceDB(
                device_name="Unknown Device",
                operating_system_details="Unknown OS",
                last_known_ip_address="0.0.0.0",
                mac_address=mac_address,
                handlers=[],
                note="",
            )
            session.add(new_device_db)
            session.commit()
            return Device.from_db(new_device_db)

    # ------------------ Public Methods -----------------

    @staticmethod
    def get_all_devices() -> Generator[Device, None, None]:
        with SessionMaker() as session:
            device_dbs = session.query(DeviceDB).all()
            for device_db in device_dbs:
                device = Device.from_db(device_db)
                yield device

    @staticmethod
    def get_device_by_id(device_id: int) -> Device | None:
        with SessionMaker() as session:
            device_db = session.query(DeviceDB).filter_by(device_id=device_id).first()
            if device_db is None:
                return None
            return Device.from_db(device_db)
        
    @staticmethod
    def get_device_by_mac(mac_address: str) -> Device | None:
        with SessionMaker() as session:
            device_db = session.query(DeviceDB).filter_by(mac_address=mac_address).first()
            if device_db is None:
                return None
            return Device.from_db(device_db)
    
    @staticmethod
    def get_devices_containing_substring(substring: str) -> Generator[Device, None, None]:
        with SessionMaker() as session:
            device_dbs = session.query(DeviceDB).filter(
                DeviceDB.device_name.ilike(f"%{substring}%") |
                DeviceDB.operating_system_details.ilike(f"%{substring}%") |
                DeviceDB.mac_address.ilike(f"%{substring}%") |
                DeviceDB.last_known_ip_address.ilike(f"%{substring}%") |
                DeviceDB.note.ilike(f"%{substring}%")
            ).all()
            for device_db in device_dbs:
                device = Device.from_db(device_db)
                yield device

    @staticmethod
    def get_device_count() -> int:
        with SessionMaker() as session:
            count = session.query(DeviceDB).count()
            return count
        
    @staticmethod
    def get_devices_by_operating_system(os_details: str) -> Generator[Device, None, None]:
        with SessionMaker() as session:
            device_dbs = session.query(DeviceDB).filter(DeviceDB.operating_system_details == os_details).all()
            for device_db in device_dbs:
                device = Device.from_db(device_db)
                yield device

    @staticmethod
    def get_devices_by_ip_address(ip_address: str) -> Generator[Device, None, None]:
        with SessionMaker() as session:
            device_dbs = session.query(DeviceDB).filter(DeviceDB.last_known_ip_address == ip_address).all()
            for device_db in device_dbs:
                device = Device.from_db(device_db)
                yield device
    
    @staticmethod
    def set_device_note(device_id: int, note: str) -> bool:
        with SessionMaker() as session:
            device_db = session.query(DeviceDB).filter_by(device_id=device_id).first()
            if device_db is None:
                return False
            device_db.note = note # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def remove_device_handler(device_id: int, user_id: int) -> bool:
        with SessionMaker() as session:
            device_db = session.query(DeviceDB).filter_by(device_id=device_id).first()
            if device_db is None:
                return False
            if user_id in device_db.handlers: # type: ignore
                device_db.handlers.remove(user_id) # type: ignore
                session.commit()
            return True
    
    @staticmethod
    def add_device_handler(device_id: int, user_id: int) -> bool:
        with SessionMaker() as session:
            device_db = session.query(DeviceDB).filter_by(device_id=device_id).first()
            if device_db is None:
                return False
            if user_id not in device_db.handlers: # type: ignore
                device_db.handlers.append(user_id) # type: ignore
                session.commit()
            return True
    
    @staticmethod
    def get_devices_by_handler(user_id: int) -> Generator[Device, None, None]:
        with SessionMaker() as session:
            device_dbs = session.query(DeviceDB).filter(DeviceDB.handlers.contains([user_id])).all() # type: ignore
            for device_db in device_dbs:
                device = Device.from_db(device_db)
                yield device
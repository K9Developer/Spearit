from __future__ import annotations

from typing import TYPE_CHECKING, Generator

from models.managers.callback_manager import CallbackEvent, CallbackManager
if TYPE_CHECKING: from models.events.types.packet_event import PacketEvent  # type-only

from models.devices.device import Device
from models.logger import Logger
from databases.engine import SessionMaker
from databases.db_types.devices.device_db import DeviceDB
from utils.types import HeartbeatDeviceInformation
from databases.db_types.groups.group_db import GroupDB

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
                CallbackManager.trigger_event(CallbackEvent.NEW_DEVICE, Device.from_db(new_device)) # type: ignore
                return new_device.device_id  # type: ignore
            else:
                existing_device.device_name = device_info.device_name or existing_device.device_name  # type: ignore
                existing_device.operating_system_details = device_info.os_details or existing_device.operating_system_details  # type: ignore
                existing_device.last_known_ip_address = device_info.ip_address or existing_device.last_known_ip_address  # type: ignore
                session.commit()
                return existing_device.device_id  # type: ignore
    
    @staticmethod
    def _update_device_from_packet_event(event: PacketEvent) -> tuple[int, int]:
        hdi1 = HeartbeatDeviceInformation.default()
        hdi1.mac_address = event.source.mac
        hdi1.ip_address = event.source.ip or "0.0.0.0"
        device_id1 = DeviceManager.submit_device_info(hdi1)

        hdi2 = HeartbeatDeviceInformation.default()
        hdi2.mac_address = event.dest.mac
        hdi2.ip_address = event.dest.ip or "0.0.0.0"
        device_id2 = DeviceManager.submit_device_info(hdi2)
        return device_id1, device_id2

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
            device_db.handlers = list(device_db.handlers or []) # type: ignore
            if user_id in device_db.handlers: # type: ignore
                device_db.handlers.remove(user_id) # type: ignore
                session.commit()
            return True
    
    @staticmethod
    def get_handlers_for_device(device_id: int) -> list[int]:
        with SessionMaker() as session:
            device_db = session.query(DeviceDB).filter_by(device_id=device_id).first()
            if device_db is None:
                return []
            users = list(device_db.handlers or [])
            groups = device_db.groups or []
            for group_id in groups:
                group_db = session.query(GroupDB).filter_by(group_id=group_id).first()
                if group_db is not None:
                    users.extend(group_db.handlers or [])
            return list(set(users))

    @staticmethod
    def add_device_handler(device_id: int, user_id: int) -> bool:
        with SessionMaker() as session:
            device_db = session.query(DeviceDB).filter_by(device_id=device_id).first()
            if device_db is None:
                return False
            if user_id not in device_db.handlers: # type: ignore
                device_db.handlers = list(device_db.handlers or []) # type: ignore
                device_db.handlers.append(user_id) # type: ignore
                session.commit()
            return True
    
    @staticmethod
    def get_devices_by_handler(user_id: int) -> Generator[Device, None, None]:
        from models.managers.user_manager import UserManager

        user = UserManager.get_user_by_id(user_id)
        if user is None: return
        is_superuser = user.is_superuser()
        if is_superuser:
            yield from DeviceManager.get_all_devices()
            return

        with SessionMaker() as session:
            device_dbs = session.query(DeviceDB).filter(DeviceDB.handlers.contains([user_id])).all() # type: ignore
            for device_db in device_dbs:
                device = Device.from_db(device_db)
                yield device
        
        with SessionMaker() as session:
            group_dbs = session.query(GroupDB).filter(GroupDB.handlers.contains(user_id)).all() # type: ignore
            for group_db in group_dbs:
                for device_id in group_db.device_ids: # type: ignore
                    device_db = session.query(DeviceDB).filter_by(device_id=device_id).first()
                    if device_db is not None:
                        yield Device.from_db(device_db)

    @staticmethod
    def update_device(device_id: int, device_name: str, groups: list[int], handlers: list[int]) -> bool:
        with SessionMaker() as session:
            device_db = session.query(DeviceDB).filter_by(device_id=device_id).first()
            if device_db is None:
                return False
            device_db.name = device_name
            device_db.groups = groups # type: ignore
            device_db.handlers = handlers # type: ignore
            session.commit()
            return True
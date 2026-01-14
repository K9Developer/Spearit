from sqlalchemy import Integer, cast, exists, func, select
from databases.db_types.devices.device_db import DeviceDB
from databases.engine import SessionMaker
from typing import Generator
from databases.db_types.groups.group_db import GroupDB
from models.devices.device import Device
from models.groups.group import Group

class GroupManager:
    
    # -------------------------- Public Methods --------------------------

    @staticmethod
    def get_all_groups() -> Generator[Group, None, None]:
        with SessionMaker() as session:
            group_dbs = session.query(GroupDB).all()
            for group_db in group_dbs:
                group = Group.from_db(group_db)
                yield group

    @staticmethod
    def get_group_by_id(group_id: int) -> Group | None:
        with SessionMaker() as session:
            group_db = session.get(GroupDB, group_id)
            if group_db is None:
                return None
            return Group.from_db(group_db)
        
    @staticmethod
    def get_group_by_name(group_name: str) -> Group | None:
        with SessionMaker() as session:
            group_db = session.query(GroupDB).filter_by(group_name=group_name).first()
            if group_db is None:
                return None
            return Group.from_db(group_db)
        
    @staticmethod
    def delete_group_by_id(group_id: int) -> bool:
        with SessionMaker() as session:
            group_db = session.get(GroupDB, group_id)
            if group_db is None:
                return False
            session.delete(group_db)
            session.commit()
            return True
        
    @staticmethod
    def add_device_to_group(group_id: int, device_id: int) -> bool:
        with SessionMaker() as session:
            group_db = session.get(GroupDB, group_id)
            device_db = session.get(DeviceDB, device_id)
            if group_db is None or device_db is None:
                return False

            device_db.groups = device_db.groups or [] # type: ignore
            group_db.device_ids = group_db.device_ids or [] # type: ignore

            if group_id in device_db.groups or device_id in group_db.device_ids:
                return False

            device_db.groups.append(group_id)
            group_db.device_ids.append(device_id)

            session.commit()
            return True
        
    @staticmethod
    def remove_device_from_group(group_id: int, device_id: int) -> bool:
        with SessionMaker() as session:
            group_db = session.get(GroupDB, group_id)
            if group_db is None: return False
            if device_id not in group_db.device_ids: return False
            device_db = session.get(DeviceDB, device_id)
            if device_db is None: return False
            device_db.groups.remove(group_id)
            group_db.device_ids.remove(device_id)
            session.commit()
            return True
        
    @staticmethod
    def get_devices_in_group(group_id: int) -> Generator[Device, None, None]:
        with SessionMaker() as session:
            group_db = session.get(GroupDB, group_id)
            if group_db is None:
                return
            for device_id in group_db.device_ids:
                device_db = session.get(DeviceDB, device_id)
                if device_db is not None:
                    yield Device.from_db(device_db)

    @staticmethod
    def create_group(group_name: str, description: str = "") -> Group:
        with SessionMaker() as session:
            group_db = GroupDB(
                group_name=group_name,
                description=description,
                device_ids=[],
                handlers=[],
                created_at=func.now()
            )
            session.add(group_db)
            session.commit()
            session.refresh(group_db)
            group = Group.from_db(group_db)
            return group
        
    @staticmethod
    def update_group_description(group_id: int, new_description: str) -> bool:
        with SessionMaker() as session:
            group_db = session.get(GroupDB, group_id)
            if group_db is None:
                return False
            group_db.description = new_description # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def update_group_name(group_id: int, new_name: str) -> bool:
        with SessionMaker() as session:
            group_db = session.get(GroupDB, group_id)
            if group_db is None:
                return False
            group_db.group_name = new_name # type: ignore
            session.commit()
            return True
        
    @staticmethod
    def get_groups_handled_by_user(user_id: int) -> Generator[Group, None, None]:
        with SessionMaker() as session:
            group_dbs = session.query(GroupDB).filter(func.json_contains(GroupDB.handlers, f'[ {user_id} ]')).all()
            for group_db in group_dbs:
                yield Group.from_db(group_db)

    @staticmethod
    def add_handler_to_group(group_id: int, user_id: int) -> bool:
        with SessionMaker() as session:
            group_db = session.get(GroupDB, group_id)
            if group_db is None:
                return False
            if user_id in group_db.handlers:
                return False
            group_db.handlers.append(user_id)
            session.commit()
            return True
        
    @staticmethod
    def remove_handler_from_group(group_id: int, user_id: int) -> bool:
        with SessionMaker() as session:
            group_db = session.get(GroupDB, group_id)
            if group_db is None:
                return False
            if user_id not in group_db.handlers:
                return False
            group_db.handlers.remove(user_id)
            session.commit()
            return True
        
    @staticmethod
    def get_groups_for_device(device_id: int) -> Generator[Group, None, None]:
        with SessionMaker() as session:
            device_db = session.get(DeviceDB, device_id)
            if device_db is None:
                return
            for group_id in device_db.groups:
                group_db = session.get(GroupDB, group_id)
                if group_db is not None:
                    yield Group.from_db(group_db)

    @staticmethod
    def add_all_devices_to_group(group_id: int) -> bool:
        with SessionMaker() as session:
            group_db = session.get(GroupDB, group_id)
            if group_db is None:
                return False

            je = func.json_each(DeviceDB.groups).table_valued("value").alias("je")
            contains_group = exists(select(1).select_from(je).where(cast(je.c.value, Integer) == group_id))
            device_dbs = (session.query(DeviceDB).filter(~contains_group).all())

            for device_db in device_dbs:
                device_db.groups.append(group_id)
                group_db.device_ids.append(device_db.device_id)  # type: ignore
            session.commit()
            return True
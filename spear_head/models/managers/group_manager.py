from databases.engine import SessionMaker
from typing import Generator
from databases.db_types.groups.group_db import GroupDB
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
            group_db = session.query(GroupDB).filter_by(group_id=group_id).first()
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
            group_db = session.query(GroupDB).filter_by(group_id=group_id).first()
            if group_db is None:
                return False
            session.delete(group_db)
            session.commit()
            return True
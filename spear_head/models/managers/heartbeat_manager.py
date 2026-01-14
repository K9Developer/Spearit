from typing import Generator
from databases.db_types.devices.heartbeat_db import HeartbeatDB
from databases.engine import SessionMaker

from models.heartbeats.heartbeat import Heartbeat

class HeartbeatManager:
    # ------------------ Public Methods -----------------

    @staticmethod
    def get_all_heartbeats() -> Generator[Heartbeat, None, None]:
        with SessionMaker() as session:
            heartbeat_dbs = session.query(HeartbeatDB).all()
            for heartbeat_db in heartbeat_dbs:
                heartbeat = Heartbeat.from_db(heartbeat_db)
                yield heartbeat
    
    @staticmethod
    def get_heartbeat_by_id(heartbeat_id: int) -> Heartbeat | None:
        with SessionMaker() as session:
            heartbeat_db = session.query(HeartbeatDB).filter_by(heartbeat_id=heartbeat_id).first()
            if heartbeat_db is None:
                return None
            return Heartbeat.from_db(heartbeat_db)
        
    @staticmethod
    def get_heartbeats_for_device(device_id: int) -> Generator[Heartbeat, None, None]:
        with SessionMaker() as session:
            heartbeat_dbs = session.query(HeartbeatDB).filter_by(device_id=device_id).order_by(HeartbeatDB.timestamp.desc()).all()
            for heartbeat_db in heartbeat_dbs:
                heartbeat = Heartbeat.from_db(heartbeat_db)
                yield heartbeat
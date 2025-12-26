from datetime import datetime
from databases.engine import SessionMaker
from models.devices.device_manager import HeartbeatDeviceInformation
from databases.db_types.devices.heartbeat_db import HeartbeatDB
from models.heartbeats.heartbeat_types import HeartbeatNetworkDetails, HeartbeatSystemMetrics

class Heartbeat:
    def __init__(self, device_info: HeartbeatDeviceInformation, network_details: HeartbeatNetworkDetails, system_metrics: HeartbeatSystemMetrics, timestamp: datetime) -> None:
        self.device_info = device_info
        self.network_details = network_details
        self.system_metrics = system_metrics
        self.timestamp = timestamp

        self.heartbeat_id: int | None = None
        self.device_id: int | None = None

    def to_db(self, device_id: int) -> HeartbeatDB:
        return HeartbeatDB(
            device_id=device_id,
            timestamp=self.timestamp,
            contacted_devices=self.network_details.get_contacted_devices(),
            system_metrics={
                "cpu_usage": self.system_metrics.cpu_usage,
                "memory_usage": self.system_metrics.memory_usage
            }
        )
    
    def update_db(self, device_id: int):
        heartbeat_id = self.heartbeat_id
        heartbeat_db = self.to_db(device_id)
        with SessionMaker() as session:
            if heartbeat_id is None:
                session.add(heartbeat_db)
                session.commit()
                session.refresh(heartbeat_db)
                heartbeat_id = heartbeat_db.heartbeat_id
            else:
                heartbeat_db.heartbeat_id = heartbeat_id # type: ignore
                session.merge(heartbeat_db)
                session.commit()

        self.heartbeat_id = heartbeat_id  # type: ignore
        self.device_id = device_id
        
    

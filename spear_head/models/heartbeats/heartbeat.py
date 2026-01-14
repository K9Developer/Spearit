from datetime import datetime
from databases.engine import SessionMaker
from databases.db_types.devices.heartbeat_db import HeartbeatDB
from models.heartbeats.heartbeat_types import HeartbeatNetworkDetails, HeartbeatSystemMetrics
from utils.types import HeartbeatDeviceInformation

class Heartbeat:
    def __init__(self, device_info: HeartbeatDeviceInformation, network_details: HeartbeatNetworkDetails, system_metrics: HeartbeatSystemMetrics, timestamp: datetime) -> None:
        self.device_info = device_info
        self.network_details = network_details
        self.system_metrics = system_metrics
        self.timestamp = timestamp

        self.heartbeat_id: int | None = None
        self.device_id: int | None = None

    @staticmethod
    def from_db(heartbeat_db: HeartbeatDB) -> "Heartbeat":
        network_details = HeartbeatNetworkDetails(
            contacted_macs=heartbeat_db.contacted_devices or {} # type: ignore
        )

        sys_metrics = heartbeat_db.system_metrics or {}
        system_metrics = HeartbeatSystemMetrics(
            cpu_usage=sys_metrics.get("cpu_usage", 0.0),
            memory_usage=sys_metrics.get("memory_usage", 0.0)
        )

        hb = Heartbeat(
            device_info=HeartbeatDeviceInformation.default(),  # Placeholder; device info not stored in heartbeat DB
            network_details=network_details,
            system_metrics=system_metrics,
            timestamp=heartbeat_db.timestamp # type: ignore
        )
        hb.heartbeat_id = heartbeat_db.heartbeat_id # type: ignore
        hb.device_id = heartbeat_db.device_id # type: ignore
        return hb

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
        
    

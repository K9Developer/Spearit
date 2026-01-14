from datetime import datetime
from models.logger import Logger
from typing import Any

from utils.parser_utils import is_valid_mac
from models.managers.device_manager import DeviceManager, HeartbeatDeviceInformation
from models.heartbeats.heartbeat import Heartbeat
from models.heartbeats.heartbeat_types import HeartbeatNetworkDetails, HeartbeatSystemMetrics

class InternalHeartbeatManager:
    @staticmethod
    def _parse_raw_heartbeat(heartbeat_data: dict[Any, Any], timestamp: datetime) -> Heartbeat:
        device_info = HeartbeatDeviceInformation(
            device_name=heartbeat_data.get("device_name", "Unknown Device"),
            os_details=heartbeat_data.get("os_details", "Unknown OS"),
            ip_address=heartbeat_data.get("ip_address", "0.0.0.0"),
            mac_address=heartbeat_data["mac_address"]
        )

        raw_network_details = heartbeat_data.get("network_details", {})
        network_details = HeartbeatNetworkDetails(
            contacted_macs=raw_network_details.get("contacted_macs", {})
        )

        raw_sys_metrics = heartbeat_data.get("system_metrics", {})
        system_metrics = HeartbeatSystemMetrics(
            cpu_usage=raw_sys_metrics.get("cpu_usage_percent", 0.0),
            memory_usage=raw_sys_metrics.get("memory_usage_percent", 0.0)
        )

        return Heartbeat(
            device_info=device_info,
            network_details=network_details,
            system_metrics=system_metrics,
            timestamp=timestamp
        )

    @staticmethod
    def _submit_heartbeat(heartbeat_data: dict[Any, Any]) -> None:
        if "mac_address" not in heartbeat_data:
            Logger.warn("Heartbeat data missing 'mac_address' field; ignoring heartbeat.")
            return
        
        if heartbeat_data["mac_address"] == "00:00:00:00:00:00" or not is_valid_mac(heartbeat_data["mac_address"]):
            Logger.warn(f"Heartbeat data contains invalid MAC address ({heartbeat_data['mac_address']}); ignoring heartbeat.")
            return
        
        Logger.debug(f"Processing heartbeat from MAC: {heartbeat_data['mac_address']}")
        hb = InternalHeartbeatManager._parse_raw_heartbeat(heartbeat_data, datetime.now())

        device_id = DeviceManager._submit_device_info(hb.device_info)
        hb.update_db(device_id)

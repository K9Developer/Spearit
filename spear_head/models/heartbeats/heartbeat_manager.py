from typing import Any

from models.devices.device_manager import DeviceManager, HeartbeatDeviceInformation


class HeartbeatManager:
    
    @staticmethod
    def submit_heartbeat(heartbeat_data: dict[Any, Any]) -> None:
        device_info = HeartbeatDeviceInformation(
            device_name=heartbeat_data.get("device_name", "Unknown Device"),
            os_details=heartbeat_data.get("os_details", "Unknown OS"),
            ip_address=heartbeat_data.get("ip_address", "0.0.0.0"),
            mac_address=heartbeat_data.get("mac_address", "00:00:00:00:00:00")
        )

        DeviceManager.submit_device_info(device_info)
        # TODO: add heartbeat to db
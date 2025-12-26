from models.devices.device import Device
from databases.db_types.devices.device import get_or_create_device_db

class HeartbeatNetworkDetails:
    def __init__(self, contacted_macs: dict[str, int]) -> None:
        self.contacted_macs = contacted_macs

    def get_contacted_devices(self) -> dict[int, int]:
        """
        Convert MAC addresses to device IDs for contacted devices.
        """

        cd = {}
        for mac, count in self.contacted_macs.items():
            defd = Device.default()
            defd.mac_address = mac
            did = get_or_create_device_db(defd)[1]
            cd[did] = count
            
        return cd

class HeartbeatSystemMetrics:
    def __init__(self, cpu_usage: float, memory_usage: float) -> None:
        self.cpu_usage = cpu_usage
        self.memory_usage = memory_usage
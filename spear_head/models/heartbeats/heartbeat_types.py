class HeartbeatNetworkDetails:
    def __init__(self, contacted_macs: dict[str, int]) -> None:
        self.contacted_macs = contacted_macs

    def get_contacted_devices(self) -> dict[int, int]:
        """
        Convert MAC addresses to device IDs for contacted devices.
        """
        from models.managers.device_manager import DeviceManager # avoid circular import

        cd = {}
        for mac, count in self.contacted_macs.items():
            device = DeviceManager.get_device_by_mac(mac)
            if device is not None and device.device_id is not None:
                cd[device.device_id] = count
            
        return cd

class HeartbeatSystemMetrics:
    def __init__(self, cpu_usage: float, memory_usage: float) -> None:
        self.cpu_usage = cpu_usage
        self.memory_usage = memory_usage
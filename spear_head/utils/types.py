from dataclasses import dataclass


@dataclass
class ProtocolInfoEntry:
    libc_name: str
    name: str

class HeartbeatDeviceInformation:
    def __init__(self, device_name: str, os_details: str, ip_address: str, mac_address: str) -> None:
        self.device_name = device_name
        self.os_details = os_details
        self.ip_address = ip_address
        self.mac_address = mac_address
    
    @staticmethod
    def default() -> 'HeartbeatDeviceInformation':
        return HeartbeatDeviceInformation(
            device_name="",
            os_details="",
            ip_address="",
            mac_address=""
        )
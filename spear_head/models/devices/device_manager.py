from databases.engine import SessionMaker
from databases.db_types.devices.device_db import DeviceDB

class HeartbeatDeviceInformation:
    def __init__(self, device_name: str, os_details: str, ip_address: str, mac_address: str) -> None:
        self.device_name = device_name
        self.os_details = os_details
        self.ip_address = ip_address
        self.mac_address = mac_address

class DeviceManager:
    
    # TODO: This feels slow
    @staticmethod
    def submit_device_info(device_info: HeartbeatDeviceInformation) -> None:
        if device_info.mac_address == "00:00:00:00:00:00":
            print("Ignoring heartbeat with invalid MAC address")
            return
            
        with SessionMaker() as session:
            existing_device = session.query(DeviceDB).filter_by(mac_address=device_info.mac_address).first()
            if existing_device is None:
                new_device = DeviceDB(
                    device_name=device_info.device_name,
                    operating_system_details=device_info.os_details,
                    last_known_ip_address=device_info.ip_address,
                    mac_address=device_info.mac_address
                )
                session.add(new_device)
                session.commit()
                print(f"Added new device: {new_device}")
            else:
                existing_device.device_name = device_info.device_name # type: ignore
                existing_device.operating_system_details = device_info.os_details # type: ignore
                existing_device.last_known_ip_address = device_info.ip_address # type: ignore
                session.commit()
                print(f"Updated existing device: {existing_device}")
            
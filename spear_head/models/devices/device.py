from attr import dataclass

from databases.db_types.devices.device_db import DeviceDB


@dataclass(slots=True)
class Device:
    device_name: str
    os_details: str
    ip_address: str
    mac_address: str
    group: None # TODO
    last_heartbeat: None # TODO (heartbeat class)

    def __str__(self) -> str:
        group = self.group if self.group is not None else "ungrouped"
        heartbeat = (
            self.last_heartbeat
            if self.last_heartbeat is not None
            else "never"
        )

        return (
            f"Device("
            f"name={self.device_name}, "
            f"os={self.os_details}, "
            f"ip={self.ip_address}, "
            f"mac={self.mac_address}, "
            f"group={group}, "
            f"last_heartbeat={heartbeat}"
            f")"
        )
    
    def to_db(self) -> DeviceDB:
        """
        Convert this Device model instance to a DeviceDB instance.
        
        Returns:
            DeviceDB: The corresponding DeviceDB instance.
        """
        return DeviceDB(
            device_name=self.device_name,
            operating_system_details=self.os_details,
            last_known_ip_address=self.ip_address,
            mac_address=self.mac_address
        )

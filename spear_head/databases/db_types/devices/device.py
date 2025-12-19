import re
from databases.db_types.devices.device_db import DeviceDB
from databases.engine import SessionMaker
from models.devices.device import Device

_MAC_RE = re.compile(
    r"""
    ^
    (?:[0-9A-Fa-f]{2}([-:]))            # aa: or aa-
    (?:[0-9A-Fa-f]{2}\1){4}              # bb:cc:dd:ee:
    [0-9A-Fa-f]{2}                       # ff
    $
    |
    ^
    (?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}  # aabb.ccdd.eeff
    $
    """,
    re.VERBOSE,
)

def is_valid_mac(mac: str) -> bool:
    return bool(_MAC_RE.match(mac))

def get_or_create_device_db(device: Device) -> tuple[bool, int]:
    """
    Get or create a DeviceDB entry for the given Device.
    
    Args:
        device (Device): The device model instance.
    Returns:
        tuple[bool, int]: A tuple where the first element indicates if the device was created,
                               and the second element is the device_id of the DeviceDB entry.
    """

    device_mac = device.mac_address
    if not is_valid_mac(device_mac):
        raise Exception("Invalid device mac address!")
    
    with SessionMaker() as session:
        matching_device = session.query(DeviceDB).filter(DeviceDB.mac_address == device_mac).one_or_none()
        if matching_device is not None:
            return (False, int(matching_device.device_id))
        
        device_db = device.to_db()
        session.add(device_db)
        try:
            session.commit()
            session.refresh(device_db)
        except Exception as e:
            session.rollback()
            raise e

        return (True, int(device_db.device_id))
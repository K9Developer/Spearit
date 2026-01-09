from sqlalchemy import JSON, Column, Integer, String
from databases.base import Base

class DeviceDB(Base):
    __tablename__ = "devices"

    device_id = Column(Integer, primary_key=True)

    device_name = Column(String(32), nullable=True)
    operating_system_details = Column(String(32), nullable=True)
    last_known_ip_address = Column(String(38), nullable=True) # support ipv6 length (38)
    mac_address = Column(String(17), nullable=False, unique=True)

    handlers = Column(JSON, nullable=True) # list of user ids
    note = Column(String(250), nullable=True)
    
    # TODO: Group

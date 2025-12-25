from typing import Union
from models.events.types.event import BaseEvent
from models.events.types.packet_event import PacketEvent


EventType_ = Union[BaseEvent, PacketEvent] # TODO: update
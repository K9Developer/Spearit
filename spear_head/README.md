TODO: For packets, events, etc. use:
from dataclasses import dataclass

@dataclass(slots=True)
class Packet:
    src: str
    dst: str
    size: int

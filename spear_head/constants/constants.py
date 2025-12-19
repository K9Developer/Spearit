from models.events.types.packet_event import ProtocolInfoEntry


INT_FIELD_SIZE = 8 # 64 bit

SOCKET_FIELD_LENGTH_SIZE = 4
SOCKET_FULL_LENGTH_SIZE = 8

AES_BLOCK_SIZE = 128

SPEAR_HEAD_WRAPPER_PORT = 12345
SPEAR_HEAD_API_PORT = 12346

protocol_data: dict[int, ProtocolInfoEntry] = dict()

class MessageIDs:
    REPORT = "RPRT"
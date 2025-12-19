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

CAMPAIGN_MATCH_SCORE_THRESHOLD = 70
TCP_FLOW_TIMEOUT_NS = 2 * 60 * 1000 * 1000 * 1000  # 2 minutes in nanoseconds
# CAMPAIGN_ONGOING_TIMEOUT_NS = 30 * 60 * 1000 * 1000 * 1000  # 30 minutes in nanoseconds
CAMPAIGN_ONGOING_TIMEOUT_NS = 30 * 1000 * 1000 * 1000  # 30 seconds in nanoseconds
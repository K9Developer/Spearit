from typing import TYPE_CHECKING
if TYPE_CHECKING: 
    from models.events.types.packet_event import ProtocolInfoEntry

DEBUG = True

INT_FIELD_SIZE = 8 # 64 bit

SOCKET_FIELD_LENGTH_SIZE = 4
SOCKET_FULL_LENGTH_SIZE = 8

AES_BLOCK_SIZE = 128

SPEAR_HEAD_WRAPPER_PORT = 12345
SPEAR_HEAD_API_PORT = 12346
ENABLE_ENCRYPTION = True

protocol_data: dict[int, 'ProtocolInfoEntry'] = dict()

class MessageIDs:
    REPORT = "RPRT"
    HEARTBEAT = "HRTB"
    REQUEST_RULES = "RQRL"
    RULES_RESPONSE = "RSLR"

CAMPAIGN_MATCH_SCORE_THRESHOLD = 70
TCP_FLOW_TIMEOUT_NS = 2 * 60 * 1000 * 1000 * 1000  # 2 minutes in nanoseconds
# CAMPAIGN_ONGOING_TIMEOUT_NS = 30 * 60 * 1000 * 1000 * 1000  # 30 minutes in nanoseconds
CAMPAIGN_ONGOING_TIMEOUT = 10  # 10 seconds

AI_MODEL = 'llama3.1'
AI_TEMPERATURE = 0.5
AI_TOP_P = 0.9
AI_CONTEXT_SIZE = 16384
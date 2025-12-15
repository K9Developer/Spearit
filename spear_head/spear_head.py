import time
from attr import dataclass
from spear_head.constants import SPEAR_HEAD_API_PORT, SPEAR_HEAD_WRAPPER_PORT, MessageIDs
from spear_head.models.connection.connection import Connection
from spear_head.models.connection.fields import FieldType, Fields
from spear_head.models.connection.socket_server import SocketServer, SocketServerEvent
from spear_head.models.events.event_manager import EventManager

@dataclass
class SpearHeadConfig:
    wrapper_host: str = "0.0.0.0"
    wrapper_port: int = SPEAR_HEAD_WRAPPER_PORT
    api_port: int = SPEAR_HEAD_API_PORT

DEFAULT_CONFIG = SpearHeadConfig()

class SpearHead:

    event_manager: EventManager
    wrapper_server: SocketServer
    config: SpearHeadConfig

    def _on_wrapper_message(self, event: SocketServerEvent, connection: Connection, fields: Fields) -> None:
        if event != SocketServerEvent.MESSAGE_RECEIVED: return
        if len(fields.fields) == 0: return
        msg_id = fields.consume_field(FieldType.TEXT)
        if msg_id is None: return
        msg_id = msg_id.as_str()

        if msg_id == MessageIDs.PACKET_REPORT:
            print("Received Packet Report Message")

    def __init__(self, config: SpearHeadConfig = DEFAULT_CONFIG) -> None:
        self.config = config
        self.wrapper_server = SocketServer(self.config.wrapper_host, self.config.wrapper_port)
        self.wrapper_server.register_callback(SocketServerEvent.MESSAGE_RECEIVED, self._on_wrapper_message)
    
    def _tick(self) -> None:
        # self.event_manager.process_events()
        pass

    def start(self) -> None:
        self.wrapper_server.accept_clients()
        print(f"Spear Head Wrapper Server is running on {self.config.wrapper_host}:{self.config.wrapper_port}...")
        while True:
            self._tick()
            time.sleep(0.1)


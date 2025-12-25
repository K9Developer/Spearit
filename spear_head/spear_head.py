import json
import time
from dataclasses import dataclass
from constants.constants import SPEAR_HEAD_API_PORT, SPEAR_HEAD_WRAPPER_PORT, MessageIDs
from models.connection.connection import Connection
from models.connection.fields import FieldType, Fields
from models.connection.socket_server import SocketServer, SocketServerEvent
from models.events.event_manager import EventManager
from models.events.types.event import EventKind
from models.heartbeats.heartbeat_manager import HeartbeatManager

@dataclass
class SpearHeadConfig:
    wrapper_host: str = "0.0.0.0"
    wrapper_port: int = SPEAR_HEAD_WRAPPER_PORT
    api_port: int = SPEAR_HEAD_API_PORT

DEFAULT_CONFIG = SpearHeadConfig()

class SpearHead:

    wrapper_server: SocketServer
    config: SpearHeadConfig

    def __init__(self, config: SpearHeadConfig = DEFAULT_CONFIG) -> None:
        self.config = config
        self.wrapper_server = SocketServer(self.config.wrapper_host, self.config.wrapper_port)
        self.wrapper_server.register_callback(SocketServerEvent.MESSAGE_RECEIVED, self._on_wrapper_message)

        self.wrapper_server.register_callback(None, lambda event, conn, fields: print(f"Wrapper Server Event: {event}, From: {conn.addr}"))

    def _on_wrapper_message(self, event: SocketServerEvent, _: Connection, fields: Fields) -> None:
        if event != SocketServerEvent.MESSAGE_RECEIVED: return
        if len(fields.fields) == 0: return
        msg_id = fields.consume_field(FieldType.TEXT)
        if msg_id is None: return
        msg_id = msg_id.as_str()

        if msg_id == MessageIDs.REPORT:
            json_event_raw = fields.consume_field(FieldType.TEXT)
            if json_event_raw == None:
                raise TypeError("Invalid field type in packet report (json)")
            json_event = json.loads(json_event_raw.as_str())
            event_data = json_event.get("data")
            event_type = json_event.get("type")
            if event_data is None or event_type is None:
                print("Invalid event")
                return
            EventManager.submit_event(event_data, EventKind.from_str(event_type))
        elif msg_id == MessageIDs.HEARTBEAT:
            json_heartbeat = fields.consume_field(FieldType.TEXT)
            if json_heartbeat is None: raise TypeError("Invalid field type in heartbeat (json)")
            try:
                heartbeat_data = json.loads(json_heartbeat.as_str())
                print(f"Received Heartbeat: {heartbeat_data}")
                HeartbeatManager.submit_heartbeat(heartbeat_data)
            except json.JSONDecodeError:
                print("Invalid heartbeat JSON data")
    
    def _tick(self) -> None:
        EventManager.process_event()

    def start(self) -> None:
        self.wrapper_server.accept_clients()
        print(f"Spear Head Wrapper Server is running on {self.config.wrapper_host}:{self.config.wrapper_port}...")
        while True:
            self._tick()
            time.sleep(0.1)


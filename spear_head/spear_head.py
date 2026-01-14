import json
import time
from dataclasses import dataclass
from constants.constants import SPEAR_HEAD_API_PORT, SPEAR_HEAD_WRAPPER_PORT, MessageIDs
from models.connection.connection import Connection
from models.connection.fields import Field, FieldType, Fields
from models.connection.socket_server import SocketServer, SocketServerEvent
from models.managers.callback_manager import CallbackEvent, CallbackManager
from models.managers.device_manager import DeviceManager
from models.managers.event_manager import EventManager
from models.events.types.event import EventKind
from models.managers.group_manager import GroupManager
from models.logger import Logger
from models.managers.internal_event_manager import InternalEventManager
from models.managers.internal_heartbeat_manager import InternalHeartbeatManager
from models.managers.rule_manager import RuleManager

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

        # setup All group
        group = GroupManager.create_group("All", "System created group containing all devices")
        GroupManager.add_all_devices_to_group(group.group_id) # type: ignore
        CallbackManager.register_callback(CallbackEvent.NEW_DEVICE, lambda device: GroupManager.add_device_to_group(group.group_id, device.device_id)) # type: ignore 

    def _on_wrapper_message(self, event: SocketServerEvent, conn: Connection, fields: Fields) -> None:
        if event != SocketServerEvent.MESSAGE_RECEIVED: return
        if len(fields.fields) == 0: return
        device_mac = fields.consume_field(FieldType.TEXT)
        if device_mac is None:
            Logger.warn("Invalid field type in message (device_mac)")
            return
        device_mac = device_mac.as_str()
        msg_id = fields.consume_field(FieldType.TEXT)
        if msg_id is None: return
        msg_id = msg_id.as_str()
        Logger.debug(f"Received message ID: {msg_id} from device MAC: {device_mac}")

        if msg_id == MessageIDs.REPORT:
            json_event_raw = fields.consume_field(FieldType.TEXT)
            if json_event_raw == None:
                Logger.warn("Invalid field type in report (json)")
                return
            
            try:
                json_event = json.loads(json_event_raw.as_str())
            except json.JSONDecodeError:
                Logger.warn("Failed to decode JSON event")
                return
            
            event_data = json_event.get("data")
            event_type = json_event.get("type")
            if event_data is None or event_type is None:
                Logger.warn("Received invalid event data")
                return
            
            InternalEventManager._submit_event(event_data, EventKind.from_str(event_type))
        elif msg_id == MessageIDs.HEARTBEAT:
            json_heartbeat = fields.consume_field(FieldType.TEXT)
            if json_heartbeat is None:
                Logger.warn("Invalid field type in heartbeat (json)")
                return
            try:
                heartbeat_data = json.loads(json_heartbeat.as_str())
                InternalHeartbeatManager._submit_heartbeat(heartbeat_data)
            except json.JSONDecodeError:
                Logger.warn("Failed to decode JSON heartbeat")
                return
        elif msg_id == MessageIDs.REQUEST_RULES:
            device = DeviceManager.get_device_by_mac(device_mac)
            if device is None:
                Logger.warn(f"Received rules request for unknown device with MAC {device_mac}")
                return
            valid_rules = RuleManager.get_rules_matching_device(device)
            raw_rules = json.dumps([rule.to_compact_json() for rule in valid_rules])
            response_fields = Fields([
                Field(FieldType.TEXT, MessageIDs.RULES_RESPONSE),
                Field(FieldType.TEXT, raw_rules)
            ])
            conn.send_fields(response_fields)
    
    def _tick(self) -> None:
        InternalEventManager._process_event()

    def start(self) -> None:
        self.wrapper_server.accept_clients()
        Logger.info(f"Spear Head Wrapper Server is running on {self.config.wrapper_host}:{self.config.wrapper_port}...")
        while True:
            self._tick()
            time.sleep(0.1)


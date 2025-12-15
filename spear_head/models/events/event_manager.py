import base64
from queue import Empty, Queue

from spear_head.models.events.types.event import BaseEvent, EventType
from spear_head.models.events.types.packet_event import PacketDeviceInfo, PacketEvent, PacketPayload, ProcessInfo
from spear_head.utils.parser import ProtocolInfoEntry, protocol_entry_from_id


class EventManager:

    event_queue: Queue[BaseEvent] = Queue()

    @staticmethod
    def _submit_packet_event(json_event: dict):
        packet_event = PacketEvent(
            event_type = EventType.PACKET,

            timestamp=json_event["timestamp_ns"],
            violated_rule_id=json_event["violated_rule_id"],
            violation_type=json_event["violation_type"],
            violation_response=json_event["violation_response"],
            protocol=protocol_entry_from_id(json_event["protocol"]),
            is_connection_establishing=json_event["is_connection_establishing"],
            direction=json_event["direction"],

            process=ProcessInfo(
                process_id=json_event["process"]["pid"],
                name=json_event["process"]["name"]
            ),

            source=PacketDeviceInfo(
                ip=json_event["ip"]["src_ip"],
                port=json_event["ip"]["src_port"],
                mac=json_event["src_mac"]
            ),

            dest=PacketDeviceInfo(
                ip=json_event["ip"]["dst_ip"],
                port=json_event["ip"]["dst_port"],
                mac=json_event["dst_mac"]
            ),

            payload=PacketPayload(
                full_size=json_event["payload"]["full_size"],
                data=bytearray(base64.b64decode(json_event["payload"]["data"]))
            )
        )
        EventManager.event_queue.put(packet_event)

    @staticmethod
    def process_event():
        try:
            curr_event = EventManager.event_queue.get(block = False)
        except Empty:
            return
        
        print(f"Processing: {curr_event}")


    @staticmethod
    def submit_event(json_event: dict, type_: EventType) -> bool:
        try:
            if type_ == EventType.PACKET:
                EventManager._submit_packet_event(json_event)
            else:
                raise Exception("Unknown event type")
            
            return True
        except Exception as _:
            return False
# pyright: reportArgumentType=false
import base64
from queue import Empty, Queue

from models.managers.device_manager import DeviceManager
from models.managers.campaign_manager import CampaignManager
from models.events.types.event import EventKind, ViolationResponse
from models.events.types.packet_event import PacketDeviceInfo, PacketDirection, PacketEvent, PacketPayload, ProcessInfo
from models.events.types.event_type import EventType_
from utils.parser import protocol_entry_from_id


class EventManager:

    event_queue: Queue[EventType_] = Queue()

    @staticmethod
    def _submit_packet_event(json_event: dict[str, str | dict[str, str]]):
        packet_event = PacketEvent(
            timestamp_ns=json_event["timestamp_ns"], 
            violated_rule_id=json_event["violated_rule_id"],
            violation_type=json_event["violation_type"],
            violation_response=ViolationResponse.from_str(json_event["violation_response"]),
            protocol=protocol_entry_from_id(json_event["protocol"]),
            is_connection_establishing=json_event["is_connection_establishing"],
            direction=PacketDirection.from_str(json_event["direction"]),

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
        DeviceManager.update_device_from_packet_event(packet_event)

    @staticmethod
    def process_event():
        try:
            curr_event = EventManager.event_queue.get(block = False)
            curr_event.update_db()
            CampaignManager.process_event(curr_event)

        except Empty:
            return
        
    @staticmethod
    def submit_event(json_event: dict[str, str | dict[str, str]], type_: EventKind) -> bool:
        # try:
            if type_ == EventKind.PACKET:
                EventManager._submit_packet_event(json_event)
            else:
                raise Exception("Unknown event type")
            
            return True
        # except Exception as e:
        #     Logger.error(f"Failed to submit event: {e}")
        #     return False
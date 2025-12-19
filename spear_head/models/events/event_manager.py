# pyright: reportArgumentType=false
import base64
from queue import Empty, Queue

from av import Packet
from databases.engine import SessionMaker
from models.events.types.event import BaseEvent, EventType, ViolationResponse
from models.events.types.packet_event import PacketDeviceInfo, PacketDirection, PacketEvent, PacketPayload, ProcessInfo
from utils.parser import protocol_entry_from_id


class EventManager:

    event_queue: Queue[PacketEvent] = Queue() # TODO: Expand with more events

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

    @staticmethod
    def process_event():
        try:
            curr_event = EventManager.event_queue.get(block = False)
            db_event = curr_event.to_db()
            print(f"Storing event to DB: {db_event}")
            with SessionMaker() as session:
                session.add(db_event)
                session.commit()

        except Empty:
            return
        
        print(f"Processing: {curr_event}")


    @staticmethod
    def submit_event(json_event: dict[str, str | dict[str, str]], type_: EventType) -> bool:
        # try:
            if type_ == EventType.PACKET:
                EventManager._submit_packet_event(json_event)
            else:
                raise Exception("Unknown event type")
            
            return True
        # except Exception as e:
        #     print(f"Failed to submit event: {e}")
        #     return False
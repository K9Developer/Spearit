from math import exp
from constants.constants import TCP_FLOW_TIMEOUT_NS
from models.events.types.event_type import EventType_
from models.events.types.packet_event import PacketEvent
from models.events.types.campaign import Campaign

def same_conversation_score(p1: PacketEvent, p2: PacketEvent) -> float:
    score = 0.0

    if p1.protocol == p2.protocol: score += 0.25
    else: return 0.0

    forward = (
        p1.source.ip == p2.source.ip and
        p1.source.port == p2.source.port and
        p1.dest.ip == p2.dest.ip and
        p1.dest.port == p2.dest.port
    )

    reverse = (
        p1.source.ip == p2.dest.ip and
        p1.source.port == p2.dest.port and
        p1.dest.ip == p2.source.ip and
        p1.dest.port == p2.source.port
    )

    if forward or reverse: score += 0.45
    else: return score

    dt = abs(p1.timestamp_ns - p2.timestamp_ns)
    if dt >= TCP_FLOW_TIMEOUT_NS: return score * 0.5

    time_score = exp(-dt / TCP_FLOW_TIMEOUT_NS)
    score += 0.30 * time_score
    return min(score, 1.0)

def fix_event_process(campaign: Campaign, event: EventType_) -> list[PacketEvent]:
    return [] # TODO
    # if not isinstance(event, PacketEvent): # TODO: need for others too?
    #     return []
    
    # chosen_event_name = ""

    # events_to_rename: list[PacketEvent] = []
    # for event_idx in range(len(campaign.events)-1, -1, -1):
    #     camp_event = campaign.events[event_idx]
    #     if not isinstance(camp_event, PacketEvent):
    #         continue
        
    #     score = same_conversation_score(event, camp_event)
    #     if score < 0.7: continue
    #     if camp_event.process.name != "N/A" and camp_event.process.name != "loader":
    #         chosen_event_name = camp_event.process.name
        
    #     if camp_event.process.name != chosen_event_name and chosen_event_name != "":
    #         events_to_rename.append(camp_event)
        
    
    # for ev in events_to_rename:
    #     ev.process.name = chosen_event_name

    # return events_to_rename
        
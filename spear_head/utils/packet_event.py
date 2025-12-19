from math import exp
from constants.constants import TCP_FLOW_TIMEOUT_NS
from models.events.types.packet_event import PacketEvent


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
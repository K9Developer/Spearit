from pathlib import Path
import json

from spear_head.models.events.types.packet_event import ProtocolInfoEntry
from spear_head.constants.constants import PROTOCOL_DATA

def parse_protocol_entries_file(file: Path) -> dict[int, 'ProtocolInfoEntry']:
    if not file.exists(): raise FileNotFoundError()
    raw = file.read_text()
    data = json.loads(raw)
    entries = {}
    for (str_id, entry) in data.items():
        entries[int(str_id)] = ProtocolInfoEntry(libc_name=entry["libc"], name=entry["name"])
    return entries


def protocol_entry_from_id(id_: int) -> 'ProtocolInfoEntry':
    global PROTOCOL_DATA
    
    if len(PROTOCOL_DATA) == 0:
        PROTOCOL_DATA = parse_protocol_entries_file(Path(r"spear_head\constants\protocol_numbers.json"))
    return PROTOCOL_DATA.get(id_, ProtocolInfoEntry("N/A", "N/A"))
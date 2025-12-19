from pathlib import Path
import json
from models.events.types.packet_event import ProtocolInfoEntry
from constants.constants import protocol_data

def parse_protocol_entries_file(file: Path) -> dict[int, 'ProtocolInfoEntry']:
    if not file.exists(): raise FileNotFoundError()
    raw = file.read_text()
    data = json.loads(raw)
    entries = {}
    for (str_id, entry) in data.items():
        entries[int(str_id)] = ProtocolInfoEntry(libc_name=entry["libc"], name=entry["name"])
    return entries


def protocol_entry_from_id(id_: int) -> 'ProtocolInfoEntry':
    global protocol_data
    
    if len(protocol_data) == 0:
        protocol_data = parse_protocol_entries_file(Path(r"constants\protocol_numbers.json"))
    return protocol_data.get(id_, ProtocolInfoEntry("N/A", "N/A"))
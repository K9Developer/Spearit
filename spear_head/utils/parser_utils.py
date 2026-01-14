from pathlib import Path
import json
from utils.types import ProtocolInfoEntry
from constants.constants import protocol_data
import re

def parse_protocol_entries_file(file: Path) -> dict[int, ProtocolInfoEntry]:
    if not file.exists(): raise FileNotFoundError()
    raw = file.read_text()
    data = json.loads(raw)
    entries = {}
    for (str_id, entry) in data.items():
        entries[int(str_id)] = ProtocolInfoEntry(libc_name=entry["libc"], name=entry["name"])
    return entries


def protocol_entry_from_id(id_: int) -> ProtocolInfoEntry:
    global protocol_data
    
    if len(protocol_data) == 0:
        protocol_data = parse_protocol_entries_file(Path("constants", "protocol_numbers.json"))
    return protocol_data.get(id_, ProtocolInfoEntry("N/A", "N/A"))

_MAC_RE = re.compile(
    r"""
    ^
    (?:[0-9A-Fa-f]{2}([-:]))            # aa: or aa-
    (?:[0-9A-Fa-f]{2}\1){4}              # bb:cc:dd:ee:
    [0-9A-Fa-f]{2}                       # ff
    $
    |
    ^
    (?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}  # aabb.ccdd.eeff
    $
    """,
    re.VERBOSE,
)

def is_valid_mac(mac: str) -> bool:
    return bool(_MAC_RE.match(mac))

from dataclasses import dataclass

class PermissionType:
    pass # TODO: add perms

@dataclass
class Permission: # TODO
    type_: PermissionType
    affected_groups: list[int]
    affected_devices: list[int]
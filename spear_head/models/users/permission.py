from enum import Enum
from dataclasses import dataclass

class UserAction(Enum):
    ROOT = "root"
    CONTROL_USERS = "control_users"
    CONTROL_GROUPS = "control_groups"
    CONTROL_DEVICES = "control_devices"
    CONTROL_RULES = "control_rules"

class ActionTargetType(Enum):
    NONE = -1
    DEVICE = 0
    GROUP = 1

@dataclass
class Permission:
    type_: UserAction
    affected_groups: list[int]
    affected_devices: list[int]

    @staticmethod
    def root() -> 'Permission':
        return Permission(
            type_=UserAction.ROOT,
            affected_groups=[],
            affected_devices=[],
        )
    
    def to_json(self) -> dict:
        return {
            "type": self.type_.value,
            "affected_groups": self.affected_groups,
            "affected_devices": self.affected_devices,
        }

@dataclass
class ActionTarget:
    target_type: ActionTargetType
    target_id: int

    @staticmethod
    def none() -> 'ActionTarget':
        return ActionTarget(ActionTargetType.NONE, -1)
    
    @staticmethod
    def device(device_id: int) -> 'ActionTarget':
        return ActionTarget(ActionTargetType.DEVICE, device_id)
    
    @staticmethod
    def group(group_id: int) -> 'ActionTarget':
        return ActionTarget(ActionTargetType.GROUP, group_id)
    
def get_description_permissions() -> dict[str, str]:
    return {
        UserAction.ROOT.value: "Full access to all actions and targets.",
        UserAction.CONTROL_USERS.value: "Permission to create, edit, and delete users.",
        UserAction.CONTROL_GROUPS.value: "Permission to create, edit, and delete groups.",
        UserAction.CONTROL_DEVICES.value: "Permission to control devices and groups.",
        UserAction.CONTROL_RULES.value: "Permission to create, edit, and delete rules.",
    }
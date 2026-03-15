from enum import Enum
from dataclasses import dataclass

class UserAction(Enum):
    ROOT = -1
    CREATE_USER = 0
    DELETE_USER = 1

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
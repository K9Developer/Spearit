from enum import Enum



class CallbackEvent(Enum):
    NEW_DEVICE = "new_device",

class CallbackManager:
    callbacks: dict[CallbackEvent, list[callable]] = { event: [] for event in CallbackEvent } # type: ignore

    @staticmethod
    def register_callback(event: CallbackEvent, callback: callable) -> None: # type: ignore
        if event not in CallbackManager.callbacks: # type: ignore
            CallbackManager.callbacks[event] = [] # type: ignore
        CallbackManager.callbacks[event].append(callback) # type: ignore

    @staticmethod
    def trigger_event(event: CallbackEvent, *args, **kwargs) -> None: # type: ignore
        if event in CallbackManager.callbacks: # type: ignore 
            for callback in CallbackManager.callbacks[event]: # type: ignore
                callback(*args, **kwargs)
from constants.constants import DEBUG

class Logger:

    DEBUG_PREFIX = "\x1b[90m[-]"
    INFO_PREFIX  = "\x1b[36m[*]\x1b[97m"
    WARN_PREFIX  = "\x1b[33m[!]"
    ERROR_PREFIX = "\x1b[41;97m[ERROR]"
    RESET = "\x1b[0m"

    @staticmethod
    def debug(message: str) -> None:
        if not DEBUG: return
        print(f"{Logger.DEBUG_PREFIX} {message}{Logger.RESET}")

    @staticmethod
    def info(message: str) -> None:
        print(f"{Logger.INFO_PREFIX} {message}{Logger.RESET}")
    @staticmethod
    def warn(message: str) -> None:
        print(f"{Logger.WARN_PREFIX} {message}{Logger.RESET}")

    @staticmethod
    def error(message: str) -> None:
        print(f"{Logger.ERROR_PREFIX} {message}{Logger.RESET}")
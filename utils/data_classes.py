from enum import Enum


class MessageType(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class SellProcessType(Enum):
    SINGLE = "single"
    ALL = "all"

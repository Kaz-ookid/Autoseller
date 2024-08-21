from enum import Enum


class MessageType(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class SellProcessType(Enum):
    SINGLE = "single"
    ALL = "all"


class Coordinates:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.size = (w, h)

    def __str__(self):
        return f"PreviousLocation(x={self.x}, y={self.y}, size={self.size})"



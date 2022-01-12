from enum import Enum
from typing import Union


class PogoDataEnum(Enum):
    @classmethod
    def get(cls, value: Union[str, int]):
        enum_list = list(cls)
        if isinstance(value, str) and value.upper() in [e.name for e in enum_list]:
            return cls[value.upper()]
        elif isinstance(value, int) and value in [e.value for e in enum_list]:
            return cls(value)
        else:
            return enum_list[0]

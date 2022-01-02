from typing import List


# proto, id, boosts
WEATHERS = [
    ("NONE", 0, [1, 2])
]


class Weather:
    id: int
    proto: str
    boosts: List[int]

    def __init__(self, id_, proto, boosts):
        self.id = id_
        self.proto = proto
        self.boosts = boosts

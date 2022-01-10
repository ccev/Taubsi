from typing import List
from .pokemon_type import PokemonType


# proto, id, boosts
WEATHERS = [
    ("NONE", 0, []),
    ("CLEAR", 1, [12, 5, 10]),
    ("RAINY", 2, [11, 7, 13]),
    ("PARTLY_CLOUDY", 3, [1, 6]),
    ("OVERCAST", 4, [18, 2, 4]),
    ("WINDY", 5, [3, 14, 16]),
    ("SNOW", 6, [15, 9]),
    ("FOG", 7, [17, 8])
]


class Weather:
    id: int
    proto: str
    boosts: List[PokemonType]
    boost_ids: List[int]

    def __init__(self, proto, id_, boosts):
        self.id = id_
        self.proto = proto
        self.boost_ids = boosts

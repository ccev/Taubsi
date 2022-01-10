from __future__ import annotations
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .weather import Weather


# proto, id, weak_to
TYPES = [
    ("POKEMON_TYPE_NONE", 0, []),
    ("POKEMON_TYPE_NORMAL", 1, [2]),
    ("POKEMON_TYPE_FIGHTING", 2, [3, 14, 18]),
    ("POKEMON_TYPE_FLYING", 3, [13, 6, 15]),
    ("POKEMON_TYPE_POISON", 4, [5, 14]),
    ("POKEMON_TYPE_GROUND", 5, [11, 12, 15]),
    ("POKEMON_TYPE_ROCK", 6, [9, 11, 12, 2, 5]),
    ("POKEMON_TYPE_BUG", 7, [10, 3, 6]),
    ("POKEMON_TYPE_GHOST", 8, [17]),
    ("POKEMON_TYPE_STEEL", 9, [5, 2, 10]),
    ("POKEMON_TYPE_FIRE", 10, [11, 5, 6]),
    ("POKEMON_TYPE_WATER", 11, [12, 13]),
    ("POKEMON_TYPE_GRASS", 12, [10, 15, 4, 3, 7]),
    ("POKEMON_TYPE_ELECTRIC", 13, [5]),
    ("POKEMON_TYPE_PSYCHIC", 14, [7, 8, 17]),
    ("POKEMON_TYPE_ICE", 15, [10, 2, 6, 9]),
    ("POKEMON_TYPE_DRAGON", 16, [16, 15, 10]),
    ("POKEMON_TYPE_DARK", 17, [2, 7, 18]),
    ("POKEMON_TYPE_FAIRY", 18, [4, 9])
]


class PokemonType:
    proto: str
    id: int
    boosted_by: Weather
    weak_to: List[PokemonType]
    weak_to_ids: List[int]

    def __init__(self, proto: str, id_: int, weak_to: List[int]):
        self.id = id_
        self.proto = proto
        self.weak_to_ids = weak_to

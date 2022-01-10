from __future__ import annotations
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .weather import Weather


# proto, id, weak_to
TYPES = [
    ("POKEMON_TYPE_NONE", 0, [], []),
    ("POKEMON_TYPE_NORMAL", 1, [2], [8]),
    ("POKEMON_TYPE_FIGHTING", 2, [3, 14, 18], [7, 6, 17]),
    ("POKEMON_TYPE_FLYING", 3, [13, 6, 15], [12, 5, 7, 2]),
    ("POKEMON_TYPE_POISON", 4, [5, 14], [12, 2, 4, 7, 18]),
    ("POKEMON_TYPE_GROUND", 5, [11, 12, 15], [13, 4, 6]),
    ("POKEMON_TYPE_ROCK", 6, [9, 11, 12, 2, 5], [1, 10, 4, 3]),
    ("POKEMON_TYPE_BUG", 7, [10, 3, 6], [12, 2, 5]),
    ("POKEMON_TYPE_GHOST", 8, [17], [1, 2, 4, 7]),
    ("POKEMON_TYPE_STEEL", 9, [5, 2, 10], [1, 12, 15, 4, 3, 14, 7, 6, 16, 9, 18]),
    ("POKEMON_TYPE_FIRE", 10, [11, 5, 6], [10, 12, 15, 7, 9, 18]),
    ("POKEMON_TYPE_WATER", 11, [12, 13], [10, 11, 15, 9]),
    ("POKEMON_TYPE_GRASS", 12, [10, 15, 4, 3, 7], [11, 12, 13, 5]),
    ("POKEMON_TYPE_ELECTRIC", 13, [5], [13, 3, 9]),
    ("POKEMON_TYPE_PSYCHIC", 14, [7, 8, 17], [2, 14]),
    ("POKEMON_TYPE_ICE", 15, [10, 2, 6, 9], [15]),
    ("POKEMON_TYPE_DRAGON", 16, [16, 15, 10], [10, 11, 12, 13]),
    ("POKEMON_TYPE_DARK", 17, [2, 7, 18], [14, 8, 17]),
    ("POKEMON_TYPE_FAIRY", 18, [4, 9], [2, 7, 16, 17])
]


class PokemonType:
    proto: str
    id: int
    boosted_by: Weather
    weak_to: List[PokemonType]
    weak_to_ids: List[int]
    resists_ids: List[int]

    def __init__(self, proto: str, id_: int, weak_to: List[int], resists: List[int]):
        self.id = id_
        self.proto = proto
        self.weak_to_ids = weak_to
        self.resists_ids = resists

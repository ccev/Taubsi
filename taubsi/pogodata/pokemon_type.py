from typing import List


# proto, id, weak_to
TYPES = [
    ("POKEMON_TYPE_NONE", 0, []),
    ("POKEMON_TYPE_NORMAL", 1, [6, 9]),
    ("POKEMON_TYPE_FIGHTING", 2, [4, 3, 14, 7, 18]),
    ("POKEMON_TYPE_FLYING", 3, [13, 6, 9]),
    ("POKEMON_TYPE_POISON", 4, [4, 5, 6, 8]),
    ("POKEMON_TYPE_GROUND", 5, [12, 7]),
    ("POKEMON_TYPE_ROCK", 6, [2, 5, 9]),
    ("POKEMON_TYPE_BUG", 7, [10, 2, 4, 8, 9, 18]),
    ("POKEMON_TYPE_GHOST", 8, [17]),
    ("POKEMON_TYPE_STEEL", 9, [10, 11, 13, 9]),
    ("POKEMON_TYPE_FIRE", 10, [10, 11, 6, 16]),
    ("POKEMON_TYPE_WATER", 11, [11, 12, 16]),
    ("POKEMON_TYPE_GRASS", 12, [10, 12, 4, 3, 3, 7, 9, 18]),
    ("POKEMON_TYPE_ELECTRIC", 13, [12, 13, 16]),
    ("POKEMON_TYPE_PSYCHIC", 14, [9, 14]),
    ("POKEMON_TYPE_ICE", 15, [9, 10, 11, 15]),
    ("POKEMON_TYPE_DRAGON", 16, [9]),
    ("POKEMON_TYPE_DARK", 17, [2, 17, 18]),
    ("POKEMON_TYPE_FAIRY", 18, [11, 4, 9])
]


class PokemonType:
    proto: str
    id: int
    weak_to: List[int]

    def __init__(self, proto: str, id_: int, weak_to: List[int]):
        self.id = id_
        self.proto = proto
        self.weak_to = weak_to

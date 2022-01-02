from enum import Enum
from typing import List


# typeid: #(effective_against, weak_against, resists, resisted_by)
EFFECTIVENESSES = {
    0: (
        [], [], [], []
    ),
    1: (
        [], [6, 9], [8], [8]
    ),
    2: (
        [1, 15, 6, 17, 9], [4, 3, 14, 7, 18], [], []
    ),
    3: (
        [12, 2, 7], [13, 6, 9], [5], []
    ),
    4: (
        [12, 18], [4, 5, 6, 8], [], [9]
    ),
    5: (
        [10, 13, 4, 6, 9], [12, 7], [13], [3]
    ),
    6: (
        [10, 15, 3, 7], [2, 5, 9], [], []
    ),
    7: (
        [12, 14, 17], [10, 2, 4, 8, 9, 18], [], [17]
    ),
    8: (
        [8, 14], [17], [1, 2], [1]
    ),
    9: (
        [15, 6, 18], [10, 11, 13, 9], [4], []
    ),
    10: (
        [12, 15, 7, 9], [10, 11, 6, 16], [], []
    ),
    11: (
        [10, 5, 6], [11, 12, 16], [], []
    ),
    12: (
        [11, 5, 6], [10, 12, 4, 3, 3, 7, 9, 18], [], []
    ),
    13: (
        [11, 3], [12, 13, 16], [], [5]
    ),
    14: (
        [2, 4], [9, 14], [], []
    ),
    15: (
        [12, 5, 3, 16], [9, 10, 11, 15], [], []
    ),
    16: (
        [16], [9], [], [18]
    ),
    17: (
        [8, 14], [2, 17, 18], [7], []
    ),
    18: (
        [2, 16, 17], [11, 4, 9], [16], []
    )
}


class TypeProto(Enum):
    POKEMON_TYPE_NONE = 0
    POKEMON_TYPE_NORMAL = 1
    POKEMON_TYPE_FIGHTING = 2
    POKEMON_TYPE_FLYING = 3
    POKEMON_TYPE_POISON = 4
    POKEMON_TYPE_GROUND = 5
    POKEMON_TYPE_ROCK = 6
    POKEMON_TYPE_BUG = 7
    POKEMON_TYPE_GHOST = 8
    POKEMON_TYPE_STEEL = 9
    POKEMON_TYPE_FIRE = 10
    POKEMON_TYPE_WATER = 11
    POKEMON_TYPE_GRASS = 12
    POKEMON_TYPE_ELECTRIC = 13
    POKEMON_TYPE_PSYCHIC = 14
    POKEMON_TYPE_ICE = 15
    POKEMON_TYPE_DRAGON = 16
    POKEMON_TYPE_DARK = 17
    POKEMON_TYPE_FAIRY = 18


class PokemonType:
    proto: TypeProto
    weak_to: List[int]

    def __init__(self, proto: TypeProto, weak_to: List[int]):
        self.proto = proto
        self.weak_to = weak_to

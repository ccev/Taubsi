from __future__ import annotations
from pydantic import BaseModel, validator
from typing import List, Optional, TYPE_CHECKING
from .pokemon import BaseStats

if TYPE_CHECKING:
    from . import PogoData, PokemonType, Move


class PokemonStats(BaseModel):
    baseStamina: int
    baseAttack: int
    baseDefense: int


class _BasePokemonSettings(BaseModel):
    @property
    def base_stats(self):
        return BaseStats.from_gamemaster(self.stats)

    def get_types(self, pogodata: PogoData) -> List[PokemonType]:
        types = []
        for type_ in [self.type, self.type2]:
            if type_:
                types.append(pogodata.get_type(type_))
        return types


class TempEvoOverrides(_BasePokemonSettings):
    tempEvoId: str
    stats: PokemonStats
    typeOverride1: str
    typeOverride2: Optional[str]

    @property
    def type(self):
        return self.typeOverride1

    @property
    def type2(self):
        return self.typeOverride2


class PokemonSettings(_BasePokemonSettings):
    pokemonId: str
    form: Optional[str]
    type: str
    type2: Optional[str]
    stats: PokemonStats
    quickMoves: Optional[List[str]]
    cinematicMoves: Optional[List[str]]
    eliteCinematicMove: Optional[List[str]]
    eliteQuickMove: Optional[List[str]]
    tempEvoOverrides: Optional[List[TempEvoOverrides]]

    @staticmethod
    def _get_base_moves(pogodata: PogoData, *moves: List[str]):
        final_moves = []
        for moves_lists in moves:
            if moves_lists:
                final_moves += moves_lists

        return [pogodata.get_move(m) for m in final_moves]

    def get_moves(self, pogodata: PogoData) -> List[Move]:
        return self._get_base_moves(pogodata, self.quickMoves, self.cinematicMoves)

    def get_elite_moves(self, pogodata: PogoData) -> List[Move]:
        return self._get_base_moves(pogodata, self.eliteQuickMove, self.eliteCinematicMove)


class MoveSettings(BaseModel):
    uniqueId: str
    type: str

    def get_type(self, pogodata: PogoData):
        return pogodata.get_type(self.type)

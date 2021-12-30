from pydantic import BaseModel, validator, PrivateAttr
from typing import Optional, List
from enum import Enum
import math
from arrow import Arrow

from taubsi.core import bot
from taubsi.core.pogo import Moveset
from taubsi.pogodata import Pokemon


class Difficulty(Enum):
    UNKNOWN = 0
    IMPOSSIBLE = 1
    HARD = 2
    MEDIUM = 3
    EASY = 4
    VERY_EASY = 5


class _BaseModel(BaseModel):
    @validator("*")
    def list_reverse(cls, v):
        if isinstance(v, list):
            v.reverse()
        return v


class _BaseResult(_BaseModel):
    power: float
    effectiveCombatTime: Optional[int]
    effectiveDeaths: Optional[float]
    potions: float
    overallRating: float
    numSims: int
    tdo: float
    tdi: float
    estimator: float


class AttackerResult(_BaseResult):
    win: Optional[bool]
    totalCombatTime: Optional[int]
    winRatio: Optional[float]
    kills: Optional[int]


class DefenderResult(_BaseResult):
    combatTime: Optional[int]
    numWins: Optional[int]
    numLosses: Optional[int]
    numResults: Optional[int]


class _BaseByMove(_BaseModel):
    move1: str
    move2: str

    @property
    def moveset(self):
        return Moveset.from_pokebattler(bot.pogodata, move_1=self.move1, move_2=self.move2)


class DefenderByMove(_BaseByMove):
    result: AttackerResult
    legacyDate: Optional[str]
    elite: Optional[bool]


class Defender(_BaseModel):
    pokemonId: str
    byMove: List[DefenderByMove]

    @property
    def pokemon(self):
        return Pokemon.from_pokebattler(self.pokemonId, bot.pogodata)


class AttackerByMove(_BaseByMove):
    defenders: List[Defender]
    total: DefenderResult


class AttackerStats(_BaseModel):
    attack: int
    defense: int
    stamina: int
    level: int
    boss: str  # level


class Attacker(_BaseModel):
    pokemonId: str
    byMove: List[AttackerByMove]
    cp: int
    numSims: int
    boss: str  # level
    randomMove: AttackerByMove
    stats: AttackerStats

    @property
    def pokemon(self):
        return Pokemon.from_pokebattler(self.pokemonId, bot.pogodata)


class RaidPayload(_BaseModel):
    _time: Arrow = PrivateAttr(default=Arrow.utcnow())
    attackers: List[Attacker]
    attackStrategy: str
    defenseStrategy: str
    numSims: int
    seed: str
    sortType: str
    filterType: str
    filterValue: str
    monteCarlo: str
    randomAssistants: int

    class Config:
        arbitrary_types_allowed = True

    @property
    def best_attackers(self) -> List[Defender]:
        return self.attackers[0].randomMove.defenders

    @property
    def estimator(self) -> float:
        return self.attackers[0].randomMove.total.estimator

    def get_difficulty(self, players: int) -> Difficulty:
        if players < self.estimator:
            if players < self.estimator - 0.3:
                difficulty = Difficulty.IMPOSSIBLE
            else:
                difficulty = Difficulty.HARD
        else:
            if players <= math.ceil(self.estimator):
                difficulty = Difficulty.MEDIUM
            elif players <= math.ceil(self.estimator) + 1:
                difficulty = Difficulty.EASY
            else:
                difficulty = Difficulty.VERY_EASY

        if players < math.floor(self.estimator):
            difficulty = Difficulty.IMPOSSIBLE

        if players == 0:
            difficulty = Difficulty.IMPOSSIBLE

        return difficulty

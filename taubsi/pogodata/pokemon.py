from __future__ import annotations
from typing import Dict, List, Union, Any, Optional, Type, TypeVar, TYPE_CHECKING
from math import floor

if TYPE_CHECKING:
    from taubsi.pogodata import PogoData


MULTIPLIERS = {
    10: 0.422500014305115,
    15: 0.517393946647644,
    20: 0.597400009632111,
    25: 0.667934000492096
}


class BaseStats:
    attack: int
    defense: int
    stamina: int

    def __init__(self, data: List[int]):
        if len(data) != 3:
            self.data = (0, 0, 0)
        self.stamina, self.attack, self.defense = data

    def __repr__(self):
        return f"<BaseStats {self.__str__()}>"

    def __str__(self):
        return f"{self.attack}/{self.defense}/{self.stamina}"

    @property
    def atk(self) -> int:
        return self.attack

    @property
    def def_(self) -> int:
        return self.defense

    @property
    def sta(self) -> int:
        return self.stamina


class Pokemon:
    id: int
    form_id: int
    costume_id: int
    mega_id: int
    base_stats: BaseStats
    mon_name: str
    form_name: str
    proto_id: str

    def __init__(self, id_: int, pogodata: PogoData, form: int = 0, costume: int = 0, mega: int = 0):
        self.id = id_
        self.form_id = form
        self.costume_id = costume
        self.mega_id = mega

        self.proto_id = pogodata.mon_mapping.get(self.id, "UNOWN")

        self.base_stats = pogodata.base_stats.get(f"{self.id}:{self.form_id}:0")
        if not self.base_stats:
            self.base_stats = pogodata.base_stats.get(f"{self.id}:0:0")
        if not self.base_stats:
            self.base_stats = BaseStats([10, 10, 10])

        self.mon_name = pogodata.mons.get(f"{self.id}:0:{self.mega_id}", "")
        self.form_name = pogodata.forms.get(self.form_id, "")

    @classmethod
    def from_db(cls, data: Dict[str, Any], pogodata: PogoData):
        return cls(
            id_=data.get("pokemon_id", 0),
            pogodata=pogodata,
            form=data.get("form", 0),
            costume=data.get("costume", 0),
            mega=data.get("evolution", data.get("temp_evolution_id", 0))
        )

    @classmethod
    def from_pogoinfo(cls, data: Dict[str, Any], pogodata: PogoData):
        return cls(
            id_=data.get("id", 0),
            pogodata=pogodata,
            form=data.get("form", 0),
            costume=data.get("costume", 0),
            mega=data.get("temp_evolution_id", 0)
        )

    @classmethod
    def from_gamemaster(cls, settings: Dict[str, Any]):
        t = []
        self = cls()
        stats = settings.get("stats")
        self.base_stats = BaseStats(list(stats.values()))
        templateid = settings["templateId"]
        self.id = int(templateid[1:5])
        self.pokemon_template = settings.get("pokemonId", "")
        self.form_template = settings.get("form", "")
        return self

    def __repr__(self):
        return f"<Pokemon {self.id}>"

    def __str__(self):
        return self.name

    def __bool__(self):
        return bool(self.id)

    @property
    def name(self):
        if not self.form_name:
            return self.mon_name
        else:
            return self.form_name + " " + self.mon_name

    def cp(self, level: int, iv: List[int]) -> int:
        multiplier = MULTIPLIERS.get(level, 0.5)
        attack = self.base_stats.attack + iv[0]
        defense = self.base_stats.defense + iv[1]
        stamina = self.base_stats.stamina + iv[2]
        return floor((attack * defense ** 0.5 * stamina ** 0.5 * multiplier ** 2) / 10)
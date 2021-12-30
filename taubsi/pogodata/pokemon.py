from __future__ import annotations
from typing import Dict, List, Union, Any, Optional, Type, TypeVar, TYPE_CHECKING
from math import floor
from taubsi.core.logging import log

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
    proto_form: str
    is_shadow: bool

    def __init__(self, id_: int, pogodata: PogoData, form: int = 0, costume: int = 0, mega: int = 0,
                 is_shadow: bool = False):
        self.__shadow_translation = pogodata.shadow_translation
        self.id = id_
        self.form_id = form
        self.costume_id = costume
        self.mega_id = mega
        self.is_shadow = is_shadow

        self.proto_id = pogodata.mon_id_to_proto.get(self.id, "UNOWN")

        if form > 0:
            self.proto_form = pogodata.form_id_to_proto.get(form, "")
        else:
            self.proto_form = ""

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

    @classmethod
    def from_pokebattler(cls, name: str, pogodata: PogoData):
        mega_id = 0
        form_id = 0
        is_shadow = False
        if "_MEGA" in name:
            if name.endswith("Y"):
                mega_id = 3
            elif name.endswith("X"):
                mega_id = 2
            else:
                mega_id = 1
            name = name.split("_MEGA")[0]
        elif name.endswith("_FORM"):
            if "SHADOW" in name:
                is_shadow = True
            name = name.replace("_FORM", "")
            form_id = pogodata.form_proto_to_id.get(name, 0)
            name = name.split("_")[0]

            if form_id == 0:
                log.info(f"Could not find form ID for pokebattler mon {name}")

        mon_id = pogodata.mon_proto_to_id.get(name, 0)
        if mon_id == 0:
            log.info(f"Could not find Mon ID for pokebattler mon {name}")

        return cls(
            id_=mon_id,
            pogodata=pogodata,
            form=form_id,
            costume=0,
            mega=mega_id,
            is_shadow=is_shadow
        )

    def __repr__(self):
        return f"<Pokemon {self.id}>"

    def __str__(self):
        return self.name

    def __bool__(self):
        return bool(self.id)

    @property
    def name(self):
        name = ""

        if self.is_shadow:
            name += self.__shadow_translation + " "

        # Niantic kinda messed up Kyurem form names
        if self.id == 646 and self.form_id == 146:
            return name + self.mon_name

        if not self.form_name:
            return name + self.mon_name
        else:
            return name + self.form_name + " " + self.mon_name

    def cp(self, level: int, iv: List[int]) -> int:
        multiplier = MULTIPLIERS.get(level, 0.5)
        attack = self.base_stats.attack + iv[0]
        defense = self.base_stats.defense + iv[1]
        stamina = self.base_stats.stamina + iv[2]
        return floor((attack * defense ** 0.5 * stamina ** 0.5 * multiplier ** 2) / 10)

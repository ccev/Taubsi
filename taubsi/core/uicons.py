from __future__ import annotations

import itertools
import random
from enum import Enum
from typing import Dict, Any, Optional, List, Union, Tuple, TYPE_CHECKING

import requests

from taubsi.pogodata import Pokemon, PokemonType, Weather
from taubsi.utils.utils import asyncget

if TYPE_CHECKING:
    from taubsi.core.pogo import Gym, Raid


class IconSetManager:
    name: str
    url: str
    index: Dict[str, Any]

    def __init__(self, name: str, url: str):
        self.url = url
        self.name = name

        result = requests.get(url + "index.json")
        self.index = result.json()
        self.reload_index()

    def reload_index(self):
        for key, value in self.index.copy().items():
            if not isinstance(value, dict):
                continue
            for sub_key, sub_value in value.items():
                self.index[f"{key}/{sub_key}"] = sub_value
            self.index.pop(key)

    async def reload(self):
        self.index = await asyncget(self.url + "Index.json", as_json=True)
        self.reload_index()


class UIconCategory(Enum):
    POKEMON = "pokemon"
    GYM = "gym"
    RAID_EGG = "raid/egg"
    WEATHER = "weather"
    TYPE = "type"


class IconSet(Enum):
    POGO_OUTLINE = IconSetManager("Pogo (Outline)", "https://raw.githubusercontent.com/whitewillem/PogoAssets/"
                                                    "main/uicons-outline/")
    POGO = IconSetManager("Pogo", "https://raw.githubusercontent.com/WatWowMap/wwm-uicons/main/")


class UIconManager:
    def pokemon(self, pokemon: Pokemon, shiny: bool = False, iconset: Optional[IconSet] = None) -> str:
        args = [
            ("", pokemon.id),
            ("e", pokemon.mega_id),
            ("f", pokemon.form_id),
            ("c", pokemon.costume_id)
        ]
        if shiny:
            args.append(("s", ""))
        return self.get(UIconCategory.POKEMON, iconset, args)

    def egg(self, raid: Raid, iconset: Optional[IconSet] = None) -> str:
        args = [("", raid.level)]
        # if raid.has_hatched:
        #     args.append(("h", ""))
        return self.get(UIconCategory.RAID_EGG, iconset, args)

    def raid(self, raid: Raid, shiny_chance: int = 0, iconset: Optional[IconSet] = None) -> str:
        if raid.boss:
            if shiny_chance:
                shiny = random.randint(1, shiny_chance) == 1
            else:
                shiny = False
            return self.pokemon(raid.boss, shiny, iconset)
        else:
            return self.egg(raid, iconset)

    def gym(self, gym: Gym, iconset: Optional[IconSet] = None) -> str:
        return self.get(UIconCategory.GYM, iconset, [("", gym.team.value)])

    def weather(self, weather: Weather, iconset: Optional[IconSet] = None) -> str:
        return self.get(UIconCategory.WEATHER, iconset, [("", weather.id)])

    def type(self, type_: PokemonType, iconset: Optional[IconSet] = None) -> str:
        return self.get(UIconCategory.TYPE, iconset, [("", type_.id)])

    @staticmethod
    def get(category: UIconCategory,
            iconset: Optional[IconSet] = None,
            args: Optional[List[Tuple[str, Union[str, int]]]] = None) -> str:
        if not iconset:
            iconset = IconSet.POGO
        if not args:
            args = []
        fin_args = []
        for identifier, id_ in args:
            if id_ != 0:
                fin_args.append(f"{identifier}{id_}")

        combinations = []
        for i in range(len(fin_args) + 1, 0, -1):
            for subset in itertools.combinations(fin_args, i):
                if subset[0] == fin_args[0]:
                    combinations.append(list(subset))
        combinations.append(["0"])
        for combination in combinations:
            name = "_".join(combination) + ".png"
            if name in iconset.value.index.get(category.value, []):
                return iconset.value.url + f"{category.value}/{name}"
        return iconset.value.url + "pokemon/0.png"

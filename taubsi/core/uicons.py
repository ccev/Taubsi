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
    id: str

    def __init__(self, name: str, url: str, id_: str):
        self.url = url
        self.name = name
        self.id = id_

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
        self.index = await asyncget(self.url + "index.json", as_json=True)
        self.reload_index()


class UIconCategory(Enum):
    # attention when adding more categories: make sure their first letter isn't duplicated because emoji manager
    POKEMON = "pokemon"
    GYM = "gym"
    RAID_EGG = "raid/egg"
    WEATHER = "weather"
    TYPE = "type"


class IconSet(Enum):
    POGO_OUTLINE = IconSetManager("Pogo (Outline)", "https://raw.githubusercontent.com/whitewillem/PogoAssets/"
                                                    "main/uicons-outline/", id_="go")
    POGO = IconSetManager("Pogo", "https://raw.githubusercontent.com/WatWowMap/wwm-uicons/main/", id_="g")


class UIcon:
    name: str
    url: str
    category: UIconCategory
    iconset: IconSet

    def __init__(self, name: str, category: UIconCategory, iconset: IconSet):
        self.name = name
        self.category = category
        self.iconset = iconset

        self.url = f"{iconset.value.url}{self.category.value}/{name}.png"

    def __repr__(self):
        return f"<UIcon name={self.name} iconset={self.iconset.name}"

    def __str__(self):
        return self.url

    def __bool__(self):
        return bool(self.url)


class UIconManager:
    def pokemon(self, pokemon: Pokemon, shiny: bool = False, iconset: Optional[IconSet] = None) -> UIcon:
        args = [
            ("", pokemon.id),
            ("e", pokemon.mega_id),
            ("f", pokemon.form_id),
            ("c", pokemon.costume_id)
        ]
        if shiny:
            args.append(("s", ""))
        return self.get(UIconCategory.POKEMON, iconset, args)

    def egg(self, raid: Raid, iconset: Optional[IconSet] = None) -> UIcon:
        args = [("", raid.level)]
        # if raid.has_hatched:
        #     args.append(("h", ""))
        return self.get(UIconCategory.RAID_EGG, iconset, args)

    def raid(self, raid: Raid, shiny_chance: int = 0, iconset: Optional[IconSet] = None) -> UIcon:
        if raid.boss:
            if shiny_chance:
                shiny = random.randint(1, shiny_chance) == 1
            else:
                shiny = False
            return self.pokemon(raid.boss, shiny, iconset)
        else:
            return self.egg(raid, iconset)

    def gym(self, gym: Gym, iconset: Optional[IconSet] = None) -> UIcon:
        return self.get(UIconCategory.GYM, iconset, [("", gym.team.value)])

    def weather(self, weather: Weather, iconset: Optional[IconSet] = None) -> UIcon:
        return self.get(UIconCategory.WEATHER, iconset, [("", weather.id)])

    def type(self, type_: PokemonType, iconset: Optional[IconSet] = None) -> UIcon:
        if iconset is None:
            iconset = IconSet.POGO_OUTLINE
        return self.get(UIconCategory.TYPE, iconset, [("", type_.id)])

    @staticmethod
    def get(category: UIconCategory,
            iconset: Optional[IconSet] = None,
            args: Optional[List[Tuple[str, Union[str, int]]]] = None) -> UIcon:
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

        name = ""
        for combination in combinations:
            possible_name = "_".join(combination)
            if possible_name + ".png" in iconset.value.index.get(category.value, []):
                name = possible_name
                break

        if not name:
            name = "0"
            category = UIconCategory.POKEMON
        return UIcon(name=name, category=category, iconset=iconset)

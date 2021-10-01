from __future__ import annotations
from typing import Dict, Any, Optional, List, Union, Tuple, TYPE_CHECKING
from enum import Enum
import random

import requests
import arrow
from pogodata.pokemon import Pokemon

if TYPE_CHECKING:
    from taubsi.cogs.raids.pogo import Gym, BaseRaid, ScannedRaid


class IconSetManager:
    name: str
    url: str
    index: Dict[str, Any]

    def __init__(self, name: str, url: str):
        self.url = url
        self.name = name

        result = requests.get(url + "index.json")
        self.index = result.json()

        for key, value in self.index.copy().items():
            if not isinstance(value, dict):
                continue
            for sub_key, sub_value in value.items():
                self.index[f"{key}/{sub_key}"] = sub_value
            self.index.pop(key)


class UIconCategory(Enum):
    POKEMON = "pokemon"
    GYM = "gym"
    RAID_EGG = "raid/egg"


class IconSet(Enum):
    POGO = IconSetManager("Pogo", "https://raw.githubusercontent.com/WatWowMap/wwm-uicons/main/")
    POGO_OUTLINE = IconSetManager("Pogo (Outline)", "https://raw.githubusercontent.com/whitewillem/PogoAssets/"
                                                    "main/uicons-outline/")


class UIconManager:
    def pokemon(self, pokemon: Pokemon, shiny: bool = False, iconset: Optional[IconSet] = None) -> str:
        args = [
            ("", pokemon.id),
            ("e", pokemon.temp_evolution_id),
            ("f", pokemon.form),
            ("c", pokemon.costume)
        ]
        if shiny:
            args.append(("s", ""))
        return self.get(UIconCategory.POKEMON, iconset, args)

    def egg(self, raid: Union[BaseRaid, ScannedRaid], iconset: Optional[IconSet] = None) -> str:
        args = [("", raid.level)]
        if raid.__dict__.get("start") and raid.start > arrow.utcnow():
            args.append(("h", ""))
        return self.get(UIconCategory.RAID_EGG, iconset, args)

    def raid(self, raid: BaseRaid, shiny_chance: int = 0, iconset: Optional[IconSet] = None) -> str:
        if raid.boss:
            if shiny_chance:
                shiny = random.randint(1, shiny_chance) == 1
            else:
                shiny = False
            return self.pokemon(raid.boss, shiny, iconset)
        else:
            return self.egg(raid, iconset)

    def gym(self, gym: Gym, iconset: Optional[IconSet] = None) -> str:
        return self.get(UIconCategory.GYM, iconset, [("", gym.team)])

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
            fin_args.append(f"{identifier}{id_}")

        combinations = []
        for i in range(1, len(fin_args) + 1):
            combinations.insert(0, fin_args[:i])
        i = 0
        for combination in combinations.copy():
            if len(combination) > 2:
                new_combination = combination.copy()
                del new_combination[-2]
                combinations.insert(i + 2, new_combination)
                i += 2
        combinations.append(["0"])

        for combination in combinations:
            name = "_".join(combination) + ".png"
            if name in iconset.value.index.get(category.value, []):
                return iconset.value.url + f"{category.value}/{name}"
        return iconset.value.url + "pokemon/0.png"

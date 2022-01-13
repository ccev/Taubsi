import re
from enum import Enum
from typing import Dict, List, Optional, Any, Union

import requests

from taubsi.utils.utils import asyncget
from .move import Move
from .pokemon import Pokemon, BaseStats
from .pokemon_type import PokemonType, TYPES
from .weather import Weather, WEATHERS
from .gamemaster_models import PokemonSettings, MoveSettings
from .enum import PogoDataEnum


GAMEMASTER_URL = "https://raw.githubusercontent.com/PokeMiners/game_masters/master/latest/latest.json"
PROTO_URL = "https://raw.githubusercontent.com/Furtif/POGOProtos/master/base/vbase.proto"
LOCALE_URL = "https://raw.githubusercontent.com/PokeMiners/pogo_assets/master/Texts/Latest%20APK/{}.txt"
REMOTE_LOCALE_URL = "https://raw.githubusercontent.com/PokeMiners/pogo_assets/master/Texts/Latest%20Remote/{}.txt"
RAIDS_URL = "https://raw.githubusercontent.com/ccev/pogoinfo/v2/active/raids.json"


class PogoData:
    def __init__(self, language: str, raw_protos: str, raw_gamemaster: List[dict], raids: Dict[str, List[dict]]):
        self.pokemon_enum: PogoDataEnum = self._convert_enum(raw_protos, "HoloPokemonId")
        self.form_enum: PogoDataEnum = self._convert_enum(raw_protos, "Form")
        self.mega_enum: PogoDataEnum = self._convert_enum(raw_protos, "HoloTemporaryEvolutionId")
        self.move_enum: PogoDataEnum = self._convert_enum(raw_protos, "HoloPokemonMove")
        self.type_enum: PogoDataEnum = self._convert_enum(raw_protos, "HoloPokemonType")
        self.weather_enum: PogoDataEnum = self._convert_enum(raw_protos, "WeatherCondition")

        self.mon_translations: Dict[str, str] = {}
        self.form_translations: Dict[int, str] = {}
        self.move_translations: Dict[int, str] = {}
        self.shadow_translation: str = ""

        self.pokemon_settings: Dict[str, PokemonSettings] = {}
        self.move_settings: Dict[int, MoveSettings] = {}

        self.raids: Dict[int, List[Pokemon]] = {}
        self.types: List[PokemonType] = []
        self.weathers: List[Weather] = []

        self.__make_types()
        self.__make_weathers()
        self.__make_locale(language)
        self.__parse_gamemaster(raw_gamemaster)
        self.__make_raids(raids)

    def __make_types(self):

        for args in TYPES:
            self.types.append(PokemonType(*args))

        for type_ in self.types:
            type_.weak_to = [self.get_type(t) for t in type_.weak_to_ids]

    def __make_weathers(self):
        self.weathers = []
        for args in WEATHERS:
            self.weathers.append(Weather(*args))

        for weather_ in self.weathers:
            weather_.boosts = []
            for type_id in weather_.boost_ids:
                type_ = self.get_type(type_id)
                type_.boosted_by = weather_
                weather_.boosts.append(type_)

    def __make_locale(self, language: str):
        for url in [LOCALE_URL, REMOTE_LOCALE_URL]:
            raw = requests.get(url.format(language.title())).text
            keys = re.findall(r"(?<=RESOURCE ID: ).*", raw)
            values = re.findall(r"(?<=TEXT: ).*", raw)

            for i in range(len(keys)):
                k: str = keys[i].strip("\r")
                v: str = values[i].strip("\r")
                if k.startswith("form_"):
                    form_name = k[5:]
                    form_id = self.form_enum.get(form_name.upper()).value
                    if form_id:
                        self.form_translations[form_id] = v
                elif k.startswith("pokemon_name_"):
                    parts = k[13:].split("_")
                    if len(parts) == 2:
                        mega_id = int(parts[1])
                    else:
                        mega_id = 0
                    mon_id = int(parts[0])
                    self.mon_translations[f"{mon_id}:{mega_id}"] = v
                elif k.startswith("move_name_"):
                    self.move_translations[int(k[10:])] = v
                elif k == "filter_label_shadow":
                    self.shadow_translation = v

    def __parse_gamemaster(self, raw_gamemaster: List[Dict]):
        for entry in raw_gamemaster:
            templateid = entry.get("templateId", "")
            if re.search(r"^V\d{4}_POKEMON_", templateid):
                data = entry.get("data", {})
                raw_settings = data.get("pokemonSettings", {})
                stats = raw_settings.get("stats")
                if not raw_settings or not stats:
                    continue

                settings = PokemonSettings(**raw_settings)

                mon_id = self.pokemon_enum.get(settings.pokemonId).value
                form_id = self.form_enum.get(settings.form).value
                identifier = f"{mon_id}:{form_id}"

                self.pokemon_settings[identifier] = settings

            elif re.search(r"^COMBAT_V\d{4}_MOVE_", templateid):
                data = entry.get("data", {})
                raw_settings = data.get("combatMove", {})
                if not raw_settings:
                    continue

                settings = MoveSettings(**raw_settings)
                move_id = self.move_enum.get(settings.uniqueId).value
                self.move_settings[move_id] = settings

    def __make_raids(self, raids: Dict[str, List[dict]]):
        for level, raids in raids.items():
            self.raids[int(level)] = [Pokemon.from_pogoinfo(d, self) for d in raids]

    @classmethod
    def make_sync(cls, language: str):
        raw_protos = requests.get(PROTO_URL).text
        raw_gamemaster = requests.get(GAMEMASTER_URL).json()
        raids = requests.get(RAIDS_URL).json()
        return cls(language, raw_protos, raw_gamemaster, raids)

    @classmethod
    async def make_async(cls, language: str):
        raw_protos = await asyncget(PROTO_URL, as_text=True)
        raw_gamemaster = await asyncget(GAMEMASTER_URL, as_json=True)
        raids = await asyncget(RAIDS_URL, as_json=True)
        return cls(language, raw_protos, raw_gamemaster, raids)

    @staticmethod
    def _convert_enum(protos: str, enum: str) -> PogoDataEnum:
        proto = re.findall(f"enum {enum} " + r"{[^}]*}", protos, re.IGNORECASE)

        final = []
        for entry in proto[0].split("\n"):
            if "}" in entry or "{" in entry:
                continue
            entry = entry.replace(" ", "").replace(";", "").split("=")
            final.append(
                (
                    entry[0].strip(),
                    int(entry[1].strip())
                )
            )

        return PogoDataEnum(enum, final)

    def get_pokemon(self,
                    pokemon_id: int = 0,
                    form: int = 0,
                    costume: int = 0,
                    evolution: int = 0,
                    **kwargs) -> Pokemon:
        return Pokemon(pokemon_id, self, form, costume, evolution)

    def get_move(self, move_id: Union[int, str]):
        return Move(move_id, self)

    @staticmethod
    def _get_generic(li: list, generic_enum: PogoDataEnum, generic_id: Union[str, int]):
        index = generic_enum.get(generic_id).value
        if index >= len(li):
            return li[0]
        return li[index]

    def get_type(self, type_id: Union[str, int]) -> PokemonType:
        return self._get_generic(self.types, self.type_enum, type_id)

    def get_weather(self, weather_id: Union[str, int]) -> Weather:
        return self._get_generic(self.weathers, self.weather_enum, weather_id)

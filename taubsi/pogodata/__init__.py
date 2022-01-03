from typing import Dict, List, Optional, Any, Union
import re

import requests

from taubsi.pogodata.pokemon import Pokemon, BaseStats
from taubsi.pogodata.move import Move
from taubsi.pogodata.pokemon_type import PokemonType, TYPES
from taubsi.pogodata.weather import Weather, WEATHERS
from taubsi.utils.utils import asyncget

GAMEMASTER_URL = "https://raw.githubusercontent.com/PokeMiners/game_masters/master/latest/latest.json"
PROTO_URL = "https://raw.githubusercontent.com/Furtif/POGOProtos/master/base/vbase.proto"
LOCALE_URL = "https://raw.githubusercontent.com/PokeMiners/pogo_assets/master/Texts/Latest%20APK/{}.txt"
REMOTE_LOCALE_URL = "https://raw.githubusercontent.com/PokeMiners/pogo_assets/master/Texts/Latest%20Remote/{}.txt"
RAIDS_URL = "https://raw.githubusercontent.com/ccev/pogoinfo/v2/active/raids.json"


class PogoData:
    base_stats: Dict[str, BaseStats]
    mons: Dict[str, str]
    forms: Dict[int, str]
    moves: Dict[int, str]
    move_id_to_proto: Dict[int, str]
    raids: Dict[int, List[Pokemon]]
    shadow_translation: str

    types: List[PokemonType]
    weathers: List[Weather]

    def __init__(self, language: str, raw_protos: str, raw_gamemaster: List[dict], raids: Dict[str, List[dict]]):
        self.base_stats = {}
        self.mons = {}
        self.forms = {}
        self.moves = {}
        self.mon_proto_to_id = {}
        self.form_proto_to_id = {}
        self.form_id_to_proto = {}
        self.raids = {}
        self.mon_to_types: Dict[str, List[PokemonType]] = {}

        self.mon_proto_to_id = self._enum_to_dict(raw_protos, "HoloPokemonId")
        self.mon_id_to_proto = self._enum_to_dict(raw_protos, "HoloPokemonId", reverse=True)
        self.form_id_to_proto = self._enum_to_dict(raw_protos, "Form", reverse=True)
        self.form_proto_to_id = self._enum_to_dict(raw_protos, "Form")
        mega_mapping = self._enum_to_dict(raw_protos, "HoloTemporaryEvolutionId")
        self.move_proto_to_id = self._enum_to_dict(raw_protos, "HoloPokemonMove")
        self.move_id_to_proto = self._enum_to_dict(raw_protos, "HoloPokemonMove", reverse=True)

        self.types = []
        for args in TYPES:
            self.types.append(PokemonType(*args))

        self.weathers = []
        for args in WEATHERS:
            self.weathers.append(Weather(*args))

        for url in [LOCALE_URL, REMOTE_LOCALE_URL]:
            raw = requests.get(url.format(language.title())).text
            keys = re.findall(r"(?<=RESOURCE ID: ).*", raw)
            values = re.findall(r"(?<=TEXT: ).*", raw)

            for i in range(len(keys)):
                k: str = keys[i].strip("\r")
                v: str = values[i].strip("\r")
                if k.startswith("form_"):
                    form_name = k[5:]
                    form_id = self.form_id_to_proto.get(form_name.upper())
                    if form_id:
                        self.forms[form_id] = v
                elif k.startswith("pokemon_name_"):
                    parts = k[13:].split("_")
                    if len(parts) == 2:
                        mega_id = int(parts[1])
                    else:
                        mega_id = 0
                    mon_id = int(parts[0])
                    self.mons[f"{mon_id}:0:{mega_id}"] = v
                elif k.startswith("move_name_"):
                    self.moves[int(k[10:])] = v
                elif k == "filter_label_shadow":
                    self.shadow_translation = v

        result = []
        for entry in raw_gamemaster:
            templateid = entry.get("templateId", "")
            if re.search(r"^V\d{4}_POKEMON_", templateid):
                data = entry.get("data", {})
                settings = data.get("pokemonSettings", {})
                stats = settings.get("stats")
                if not settings or not stats:
                    continue

                mon = settings.get("pokemonId")
                mon_id = self.mon_proto_to_id.get(mon, 0)

                form = settings.get("form")
                form_id = self.form_proto_to_id.get(form, 0)
                base_stats = BaseStats(list(stats.values()))
                identifier = f"{mon_id}:{form_id}"
                self.base_stats[f"{identifier}:0"] = base_stats

                types = []
                self._gamemaster_type_convert(settings, "type", types)
                self._gamemaster_type_convert(settings, "type2", types)
                self.mon_to_types[f"{identifier}:0"] = types

                mega_overrides: Optional[List[dict]] = settings.get("tempEvoOverrides")
                if not mega_overrides:
                    continue
                for mega_override in mega_overrides:
                    stats = mega_override.get("stats")
                    if not stats:
                        continue
                    base_stats = BaseStats(list(stats.values()))
                    mega = mega_override.get("tempEvoId")
                    mega_id = mega_mapping.get(mega, 0)
                    identifier = f"{identifier}:{mega_id}"
                    self.base_stats[identifier] = base_stats

                    types = []
                    self._gamemaster_type_convert(settings, "typeOverride1", types)
                    self._gamemaster_type_convert(settings, "typeOverride2", types)
                    self.mon_to_types[f"{identifier}:0"] = types

        for level, raids in raids.items():
            self.raids[int(level)] = [Pokemon.from_pogoinfo(d, self) for d in raids]

    def _gamemaster_type_convert(self, settings: dict, key: str, types: list):
        type_ = settings.get(key)
        if not type_:
            return

        for montype in self.types:
            if montype.proto == type_:
                types.append(montype)
                return

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
    def _enum_to_dict(protos: str, enum: str, reverse: bool = False) -> Union[Dict[str, int], Dict[int, str]]:
        proto = re.findall(f"enum {enum} " + r"{[^}]*}", protos, re.IGNORECASE)

        final = {}
        for entry in proto[0].split("\n"):
            if "}" in entry or "{" in entry:
                continue
            k: str = entry.split(" =")[0].strip()
            v: int = int(entry.split("= ")[1].split(";")[0].strip())
            if reverse:
                final[v] = k
            else:
                final[k] = v

        return final

    def get_pokemon(self, data: Dict[str, Any]):
        """
        data = {
            "pokemon_id": int,
            "form": int,
            "costume": int,
            "temp_evolution_id": int
        }
        """
        return Pokemon.from_db(data, self)

    def get_move(self, move_id: int):
        return Move(move_id, self)

    @staticmethod
    def _get_generic(li: list, value: int):
        if value >= len(li):
            return li[0]
        return li[value]

    def get_type(self, type_id: int) -> PokemonType:
        return self._get_generic(self.types, type_id)

    def get_weather(self, weather_id: int) -> Weather:
        return self._get_generic(self.weathers, weather_id)

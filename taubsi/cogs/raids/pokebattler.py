from __future__ import annotations

import json
from typing import TYPE_CHECKING, List

from taubsi.taubsi_objects import tb
from taubsi.utils.utils import asyncget

if TYPE_CHECKING:
    from .raidmessage import RaidMessage
    from pogodata.pokemon import Pokemon
    from pogodata.moves import Move

PB_LINK = "https://fight.pokebattler.com/raids/defenders/{}/levels/RAID_LEVEL_{}" \
          "/attackers/levels/35/strategies/CINEMATIC_ATTACK_WHEN_POSSIBLE/DEFENSE_RANDOM_MC?sort=ESTIMATOR" \
          "&weatherCondition=NO_WEATHER&dodgeStrategy=DODGE_REACTION_TIME&aggregation=AVERAGE&randomAssistants=-1" \
          "&includeLegendary=true&includeShadow=true&includeMegas=true&attackerTypes=POKEMON_TYPE_ALL "


class NameConverter:
    @staticmethod
    def from_pd(mon: Pokemon) -> str:
        mon_name: str = mon.template
        mon_name.strip("_NORMAL")

        if mon.temp_evolution_id > 0:
            mon_name += "_" + mon.temp_evolution_template.strip("TEMP_EVOLUTION_")
        elif mon_name != mon.base_template:
            mon_name += "_FORM"

        return mon_name

    @staticmethod
    def to_pd(mon_name: str) -> Pokemon:
        if "FORM" in mon_name:
            return tb.pogodata.get_mon(template=mon_name.strip("_FORM"))
        elif "MEGA" in mon_name:
            base, mega_type = mon_name.split("_MEGA")
            return tb.pogodata.get_mon(base_template=base, temp_evolution_base="TEMP_EVOLUTION_MEGA" + mega_type)

        return tb.pogodata.get_mon(base_template=mon_name)


class PokeBattler:
    @classmethod
    async def init(cls, raidmessage: RaidMessage, moves: List[Move] = None):
        if moves is None:
            moves = []
        cls.raidmessage: RaidMessage = raidmessage
        cls.moves: List[Move] = moves

        if not cls.raidmessage.raid.boss:
            return cls
        name = NameConverter.from_pd(cls.raidmessage.raid.boss)

        if cls.raidmessage.raid.level == 6:
            level = "MEGA"
        else:
            level = str(cls.raidmessage.raid.level)

        link = PB_LINK.format(name, level)
        result = await asyncget(link)
        result = json.loads(result.decode("utf-8"))
        print(result)
        final = {}

        attackers = result["attackers"][0]
        moves = attackers["byMove"]

        for move in moves:
            counters = []
            defenders = move["defenders"]

            for defender in defenders:
                mon = defender["pokemonId"]
                estimator = 100
                for def_move in defender["byMove"]:
                    def_est = def_move["result"]["estimator"]
                    if def_est < estimator:
                        estimator = def_est
                counters.append((mon, estimator))

            print(move["move1"], move["move2"])
            print(sorted(counters, key=lambda c: c[1]))
            print("\n\n")
        


from __future__ import annotations
from taubsi.pokebattler.models import RaidPayload
from typing import TYPE_CHECKING, Dict
from taubsi.utils.utils import asyncget
from taubsi.core.logging import log

from arrow import Arrow

if TYPE_CHECKING:
    from taubsi.pogodata import PogoData, Pokemon
    from taubsi.core.pogo import Raid


BASE_URL = "https://fight.pokebattler.com/raids/defenders/{}/levels/RAID_LEVEL_{}/attackers/levels/40/strategies/" \
           "CINEMATIC_ATTACK_WHEN_POSSIBLE/DEFENSE_RANDOM_MC?sort=ESTIMATOR&weatherCondition=NO_WEATHER&" \
           "dodgeStrategy=DODGE_REACTION_TIME&aggregation=AVERAGE&includeLegendary=true&includeShadow=true&" \
           "includeMegas=true&attackerTypes=POKEMON_TYPE_ALL"


class PokeBattler:
    _cache: Dict[str, RaidPayload]

    def __init__(self):
        self._cache = {}

    async def get(self, pokemon: Pokemon, level: int) -> RaidPayload:
        if level == 6:
            level = "MEGA"

        pokebattler_name = pokemon.proto_id
        if pokemon.mega_id > 0:
            pokebattler_name += "_MEGA"
        elif pokemon.form_id > 0 and "NORMAL" not in pokemon.proto_form:
            pokebattler_name = pokemon.proto_form + "_FORM"

        cached = self._cache.get(pokebattler_name)
        if cached and cached._time > Arrow.utcnow().shift(days=-1):
            log.info(f"Serving cached pokebattler result for {pokebattler_name}")
            return cached

        url = BASE_URL.format(pokebattler_name, level)
        log.info(f"Querying pokebattler for {pokebattler_name}")
        log.info(url)
        result = await asyncget(url, as_json=True)
        raid_payload = RaidPayload(**result)

        self._cache[pokebattler_name] = raid_payload
        return raid_payload

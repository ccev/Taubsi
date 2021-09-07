from __future__ import annotations
from typing import Dict, Union, List
from enum import Enum
import arrow

import discord
from discord.ext import commands

from taubsi.taubsi_objects import tb
from taubsi.cogs.playerstats.errors import *
from taubsi.utils.enums import Team
from config.emotes import BADGE_LEVELS


class DataLevel(Enum):
    NONE = 0
    TAUBSI = 10
    GYM = 20
    RAID = 30
    FRIEND = 40


class Player:
    ign: str
    user: discord.Member
    data_level: DataLevel

    team: Team
    level: int
    updated: arrow.Arrow
    stats: Dict[str, Union[int, arrow.Arrow]]

    def __init__(self, ign, user):
        self.ign = ign
        self.user = user

    async def get_stats(self):
        fetch_stats = ",".join([s.value for s in Stat.__dict__.values() if isinstance(s, Badge)])
        result = await tb.queries.execute(
            "SELECT team, level, last_seen, {} "
            "FROM cev_trainer "
            "WHERE name = '{}'".format(fetch_stats, self.ign),
            as_dict=True
        )
        self.stats = result[0]

        self.updated = arrow.get(self.stats["last_seen"]).to("local")
        self.level = self.stats["level"]
        self.team = Team(self.stats["team"])
        if self.stats["stops_spun"]:
            self.data_level = DataLevel.FRIEND
        elif self.stats["caught_pokemon"]:
            self.data_level = DataLevel.RAID
        elif self.stats["xp"]:
            self.data_level = DataLevel.GYM
        else:
            self.data_level = DataLevel.TAUBSI

    def make_text(self):
        return (
            f"XP: {self.stats['xp']}\n"
            f"Gedrehte Stops: {self.stats['stops_spun']}"
        )

    @classmethod
    async def from_command(cls, player, ctx: commands.Context):
        if isinstance(player, discord.Member):
            ign = await tb.intern_queries.execute(f"SELECT ingame_name FROM users WHERE user_id = {player.id}")
            if not ign or not ign[0] or not ign[0][0]:
                if player.id == ctx.author.id:
                    raise SelfNotLinked
                raise UserNotLinked
            ign = ign[0][0]
        else:
            if any(not c.isalnum() for c in player):
                raise PlayerNotLinked
            result = await tb.intern_queries.execute(f"SELECT user_id, ingame_name FROM users "
                                                     f"WHERE ingame_name = '{player}'")
            if not result:
                raise PlayerNotLinked
            user_id = result[0][0]
            ign = result[0][1]
            player = await ctx.guild.fetch_member(int(user_id))

        player_ = cls(ign, player)
        await player_.get_stats()
        return player_


class Badge:
    value: str
    targets: List[int]

    def __init__(self, value: str, targets: List[int]):
        self.value = value
        self.targets = targets

    def next_target(self, number: int) -> str:
        for target in self.targets:
            if target > number:
                return f"/{target:,}"
        return ""

    def get_tier_prefix(self, number: int) -> str:
        level = sum([1 for t in self.targets if t <= number])
        emoji = BADGE_LEVELS[level]
        return emoji


class Stat:
    XP = Badge("xp", [])
    KM_WALKED = Badge("km_walked", [10, 100, 1000, 10000])
    CAUGHT_POKEMON = Badge("caught_pokemon", [30, 500, 2000, 50000])
    STOPS = Badge("stops_spun", [100, 1000, 2000, 50000])
    EVOLVED = Badge("evolved", [3, 20, 200, 2000])
    HATCHED = Badge("hatched", [10, 100, 500, 2500])
    QUESTS = Badge("quests", [10, 100, 1000, 2500])
    TRADES = Badge("trades", [10, 100, 1000, 2500])
    UNIQUE_STOPS = Badge("unique_stops_spun", [10, 100, 1000, 2000])
    BEST_FRIENDS = Badge("best_friends", [1, 2, 3, 20])

    TOTAL_BATTLES_WON = Badge("battles_won", [])
    NORMAL_RAIDS_WON = Badge("normal_raids_won", [10, 100, 1000, 2000])
    LEGENDARY_RAIDS_WON = Badge("legendary_raids_won", [10, 100, 1000, 2000])
    FRIEND_RAIDS = Badge("raids_with_friends", [10, 100, 1000, 2000])
    RAID_ACHIEVEMENTS = Badge("raid_achievements", [1, 50, 200, 500])
    UNIQUE_RAIDS = Badge("unique_raid_bosses", [2, 10, 50, 150])
    GRUNTS = Badge("grunts_defeated", [10, 100, 1000, 2000])
    GIOVANNI = Badge("giovanni_defeated", [1, 5, 20, 50])
    PURIFIED = Badge("purified", [5, 50, 500, 1000])
    GYM_BATTLES_WON = Badge("gym_battles_won", [10, 100, 1000, 4000])
    BERRIES_FED = Badge("berries_fed", [10, 100, 1000, 15000])
    HOURS_DEFENDED = Badge("hours_defended", [10, 100, 1000, 15000])
    TRAININGS_WON = Badge("trainings_won", [10, 100, 1000, 2000])
    GREAT_WON = Badge("league_great_won", [5, 50, 200, 1000])
    ULTRA_WON = Badge("league_ultra_won", [5, 50, 200, 1000])
    MASTER_WON = Badge("league_master_won", [5, 50, 200, 1000])
    GBL_RANK = Badge("gbl_rank", [])
    GBL_RATING = Badge("gbl_rating", [])

    BEST_BUDDIES = Badge("best_buddies", [1, 10, 100, 200])
    MEGA_EVOS = Badge("mega_evos", [1, 50, 500, 1000])
    COLLECTIONS = Badge("collections_done", [])
    UNIQUE_MEGA_EVOS = Badge("unique_mega_evos", [1, 24, 36, 46])
    STREAKS = Badge("7_day_streaks", [1, 10, 50, 100])
    TRADE_KM = Badge("trade_km", [1000, 100000, 1000000, 10000000])
    LURE_CAUGHT = Badge("caught_at_lure", [5, 25, 500, 2500])
    WAYFARER = Badge("wayfarer_agreements", [50, 500, 1000, 1500])
    REFERRED = Badge("trainers_referred", [1, 10, 20, 50])
    PHOTOBOMBS = Badge("photobombs", [10, 50, 200, 400])

    UNIQUE_UNOWN = Badge("unique_unown", [3, 10, 26, 28])
    XL_KARPS = Badge("xl_karps", [3, 50, 300, 1000])
    XS_RATS = Badge("xs_rats", [3, 50, 300, 1000])
    PIKACHU = Badge("pikachu_caught", [3, 50, 300, 1000])
    DEX_1 = Badge("dex_gen1", [5, 50, 100, 151])
    DEX_2 = Badge("dex_gen2", [5, 30, 70, 100])
    DEX_3 = Badge("dex_gen3", [5, 40, 90, 135])
    DEX_4 = Badge("dex_gen4", [5, 30, 80, 107])
    DEX_5 = Badge("dex_gen5", [5, 50, 100, 156])
    DEX_6 = Badge("dex_gen6", [5, 25, 50, 72])
    DEX_7 = Badge("dex_gen7", [])
    DEX_8 = Badge("dex_gen8", [5, 25, 50, 89])
    NORMAL = Badge("caught_normal", [10, 50, 200, 2500])
    FIGHTING = Badge("caught_fighting", [10, 50, 200, 2500])
    FLYING = Badge("caught_flying", [10, 50, 200, 2500])
    POISON = Badge("caught_poison", [10, 50, 200, 2500])
    GROUND = Badge("caught_ground", [10, 50, 200, 2500])
    ROCK = Badge("caught_rock", [10, 50, 200, 2500])
    BUG = Badge("caught_bug", [10, 50, 200, 2500])
    GHOST = Badge("caught_ghost", [10, 50, 200, 2500])
    STEEL = Badge("caught_steel", [10, 50, 200, 2500])
    FIRE = Badge("caught_fire", [10, 50, 200, 2500])
    WATER = Badge("caught_water", [10, 50, 200, 2500])
    GRASS = Badge("caught_grass", [10, 50, 200, 2500])
    ELECTRIC = Badge("caught_electric", [10, 50, 200, 2500])
    PSYCHIC = Badge("caught_psychic", [10, 50, 200, 2500])
    ICE = Badge("caught_ice", [10, 50, 200, 2500])
    DRAGON = Badge("caught_dragon", [10, 50, 200, 2500])
    DARK = Badge("caught_dark", [10, 50, 200, 2500])
    FAIRY = Badge("caught_fairy", [10, 50, 200, 2500])

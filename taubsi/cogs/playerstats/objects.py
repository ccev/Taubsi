from __future__ import annotations
from typing import Optional, Dict, List, Union
from enum import Enum
from datetime import datetime
import time
import arrow

import discord
from discord.ext import commands

from taubsi.taubsi_objects import tb
from taubsi.cogs.playerstats.errors import *
from taubsi.utils.enums import Team
from config.emotes import TEAM_COLORS, BADGE_LEVELS


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
    updated: int
    stats: Dict[str, int]

    def __init__(self, ign, user):
        self.ign = ign
        self.user = user

    async def get_stats(self):
        fetch_stats = ",".join([s.value for s in Stat.__dict__.values() if isinstance(s, Badge)])
        result = await tb.queries.execute(
            "SELECT team, level, last_seen AS last_seen, {} "
            "FROM cev_trainer "
            "WHERE name = '{}'".format(fetch_stats, self.ign),
            as_dict=True
        )
        self.stats = result[0]

        self.updated = self.stats["last_seen"]
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
            if not ign:
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
    
    
class _StatCategory(discord.SelectOption):
    name: str
    id: str
    stats: Dict[str, List[Stat]]
    
    def __init__(self):
        self.id = self.name
        lang_key = "stats_category_" + self.name
        self.name = tb.translate(lang_key)
        desc = tb.translate(lang_key + "_desc")

        super().__init__(label=self.name, value=self.id, description=desc)


class StatCategoryGeneral(_StatCategory):
    name = "general"
    stats = {
        None: [Stat.XP, Stat.CAUGHT_POKEMON, Stat.STOPS, Stat.KM_WALKED,
               Stat.HATCHED, Stat.QUESTS, Stat.EVOLVED, Stat.TRADES,
               Stat.UNIQUE_STOPS, Stat.BEST_FRIENDS]
    }


class StatCategoryBattles(_StatCategory):
    name = "battles"
    stats = {
        None: [Stat.TOTAL_BATTLES_WON],
        "raids": [Stat.NORMAL_RAIDS_WON, Stat.LEGENDARY_RAIDS_WON,
                  Stat.FRIEND_RAIDS, Stat.RAID_ACHIEVEMENTS, Stat.UNIQUE_RAIDS],
        "pvp": [Stat.GBL_RANK, Stat.GBL_RATING, Stat.GREAT_WON, Stat.ULTRA_WON,
                Stat.MASTER_WON, Stat.TRAININGS_WON],
        "team_rocket": [Stat.GRUNTS, Stat.GIOVANNI, Stat.PURIFIED],
        "gyms": [Stat.GYM_BATTLES_WON, Stat.HOURS_DEFENDED, Stat.BERRIES_FED]
    }


class StatCategoryCollection(_StatCategory):
    name = "collection"
    stats = {
        "dex": [Stat.DEX_1, Stat.DEX_2, Stat.DEX_3, Stat.DEX_4, Stat.DEX_5,
                Stat.DEX_6, Stat.DEX_7, Stat.DEX_8],
        "specific": [Stat.UNIQUE_UNOWN, Stat.XL_KARPS, Stat.XS_RATS, Stat.PIKACHU],
        "types": [Stat.NORMAL, Stat.FIGHTING, Stat.FLYING, Stat.POISON, Stat.GROUND,
                  Stat.ROCK, Stat.BUG, Stat.GHOST, Stat.STEEL, Stat.FIRE, Stat.WATER,
                  Stat.GRASS, Stat.ELECTRIC, Stat.PSYCHIC, Stat.ICE, Stat.DRAGON,
                  Stat.DARK, Stat.FAIRY]
    }


class StatCategoryMisc(_StatCategory):
    name = "misc"
    stats = {
        None: [Stat.COLLECTIONS, Stat.TRADE_KM, Stat.BEST_BUDDIES, Stat.MEGA_EVOS,
               Stat.UNIQUE_MEGA_EVOS, Stat.STREAKS, Stat.LURE_CAUGHT, Stat.WAYFARER,
               Stat.REFERRED, Stat.PHOTOBOMBS]
    }


class StatSelect(discord.ui.Select):
    def __init__(self, view: StatView):
        self.stat_view = view
        self.categories: Dict[str, _StatCategory] = {}

        super().__init__(custom_id="stats", placeholder=tb.translate("stats_placeholder"), min_values=0, max_values=1)

        for i, category in enumerate([StatCategoryGeneral, StatCategoryBattles, StatCategoryCollection,
                                      StatCategoryMisc]):
            category = category()
            if i == 0:
                category.default = True

            self.categories[category.id] = category
            self.options.append(category)

    async def callback(self, interaction: discord.Interaction):
        if self.stat_view.author_id != interaction.user.id:
            return
        category = self.categories[self.values[0]]
        embed = self.stat_view.get_embed(category)
        for option in self.options:
            if option.value == self.values[0]:
                option.default = True
            else:
                option.default = False
        await interaction.response.edit_message(embed=embed, view=self.stat_view)


class StatView(discord.ui.View):
    def __init__(self, player: Player, author_id: int):
        super().__init__()
        self.player = player
        self.author_id = author_id
        self.stat_select = StatSelect(self)
        self.add_item(self.stat_select)

    def _stat_text(self, stat_enum: Badge):
        stat_id = stat_enum.value
        stat_value = self.player.stats.get(stat_id)
        if not stat_value:
            return ""
        stat_name = tb.translate("stats_" + stat_id)
        stat_emoji = stat_enum.get_tier_prefix(stat_value)
        stat_suffix = stat_enum.next_target(stat_value)
        return f"{stat_emoji}{stat_name}: **{stat_value:,}**{stat_suffix}\n".replace(",", tb.translate("dot"))

    def _base_embed(self):
        embed = discord.Embed()
        embed.title = tb.translate("stats_title").format(self.player.ign)
        embed.colour = TEAM_COLORS[self.player.team.value]
        embed.set_thumbnail(url=f"https://raw.githubusercontent.com/whitewillem/PogoAssets/main/uicons/team/"
                                f"{self.player.team.value}.png")
        updated = arrow.get(self.player.updated)
        updated = updated.to("local")
        time_diff = time.time() - updated.timestamp()
        hours, minutes = time_diff // 3600, time_diff % 3600 // 60
        embed.set_footer(text=tb.translate("stats_last_seen").format(f"{int(hours)}h {int(minutes)}m"))
        return embed

    def get_gym_embed(self):
        embed = self._base_embed()
        embed.description = ""
        for stat in [Stat.XP, Stat.CAUGHT_POKEMON, Stat.TOTAL_BATTLES_WON]:
            embed.description += self._stat_text(stat)
        return embed

    def get_embed(self, category: _StatCategory):
        embed = self._base_embed()
        for title, stat_list in category.stats.items():
            text = ""
            for stat_enum in stat_list:
                text += self._stat_text(stat_enum)

            if title is None:
                embed.description = text
            else:
                title = tb.translate("stats_title_" + title)
                embed.add_field(name=title, value=text, inline=False)
        return embed

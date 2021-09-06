from __future__ import annotations
from typing import Optional, Dict, List, Union
from enum import Enum

import discord
from discord.ext import commands

from taubsi.taubsi_objects import tb
from taubsi.cogs.playerstats.errors import *
from taubsi.utils.enums import Team
from config.emotes import TEAM_COLORS


class Stat(Enum):
    XP = "xp"
    KM_WALKED = "km_walked"
    CAUGHT_POKEMON = "caught_pokemon"
    STOPS = "stops_spun"
    EVOLVED = "evolved"
    HATCHED = "hatched"
    QUESTS = "quests"
    TRADES = "trades"
    UNIQUE_STOPS = "unique_stops_spun"
    BEST_FRIENDS = "best_friends"

    TOTAL_BATTLES_WON = "battles_won"
    NORMAL_RAIDS_WON = "normal_raids_won"
    LEGENDARY_RAIDS_WON = "legendary_raids_won"
    FRIEND_RAIDS = "raids_with_friends"
    RAID_ACHIEVEMENTS = "raid_achievements"
    UNIQUE_RAIDS = "unique_raid_bosses"
    GRUNTS = "grunts_defeated"
    GIOVANNI = "giovanni_defeated"
    PURIFIED = "purified"
    GYM_BATTLES_WON = "gym_battles_won"
    BERRIES_FED = "berries_fed"
    HOURS_DEFENDED = "hours_defended"
    TRAININGS_WON = "trainings_won"
    GREAT_WON = "league_great_won"
    ULTRA_WON = "league_ultra_won"
    MASTER_WON = "league_master_won"
    GBL_RANK = "gbl_rank"
    GBL_RATING = "gbl_rating"

    BEST_BUDDIES = "best_buddies"
    MEGA_EVOS = "mega_evos"
    COLLECTIONS = "collections_done"
    UNIQUE_MEGA_EVOS = "unique_mega_evos"
    STREAKS = "7_day_streaks"
    TRADE_KM = "trade_km"
    LURE_CAUGHT = "caught_at_lure"
    WAYFARER = "wayfarer_agreements"
    REFERRED = "trainers_referred"
    PHOTOBOMBS = "photobombs"

    UNIQUE_UNOWN = "unique_unown"
    XL_KARPS = "xl_karps"
    XS_RATS = "xs_rats"
    PIKACHU = "pikachu_caught"
    DEX_1 = "dex_gen1"
    DEX_2 = "dex_gen2"
    DEX_3 = "dex_gen3"
    DEX_4 = "dex_gen4"
    DEX_5 = "dex_gen5"
    DEX_6 = "dex_gen6"
    DEX_7 = "dex_gen7"
    DEX_8 = "dex_gen8"
    NORMAL = "caught_normal"
    FIGHTING = "caught_fighting"
    FLYING = "caught_flying"
    POISON = "caught_poison"
    GROUND = "caught_ground"
    ROCK = "caught_rock"
    BUG = "caught_bug"
    GHOST = "caught_ghost"
    STEEL = "caught_steel"
    FIRE = "caught_fire"
    WATER = "caught_water"
    GRASS = "caught_grass"
    ELECTRIC = "caught_electric"
    PSYCHIC = "caught_psychic"
    ICE = "caught_ice"
    DRAGON = "caught_dragon"
    DARK = "caught_dark"
    FAIRY = "caught_fairy"


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
    stats: Dict[str, int]

    def __init__(self, ign, user):
        self.ign = ign
        self.user = user

    async def get_stats(self):
        fetch_stats = ",".join([s.value for s in Stat])
        result = await tb.queries.execute(
            "SELECT team, level, {} "
            "FROM cev_trainer "
            "WHERE name = '{}'".format(fetch_stats, self.ign),
            as_dict=True
        )
        self.stats = result[0]

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
            user_id = await tb.intern_queries.execute(f"SELECT user_id FROM users WHERE ingame_name = '{player}'")
            if not user_id:
                raise PlayerNotLinked
            user_id = user_id[0][0]
            ign = player
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

    def _stat_text(self, stat_enum: Stat):
        stat_id = stat_enum.value
        stat_name = tb.translate("stats_" + stat_id)
        stat_value = self.player.stats.get(stat_id)
        if not stat_value:
            return ""
        return f"{stat_name}: **{stat_value:,}**\n".replace(",", tb.translate("dot"))

    def _base_embed(self):
        embed = discord.Embed()
        embed.title = tb.translate("stats_title").format(self.player.ign)
        embed.colour = TEAM_COLORS[self.player.team.value]
        embed.set_thumbnail(url=f"https://raw.githubusercontent.com/whitewillem/PogoAssets/main/uicons/team/"
                                f"{self.player.team.value}.png")
        return embed

    def get_gym_embed(self):
        embed = self._base_embed()
        embed.description = ""
        for stat in [Stat.XP, Stat.CAUGHT_POKEMON, Stat.TOTAL_BATTLES_WON]:
            embed.description += self._stat_text(stat)

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

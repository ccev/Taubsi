from __future__ import annotations
from typing import List, Dict, TYPE_CHECKING

import arrow
import discord

from taubsi.cogs.playerstats.objects import Player, LinkAdButton, DataLevel
from taubsi.core import bot, Stat, Badge


class _StatCategory(discord.SelectOption):
    name: str
    id: str
    stats: Dict[str, List[Badge]]

    def __init__(self):
        self.id = self.name
        lang_key = "stats_category_" + self.name
        self.name = bot.translate(lang_key)
        desc = bot.translate(lang_key + "_desc")

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

        super().__init__(custom_id="stats_select", placeholder=bot.translate("stats_placeholder"),
                         min_values=0, max_values=1)

        for category in [StatCategoryGeneral, StatCategoryBattles, StatCategoryCollection,
                         StatCategoryMisc]:
            category = category()

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

        if self.player.data_level.value < DataLevel.FRIEND.value:
            self.add_item(LinkAdButton())
        else:
            self.stat_select = StatSelect(self)
            self.add_item(self.stat_select)

    def _stat_text(self, stat_enum: Badge, badge_levels=False):
        stat_id = stat_enum.value
        stat_value = self.player.stats.get(stat_id)
        if not stat_value:
            return ""
        stat_name = bot.translate("stats_" + stat_id)
        if badge_levels:
            stat_emoji = stat_enum.get_tier_prefix(stat_value)
            stat_suffix = stat_enum.next_target(stat_value)
        else:
            stat_emoji = ""
            stat_suffix = ""
        return f"{stat_emoji}{stat_name}: **{stat_value:,}**{stat_suffix}\n".replace(",", tb.translate("dot"))

    def _base_embed(self):
        embed = discord.Embed()
        embed.title = bot.translate("stats_title").format(self.player.ign)
        embed.colour = bot.config.TEAM_COLORS[self.player.team.value]
        embed.set_thumbnail(url=f"https://raw.githubusercontent.com/whitewillem/PogoAssets/main/uicons/team/"
                                f"{self.player.team.value}.png")

        time_diff = arrow.now() - self.player.updated
        seconds, days = time_diff.seconds, time_diff.days
        hours, minutes = int(seconds // 3600), int(seconds % 3600 // 60)

        days_str = bot.translate("days")
        hours_str = bot.translate("hours")
        minutes_str = bot.translate("minutes")

        if days:
            last_updated = f"{days} {days_str}, {hours} {hours_str}"
        elif hours:
            last_updated = f"{hours} {hours_str}, {minutes} {minutes_str}"
        else:
            last_updated = f"{minutes} {minutes_str}"
        embed.set_footer(text=bot.translate("stats_last_seen").format(last_updated))
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
                text += self._stat_text(stat_enum, badge_levels=True)

            if title is None:
                embed.description = text
            else:
                title = bot.translate("stats_title_" + title)
                embed.add_field(name=title, value=text, inline=False)
        return embed

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

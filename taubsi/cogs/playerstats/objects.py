from __future__ import annotations
from typing import Dict, Union
from enum import Enum
import arrow

import discord
from discord.ext import commands

from taubsi.cogs.playerstats.errors import *
from taubsi.core import bot, Team
from taubsi.corgs.playerstats.objects import Badge, Stat


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

    @classmethod
    async def from_context(cls, member: discord.Member):
        ign = await bot.taubsi_db.execute(f"SELECT ingame_name FROM users WHERE user_id = {member.id}",
                                          as_dict=False)
        if not ign or not ign[0] or not ign[0][0]:
            raise UserNotLinked
        ign = ign[0][0]

        player_ = cls(ign, member)
        await player_.get_stats()
        return player_

    @classmethod
    async def from_command(cls, player, ctx: commands.Context):
        if isinstance(player, discord.Member):
            ign = await bot.taubsi_db.execute(f"SELECT ingame_name FROM users WHERE user_id = {player.id}",
                                              as_dict=False)
            if not ign or not ign[0] or not ign[0][0]:
                if player.id == ctx.author.id:
                    raise SelfNotLinked
                raise UserNotLinked
            ign = ign[0][0]
        else:
            if any(not c.isalnum() for c in player):
                raise PlayerNotLinked
            result = await bot.taubsi_db.execute(f"SELECT user_id, ingame_name FROM users "
                                                 f"WHERE ingame_name = '{player}'", as_dict=False)
            if not result:
                raise PlayerNotLinked
            user_id = result[0][0]
            ign = result[0][1]
            player = await ctx.guild.fetch_member(int(user_id))

        player_ = cls(ign, player)
        await player_.get_stats()
        return player_

    async def get_stats(self):
        fetch_stats = ",".join([s.value for s in Stat.__dict__.values() if isinstance(s, Badge)])
        result = await bot.mad_db.execute(
            "SELECT team, level, last_seen, {} "
            "FROM cev_trainer "
            "WHERE name = '{}'".format(fetch_stats, self.ign)
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


class LinkAdButton(discord.ui.Button):
    def __init__(self, row: int = 0):
        super().__init__(style=discord.ButtonStyle.blurple,
                         label=bot.translate("link_ad_label"),
                         row=row)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(ephemeral=True, content=bot.translate("link_ad_text"))

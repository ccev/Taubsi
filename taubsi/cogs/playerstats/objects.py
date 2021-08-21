from typing import Optional
from enum import Enum

import discord

from taubsi.taubsi_objects import tb
from taubsi.cogs.playerstats.errors import *


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

    xp: Optional[int]
    battles_won: Optional[int]
    km_walked: Optional[float]
    caught_mons: Optional[int]
    stops_spun: Optional[int]

    def __init__(self, ign, user):
        self.ign = ign
        self.user = user

    async def get_stats(self):
        result = await tb.queries.execute(
            "SELECT xp, battles_won, km_walked, caught_pokemon, stops_spun "
            "FROM cev_trainer "
            "WHERE name = '{}'".format(self.ign)
        )
        self.xp, self.battles_won, self.km_walked, self.caught_mons, self.stops_spun = result[0]

        if self.stops_spun:
            self.data_level = DataLevel.FRIEND
        elif self.caught_mons:
            self.data_level = DataLevel.RAID
        elif self.xp:
            self.data_level = DataLevel.GYM
        else:
            self.data_level = DataLevel.TAUBSI

    def make_text(self):
        return (
            f"XP: {self.xp}\n"
            f"Gedrehte Stops: {self.stops_spun}"
        )

    @classmethod
    async def from_command(cls, player, guild: discord.Guild):
        print(type(player))
        if isinstance(player, discord.Member):
            ign = await tb.intern_queries.execute(f"SELECT ingame_name FROM users WHERE user_id = {player.id}")
            if not ign:
                raise UserNotLinked
            ign = ign[0][0]
        else:
            user_id = await tb.intern_queries.execute(f"SELECT user_id FROM users WHERE ingame_name = '{player}'")
            if not user_id:
                raise UserNotLinked
            user_id = user_id[0][0]
            ign = player
            player = await guild.fetch_member(int(user_id))

        player_ = cls(ign, player)
        await player_.get_stats()
        return player_

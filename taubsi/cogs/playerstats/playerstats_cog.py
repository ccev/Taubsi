from typing import Optional, Union

import discord
from discord.ext import commands

from taubsi.utils.logging import logging
from taubsi.taubsi_objects import tb
from taubsi.cogs.setup.objects import TaubsiUser
from taubsi.utils.checks import is_guild
from taubsi.cogs.setup.errors import *
from taubsi.utils.enums import Team
from taubsi.cogs.playerstats.stats import StatView
from taubsi.cogs.playerstats.objects import Player, DataLevel
from taubsi.cogs.playerstats.leaderboard import LeaderboardView
from taubsi.cogs.playerstats.errors import *
from taubsi.utils.errors import command_error


log = logging.getLogger("PlayerStats")


class PlayerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        if not isinstance(error, TaubsiError):
            log.exception(error)
            return
        await command_error(ctx.message, error.__doc__, False)

    @commands.command()
    @commands.check(is_guild)
    async def link(self, ctx, *, name):
        if any(not c.isalnum() for c in name):
            raise NameNotFound
        ingame = await tb.queries.execute(f"select name, team, level from cev_trainer "
                                          f"where name = %s;", args=name)
        if len(ingame) == 0:
            raise NameNotFound

        embed = discord.Embed(description=f"✅ Du bist nun mit dem Pokémon GO Account {name} verbunden", color=3092790)
        await ctx.send(embed=embed)

        user = TaubsiUser()
        await user.from_command(ctx.author)
        user.team, user.level = Team(ingame[0][1]), ingame[0][2]
        await user.update()

        name = ingame[0][0]
        keyvals = {
            "user_id": ctx.author.id,
            "ingame_name": name
        }
        await tb.intern_queries.insert("users", keyvals)

    @commands.command(aliases=["lb"])
    @commands.check(is_guild)
    async def leaderboard(self, ctx):
        view = LeaderboardView(ctx.author.id)
        await view.prepare()
        await ctx.send(embed=view.embed, view=view)
        return
        players = await tb.queries.execute(
            "select t.name, t.xp from taubsi3.users u "
            "left join mad.cev_trainer t on u.ingame_name = t.name "
            "where ingame_name is not null order by xp desc limit 10;")
        text = ""
        for rank, (name, xp) in enumerate(players, start=1):
            text += (str(rank) + ". " + name).ljust(25) + "{:,}".format(xp).replace(",", ".") + " XP\n"
        await ctx.send(f"```\n{text}```")

    @commands.command(aliases=["s"])
    @commands.check(is_guild)
    async def stats(self, ctx: commands.Context, player: Optional[Union[discord.Member, str]]):
        if not player:
            player = ctx.author
        player = await Player.from_command(player, ctx)
        view = StatView(player, ctx.author.id)
        if player.data_level.value >= DataLevel.FRIEND.value:
            embed = view.get_embed(list(view.stat_select.categories.values())[0])
            await ctx.send(embed=embed, view=view)
            return
        elif player.data_level.value >= DataLevel.GYM.value:
            embed = view.get_gym_embed()
            await ctx.send(embed=embed)
            return


def setup(bot):
    bot.add_cog(PlayerStats(bot))

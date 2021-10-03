from typing import Optional, Union, TYPE_CHECKING

import discord
from discord.ext import commands

from taubsi.cogs.playerstats.errors import *
from taubsi.cogs.playerstats.objects import Player
from taubsi.cogs.playerstats.playerstats_commands import PlayerstatsCommands
from taubsi.cogs.playerstats.stats import StatView
from taubsi.cogs.setup.errors import *
from taubsi.core import log
from taubsi.utils.checks import is_guild
from taubsi.utils.errors import command_error

if TYPE_CHECKING:
    from taubsi.core import TaubsiBot


class PlayerStats(commands.Cog):
    def __init__(self, bot):
        self.bot: TaubsiBot = bot

    async def cog_command_error(self, ctx, error):
        if not isinstance(error, TaubsiError):
            log.exception(error)
            return
        await command_error(self.bot, ctx.message, error.__doc__, False)

    @commands.command()
    @commands.check(is_guild)
    async def link(self, ctx, *, name=None):
        if not name:
            raise MissingName
        if any(not c.isalnum() for c in name):
            raise NameNotFound

        await PlayerstatsCommands.link(name, ctx.author, ctx.send)

    @commands.command()
    @commands.check(is_guild)
    async def unlink(self, ctx):
        await PlayerstatsCommands.unlink(ctx.author.id, ctx.send)

    @commands.command(aliases=["lb"])
    @commands.check(is_guild)
    async def leaderboard(self, ctx):
        await PlayerstatsCommands.leaderboard(ctx.author.id, ctx.send)

    @commands.command(aliases=["s"])
    @commands.check(is_guild)
    async def stats(self, ctx: commands.Context, player: Optional[Union[discord.Member, str]]):
        if not player:
            player = ctx.author

        player = await Player.from_command(player, ctx)
        view = StatView(player, ctx.author.id)

        await PlayerstatsCommands.stats(player, view, ctx.send)


def setup(bot):
    bot.add_cog(PlayerStats(bot))

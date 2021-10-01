from typing import Optional, Union, TYPE_CHECKING

import discord
from discord.ext import commands

from taubsi.core import log
from taubsi.utils.checks import is_guild
from taubsi.cogs.setup.errors import *
from taubsi.cogs.playerstats.stats import StatView
from taubsi.cogs.playerstats.objects import Player, DataLevel
from taubsi.cogs.playerstats.leaderboard import LeaderboardView
from taubsi.cogs.playerstats.link import LinkView
from taubsi.cogs.playerstats.errors import *
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
        ingame = await self.bot.mad_db.execute(f"select name, team, level from cev_trainer "
                                               f"where name = %s;", args=name, as_dict=False)
        if len(ingame) == 0:
            raise NameNotFound

        embed = discord.Embed(
            title=self.bot.translate("link_title"),
            description=self.bot.translate("link_terms")
        )
        view = LinkView(ctx.author, ingame)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @commands.command()
    @commands.check(is_guild)
    async def unlink(self, ctx):
        embed = discord.Embed(description=self.bot.translate("unlink"), color=3092790)
        await self.bot.taubsi_db.execute(f"update users set ingame_name = NULL where user_id = {ctx.author.id}",
                                         commit=True)
        await ctx.send(embed=embed)

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
            await ctx.send(embed=embed, view=view)
            return


def setup(bot):
    bot.add_cog(PlayerStats(bot))

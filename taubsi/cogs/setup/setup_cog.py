from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from taubsi.cogs.setup.errors import *
from taubsi.cogs.setup.objects import TaubsiUser
from taubsi.core import log, Team
from taubsi.utils.checks import is_guild
from taubsi.utils.errors import command_error, TaubsiError
from taubsi.cogs.setup.setup_commands import SetupCommands

if TYPE_CHECKING:
    from taubsi.core import TaubsiBot


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot: TaubsiBot = bot
        self.setup_commands = SetupCommands()

    async def cog_command_error(self, ctx, error):
        if not isinstance(error, TaubsiError):
            log.exception(error)
            return
        await command_error(ctx.send, error.__doc__, False)

    @commands.command(aliases=["lvl", "l"])
    @commands.check(is_guild)
    async def level(self, ctx, level: int):
        await self.setup_commands.level(level, ctx.author, ctx.send)

    @commands.command(aliases=["lvlup", "up"])
    @commands.check(is_guild)
    async def levelup(self, ctx):
        await self.setup_commands.levelup(ctx.author, ctx.send)

    @commands.command(aliases=["n"])
    @commands.check(is_guild)
    async def name(self, ctx, *, name):
        await self.setup_commands.name(name, ctx.author, ctx.send)

    @commands.command(aliases=["code", "freund"])
    @commands.check(is_guild)
    async def trainercode(self, ctx, *, arg=None):
        return
        member = None
        try:
            member = await commands.MemberConverter().convert(ctx, arg)
        except commands.CommandError:
            member = ctx.author
        
        user = TaubsiUser()
        await user.from_member(member)

        if member or arg is None:
            if not user.friendcode:
                raise NoCodeSet
            await ctx.send(f"`{user.friendcode}`")

        else:
            if isinstance(arg, str):
                try:
                    arg = int(arg.replace(" ", ""))
                except:
                    raise WrongCodeFormat
            user = TaubsiUser()
            await user.from_member(ctx.author)
            user.friendcode = int(arg)
            await user.update()
            await self.response(ctx, self.bot.translate("tb_saved_code"))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id not in self.bot.team_choose_ids:
            return
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = message.guild.get_member(payload.user_id)
        user = TaubsiUser()
        await user.from_member(member)
        user.team = self.setup_commands.team_aliases(payload.emoji.name)
        await user.update()
    
    @commands.command()
    @commands.check(is_guild)
    async def team(self, ctx, team_name):
        await self.setup_commands.team(team_name, ctx.author, ctx.send)

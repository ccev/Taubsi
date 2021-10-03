from typing import Callable

import discord
from discord.application_commands import ApplicationCommand, option

from taubsi.cogs.setup.errors import *
from taubsi.cogs.setup.objects import TaubsiUser
from taubsi.core import bot, Team


class SetupCommands:
    max_level = 50

    def _check_level(self, level):
        if level > self.max_level:
            raise LevelTooHigh
        if level <= 1:
            raise LevelTooSmall

    @staticmethod
    async def _response(send: Callable, text):
        embed = discord.Embed(description=text, color=3092790)
        await send(embed=embed)

    @staticmethod
    def team_aliases(team_name):
        aliases = {
            Team(1): ["mystic", "blau", "weisheit", "team_blau"],
            Team(2): ["valor", "rot", "wagemut", "team_rot"],
            Team(3): ["instinct", "gelb", "intuition", "team_gelb"]
        }
        for enum, alias in aliases.items():
            if [name for name in alias if name in team_name.lower()]:
                return enum
        return Team(0)

    async def name(self, name: str, member: discord.Member, send: Callable):
        await self._response(send, bot.translate("setup_name").format(name))
        user = TaubsiUser()
        await user.from_member(member)
        user.name = name
        await user.update()

    async def level(self, level: int, member: discord.Member, send: Callable):
        self._check_level(level)
        await self._response(send, bot.translate("setup_set_level").format(level))
        user = TaubsiUser()
        await user.from_member(member)
        user.level = level
        await user.update()

    async def levelup(self, member: discord.Member, send: Callable):
        user = TaubsiUser()
        await user.from_member(member)

        level = user.level + 1
        self._check_level(level)
        await self._response(send, bot.translate("setup_level_up").format(level))

        user.level = level
        await user.update()

    async def team(self, team_name: str, member: discord.Member, send: Callable):
        user = TaubsiUser()
        await user.from_member(member)
        team = self.team_aliases(team_name)
        if team.value == 0:
            raise NoTeam
        user.team = team
        await user.update()
        await self._response(send, bot.translate("setup_team").format(team.name.lower().capitalize()))


class NameCommand(ApplicationCommand, name="name"):
    """Setze deinen Discord Namen"""
    name: str = option(description="Dein Name", required=True)

    async def callback(self, interaction: discord.Interaction):
        await SetupCommands().name(self.name, interaction.user, interaction.response.send_message)


class LevelCommand(ApplicationCommand, name="level"):
    """Setze dein Trainerlevel"""
    level: int = option(description="Dein Level", required=True)

    async def callback(self, interaction: discord.Interaction):
        await SetupCommands().level(self.level, interaction.user, interaction.response.send_message)


class LevelUpCommand(ApplicationCommand, name="levelup"):
    """Erhöhe dein Trainerlevel um 1"""

    async def callback(self, interaction: discord.Interaction):
        await SetupCommands().levelup(interaction.user, interaction.response.send_message)


class TeamCommand(ApplicationCommand, name="team"):
    """Setze dein Team"""
    team: str = option(description="Dein Team", required=True)

    async def callback(self, interaction: discord.Interaction):
        await SetupCommands().team(self.team, interaction.user, interaction.response.send_message)

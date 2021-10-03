from typing import Callable, Optional

import discord
from discord.application_commands import ApplicationCommand, option, UserCommand

from taubsi.cogs.playerstats.leaderboard import LeaderboardView
from taubsi.cogs.playerstats.link import LinkView
from taubsi.cogs.playerstats.objects import Player
from taubsi.cogs.playerstats.stats import StatView, DataLevel
from taubsi.cogs.setup.errors import NameNotFound
from taubsi.core import bot
from taubsi.utils.errors import TaubsiError


class PlayerstatsCommands:
    @staticmethod
    async def stats(player: Player, view: StatView, send: Callable, **send_kwargs):
        if player.data_level.value >= DataLevel.FRIEND.value:
            embed = view.get_embed(list(view.stat_select.categories.values())[0])
            await send(embed=embed, view=view, **send_kwargs)
            return
        elif player.data_level.value >= DataLevel.GYM.value:
            embed = view.get_gym_embed()
            await send(embed=embed, view=view, **send_kwargs)
            return

    @staticmethod
    async def link(name: str, user: discord.User, send: Callable, channel: Optional[discord.TextChannel] = None):
        ingame = await bot.mad_db.execute(f"select name, team, level from cev_trainer "
                                          f"where name = %s;", args=name, as_dict=False)
        if len(ingame) == 0:
            raise NameNotFound

        embed = discord.Embed(
            title=bot.translate("link_title"),
            description=bot.translate("link_terms")
        )
        view = LinkView(user, ingame)
        message = await send(embed=embed, view=view)
        if message:
            view.message = message
        else:
            async for message in channel.history(limit=5):
                if message.author.id == bot.user.id:
                    view.message = message
                    return

    @staticmethod
    async def unlink(user_id: int, send: Callable):
        embed = discord.Embed(description=bot.translate("unlink"), color=3092790)
        await bot.taubsi_db.execute(f"update users set ingame_name = NULL where user_id = {user_id}",
                                    commit=True)
        await send(embed=embed)

    @staticmethod
    async def leaderboard(user_id: int, send: Callable):
        view = LeaderboardView(user_id)
        await view.prepare()
        await send(embed=view.embed, view=view)


async def stats_callback(interaction: discord.Interaction, member: discord.Member, ephemeral: bool):
    try:
        player = await Player.from_app(member, interaction.user.id)
    except TaubsiError:
        # TODO proper error handling
        await interaction.response.send_message("User nicht gelinkt", ephemeral=ephemeral)
        return
    view = StatView(player, interaction.user.id)

    await PlayerstatsCommands.stats(player, view, interaction.response.send_message, ephemeral=ephemeral)


class StatContext(UserCommand, name="Stats"):
    """Zeige die Stats von diesem Spieler"""

    async def callback(self, interaction: discord.Interaction):
        await stats_callback(interaction, interaction.target, ephemeral=True)


class StatsCommand(ApplicationCommand, name="stats"):
    """Zeige die Stats von einem Spieler"""
    spieler: discord.Member = option(description="Der Spieler. Leer lassen um deine eigenen Stats zu zeigen")

    async def callback(self, interaction: discord.Interaction):
        if not self.spieler:
            self.spieler = interaction.user
        await stats_callback(interaction, self.spieler, ephemeral=False)


class LinkCommand(ApplicationCommand, name="link"):
    """Linke dich mit einem Pokémon GO Account"""
    name: str = option(description="Dein Trainername", required=True)

    async def callback(self, interaction: discord.Interaction):
        await PlayerstatsCommands.link(self.name, interaction.user, interaction.response.send_message, channel=interaction.channel)


class UnlinkCommand(ApplicationCommand, name="unlink"):
    """Unlinke dich von deinem Pokémon GO Account"""

    async def callback(self, interaction: discord.Interaction):
        await PlayerstatsCommands.unlink(interaction.user.id, interaction.response.send_message)


class LeaderboardCommand(ApplicationCommand, name="leaderboard"):
    """Zeige eine Rangliste mit allen gelinkten Spielern"""

    async def callback(self, interaction: discord.Interaction):
        await PlayerstatsCommands.leaderboard(interaction.user.id, interaction.response.send_message)

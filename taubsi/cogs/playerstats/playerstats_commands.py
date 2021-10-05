from typing import Callable, Optional

import discord
from discord.application_commands import ApplicationCommand, option, UserCommand

from taubsi.cogs.playerstats.leaderboard import LeaderboardView
from taubsi.cogs.playerstats.link import LinkView
from taubsi.cogs.playerstats.objects import Player
from taubsi.cogs.playerstats.stats import StatView, DataLevel
from taubsi.cogs.setup.errors import NameNotFound
from taubsi.core import bot


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
    async def link(name: str, user: discord.User, send: Callable, interaction: Optional[discord.Interaction] = None):
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
            view.message = await interaction.original_message()

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
    player = await Player.from_app(member, interaction.user.id)
    view = StatView(player, interaction.user.id)

    await PlayerstatsCommands.stats(player, view, interaction.response.send_message, ephemeral=ephemeral)


class StatContext(UserCommand, name="Stats", description=bot.translate("context_stats_desc")):
    async def callback(self, interaction: discord.Interaction):
        await stats_callback(interaction, interaction.target, ephemeral=True)


class StatsCommand(ApplicationCommand, name="stats", description=bot.translate("command_stats_desc")):
    trainer: discord.Member = option(description=bot.translate("command_stats_trainer_desc"))

    async def callback(self, interaction: discord.Interaction):
        if not self.trainer:
            self.trainer = interaction.user
        await stats_callback(interaction, self.trainer, ephemeral=False)


class LinkCommand(ApplicationCommand, name="link", description=bot.translate("command_link_desc")):
    name: str = option(description=bot.translate("command_link_name_desc"), required=True)

    async def callback(self, interaction: discord.Interaction):
        await PlayerstatsCommands.link(self.name, interaction.user, interaction.response.send_message,
                                       interaction=interaction)


class UnlinkCommand(ApplicationCommand, name="unlink", description=bot.translate("command_unlink_desc")):
    async def callback(self, interaction: discord.Interaction):
        await PlayerstatsCommands.unlink(interaction.user.id, interaction.response.send_message)


class LeaderboardCommand(ApplicationCommand, name="leaderboard", description = bot.translate("command_lb_desc")):
    async def callback(self, interaction: discord.Interaction):
        await PlayerstatsCommands.leaderboard(interaction.user.id, interaction.response.send_message)

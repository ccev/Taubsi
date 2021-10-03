import discord
from discord.application_commands import ApplicationCommand, option, UserCommand

from taubsi.core import bot
from taubsi.cogs.playerstats.objects import Player
from taubsi.cogs.playerstats.stats import StatView, DataLevel
from taubsi.cogs.playerstats.errors import PlayerNotLinked


class StatContext(UserCommand, name="Stats"):
    """Zeige die Stats von diesem Spieler"""

    async def callback(self, interaction: discord.Interaction):
        member: discord.Member = interaction.target

        try:
            player = await Player.from_context(member)
        except PlayerNotLinked:
            await interaction.response.send_message("User nicht gelinkt", ephemeral=True)
            return
        view = StatView(player, interaction.user.id)
        if player.data_level.value >= DataLevel.FRIEND.value:
            embed = view.get_embed(list(view.stat_select.categories.values())[0])
            await interaction.response.send_message(embed=embed, view=view)
            return
        elif player.data_level.value >= DataLevel.GYM.value:
            embed = view.get_gym_embed()
            await interaction.response.send_message(embed=embed, view=view)
            return

import discord
from discord.application_commands import ApplicationCommand, option

from taubsi.core import bot, Server
from taubsi.utils.matcher import match_gyms
from taubsi.cogs.raids.raid_cog import match_time
from taubsi.cogs.raids.raidmessage import RaidMessage


class RaidCommand(ApplicationCommand, name="raid"):
    """Setze einen Raid an"""
    arena = option(description="Die Arena", required=True)
    zeit: str = option(description="Wann der Raid gespielt werden soll", required=True)

    def __init__(self):
        raid_cog = bot.get_cog("RaidCog")
        self.create_raid = raid_cog.create_raid

    @staticmethod
    def _get_server(guild_id: int) -> Server:
        server = None
        for possible_server in bot.servers:
            if possible_server.id == guild_id:
                server = possible_server
                break
        if not server:
            raise
        return server

    @arena.autocomplete
    async def gym_autocomplete(self, interaction: discord.Interaction):
        server = self._get_server(interaction.guild_id)
        matched_gyms = match_gyms(server.gyms, interaction.value, score_cutoff=0)
        for gym, _ in matched_gyms:
            yield gym.name

    async def callback(self, interaction: discord.Interaction):
        time = match_time(self.zeit)
        time = time[0]

        if not time:
            await interaction.response.send_message("Dem konnte ich keine Zeit entnehmen", ephemeral=True)
            return

        server = self._get_server(interaction.guild_id)
        gym = None
        for possible_gym in server.gyms:
            if possible_gym.name == self.arena:
                gym = possible_gym

        if not gym:
            await interaction.response.send_message("Sorry, du musst einen richtigen Arenanamen angeben",
                                                    ephemeral=True)
            return

        raidmessage = await RaidMessage.from_slash(gym, time, interaction)
        await self.create_raid(raidmessage)

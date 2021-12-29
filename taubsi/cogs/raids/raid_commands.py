import discord
from discord.application_commands import ApplicationCommand, option, ApplicationCommandOptionChoice

from taubsi.cogs.raids.errors import WrongChannel, InvalidTime, WrongGymName
from taubsi.cogs.raids.raid_cog import match_time
from taubsi.cogs.raids.raidmessage import RaidMessage
from taubsi.core import bot, Server, log
from taubsi.utils.errors import TaubsiError


class RaidCommand(ApplicationCommand, name="raid", description=bot.translate("command_raid_desc")):
    arena = option(name=bot.translate("command_raid_gym"),
                   description=bot.translate("command_raid_gym_desc"), required=True)
    zeit: str = option(name=bot.translate("command_raid_time"),
                       description=bot.translate("command_raid_time_desc"), required=True)

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
            raise TaubsiError
        return server

    @arena.autocomplete
    async def gym_autocomplete(self, interaction: discord.Interaction):
        log.info(f"User {interaction.user} is choosing a gym in the /raid command")
        server = self._get_server(interaction.guild_id)
        if not interaction.value:
            matched_gyms = [(g, 0) for g in server.gyms[:10]]
        else:
            matched_gyms = server.match_gyms(interaction.value, limit=25)

        for gym, _ in matched_gyms:
            yield ApplicationCommandOptionChoice(name=gym.name, value=gym.id)

    # possible TODO: time autocomplete based on active raids

    async def callback(self, interaction: discord.Interaction):
        if interaction.channel_id not in bot.raid_channel_dict.keys():
            raise WrongChannel
        time = match_time(self.zeit)
        time = time[0]

        if not time:
            raise InvalidTime

        server = self._get_server(interaction.guild_id)
        gym = server.gym_dict.get(self.arena)

        if not gym:
            raise WrongGymName

        raidmessage = await RaidMessage.from_slash(gym, time, interaction)
        await self.create_raid(raidmessage)

from taubsi.core import bot
from taubsi.core.config_classes import Cog
from taubsi.cogs.raids.raid_commands import RaidCommand
from taubsi.cogs.playerstats.playerstats_commands import (StatContext, StatsCommand, LinkCommand,
                                                          UnlinkCommand, LeaderboardCommand)
from taubsi.cogs.setup.setup_commands import (NameCommand, LevelCommand, LevelUpCommand, TeamCommand)
from taubsi.utils.errors import app_command_error

bot.load_cogs()

app_commands = {
    Cog.RAIDS: [RaidCommand],
    Cog.PLAYERSTATS: [StatContext, StatsCommand, LinkCommand, UnlinkCommand, LeaderboardCommand],
    Cog.SETUP: [NameCommand, LevelCommand, LevelUpCommand, TeamCommand]
}

for server in bot.servers:
    for cog, commands in app_commands.items():
        if cog not in bot.config.COGS:
            continue
        for command in commands:
            command.command_error = app_command_error
            bot.add_application_command(command=command, guild_id=server.id)

bot.run(bot.config.BOT_TOKEN)

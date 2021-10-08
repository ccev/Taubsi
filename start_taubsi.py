from taubsi.core import bot
from taubsi.core.config_classes import Cog
from taubsi.cogs.raids.raid_commands import RaidCommand
from taubsi.cogs.playerstats.playerstats_commands import (StatContext, StatsCommand, LinkCommand,
                                                          UnlinkCommand, LeaderboardCommand)
from taubsi.cogs.setup.setup_commands import (NameCommand, LevelCommand, LevelUpCommand, TeamCommand)
from taubsi.utils.errors import app_command_error

from taubsi.cogs.raids.raid_cog import RaidCog
from taubsi.cogs.setup.setup_cog import Setup
from taubsi.cogs.loops.loop import LoopCog
from taubsi.cogs.raid_info.info_cog import InfoCog
from taubsi.cogs.dmap.dmap_cog import DMapCog
from taubsi.cogs.auto_setup.auto_setup_cog import AutoSetupCog
from taubsi.cogs.playerstats.playerstats_cog import PlayerStats
from taubsi.cogs.articlepreview.preview_cog import PreviewCog


bot.cog_dict = {
    Cog.RAIDS: RaidCog,
    Cog.SETUP: Setup,
    Cog.MAIN_LOOPS: LoopCog,
    Cog.RAIDINFO: InfoCog,
    Cog.DMAP: DMapCog,
    Cog.AUTOSETUP: AutoSetupCog,
    Cog.PLAYERSTATS: PlayerStats,
    Cog.ARTICLEPREVIEW: PreviewCog
}

for cog_enum, cog_class in bot.cog_dict.items():
    if cog_enum not in bot.config.COGS:
        continue
    cog = cog_class(bot)
    bot.add_cog(cog)
    bot.cog_dict[cog_enum] = cog

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

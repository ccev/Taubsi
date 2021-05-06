import re
from dateutil import tz

from taubsi.utils.logging import logging
from taubsi.utils.matcher import get_matches
from taubsi.utils.errors import command_error
from taubsi.taubsi_objects import tb
from taubsi.cogs.raids.emotes import NUMBER_EMOJIS, CONTROL_EMOJIS
from taubsi.cogs.raids.raidmessage import RaidMessage, RAID_WARNINGS
from taubsi.cogs.raids.choicemessage import ChoiceMessage
from taubsi.cogs.raids.pogo import BaseRaid

import asyncio
import dateparser
import arrow
from discord.ext import tasks, commands

log = logging.getLogger("Raids")


class RaidCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_raids = {}

        

        self.info_loop.start()

    @tasks.loop(seconds=10)
    async def info_loop(self):


def setup(bot):
    bot.add_cog(RaidCog(bot))
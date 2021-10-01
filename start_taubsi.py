from discord.ext import commands
import discord

from taubsi.taubsi_objects import tb
from taubsi.utils.logging import log
from taubsi.taubsi_objects.servers import load_servers
from config.dmap_config import MESSAGES

from typing import List
from pogodata import PogoData
from taubsi.taubsi_objects.queries import Queries
from taubsi.taubsi_objects.uicons import UIconManager
from taubsi.taubsi_objects.translator import Translator
from taubsi.taubsi_objects.config_classes import Server
from taubsi.cogs.dmap.dmap_cog import PermaMap
from config import Config

extensions = [
    "taubsi.cogs.raids.raid_cog",
    "taubsi.cogs.setup.setup_cog",
    "taubsi.cogs.loop",
    "taubsi.cogs.raids.info_cog",
    "taubsi.cogs.dmap.dmap_cog"
]
startup = True


@tb.bot.event
async def on_ready():
    global startup

    if not startup:
        return
    await load_servers()
    tb.trash_channel = await tb.bot.fetch_channel(tb.config["trash_channel"])

    for message_id in MESSAGES:
        tb.bot.add_view(PermaMap(message_id), message_id=message_id)

    for extension in extensions:
        tb.bot.load_extension(extension)
    if tb.config.get("secret", False):
        tb.bot.load_extension("taubsi.cogs.setup.auto_setup_cog")
        tb.bot.load_extension("taubsi.cogs.playerstats.playerstats_cog")
        tb.bot.load_extension("taubsi.cogs.articlepreview.preview_cog")
    raidcog = tb.bot.get_cog("RaidCog")
    await raidcog.final_init()
    
    log.info("Fully loaded, ready for action")
    startup = False

tb.bot.run(tb.config["bot_token"])


class TaubsiBot(commands.Bot):
    _startup: bool = True
    config: Config
    mad_db: Queries
    taubsi_db: Queries
    uicons: UIconManager
    translate: Translator.translate
    pogodata: PogoData
    servers: List[Server]
    trash_channel: discord.TextChannel

    def __init__(self):
        intents = discord.Intents(members=True, guild_messages=True, reactions=True)
        super().__init__(command_prefix="!", case_insensitive=True, intents=intents)
        self.config = Config()
        self.mad_db = Queries(self.config, self.loop, self.config.MAD_DB_NAME)
        self.taubsi_db = Queries(self.config, self.loop, self.config.TAUBSI_DB_NAME)
        self.uicons = UIconManager()
        self.servers = self.config.SERVERS

        translator_ = Translator(self.config.LANGUAGE.value)
        self.translate = translator_.translate
        self.reload_pogodata()

        for cog in self.config.COGS:
            self.load_extension(cog.value)

    def reload_pogodata(self):
        self.pogodata = PogoData(self.config.LANGUAGE.value)

    async def on_ready(self):
        if not self._startup:
            return
        self._startup = False

        self.trash_channel = await self.fetch_channel(self.config.TRASH_CHANNEL_ID)

        log.info("Fully loaded, ready for action")

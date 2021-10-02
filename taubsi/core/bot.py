from typing import List, Dict

import discord
from discord.ext import commands
from pogodata import PogoData

from config import Config
from taubsi.core.queries import Queries
from taubsi.core.uicons import UIconManager
from taubsi.core.translator import Translator
from taubsi.core.config_classes import Server, RaidChannel
from taubsi.core.logging import log
from taubsi.core.cogs import Cog


class TaubsiBot(commands.Bot):
    _startup: bool = True
    config: Config
    mad_db: Queries
    taubsi_db: Queries
    uicons: UIconManager
    translate: Translator.translate
    pogodata: PogoData
    servers: List[Server]
    server_ids: List[int]
    team_choose_ids: List[int]
    raid_channel_dict: Dict[int, RaidChannel]
    trash_channel: discord.TextChannel

    def __init__(self):
        intents = discord.Intents(members=True, guild_messages=True, reactions=True, guilds=True)
        super().__init__(command_prefix="!", case_insensitive=True, intents=intents)
        self.config = Config()
        self.mad_db = Queries(self.config, self.loop, self.config.MAD_DB_NAME)
        self.taubsi_db = Queries(self.config, self.loop, self.config.TAUBSI_DB_NAME)
        self.uicons = UIconManager()
        self.servers = self.config.SERVERS

        self.server_ids = []
        self.team_choose_ids = []
        self.raid_channel_dict = {}
        for server in self.servers:
            self.server_ids.append(server.id)
            self.team_choose_ids += server.team_choose_ids
            for raid_channel in server.raid_channels:
                self.raid_channel_dict[raid_channel.id] = raid_channel

        translator_ = Translator(self.config.LANGUAGE.value)
        self.translate = translator_.translate
        self.reload_pogodata()

    def load_cogs(self):
        for cog in self.config.COGS:
            self.load_extension(cog.value)

    def reload_pogodata(self):
        self.pogodata = PogoData(self.config.LANGUAGE.value)

    async def on_ready(self):
        if not self._startup:
            return
        self._startup = False
        log.info("Logged in, setting up everything")

        self.trash_channel = await self.fetch_channel(self.config.TRASH_CHANNEL_ID)

        log.info("Preparing servers")
        for server in self.servers:
            await server.load(self)
            for info_channel in server.info_channels:
                info_channel.channel = await self.fetch_channel(info_channel.id)

        log.info("Preparing cogs")
        if Cog.RAIDS in self.config.COGS:
            raidcog = self.get_cog("RaidCog")
            await raidcog.final_init()

        if Cog.RAIDINFO in self.config.COGS:
            infocog = self.get_cog("InfoCog")
            infocog.final_init()

        if Cog.MAIN_LOOPS in self.config.COGS:
            loopcog = self.get_cog("LoopCog")
            loopcog.final_init()

        log.info("Fully loaded, ready for action")


bot = TaubsiBot()

from typing import List

import discord
from discord.ext import commands
from pogodata import PogoData

from config import Config
from taubsi.core.queries import Queries
from taubsi.core.uicons import UIconManager
from taubsi.core.translator import Translator
from taubsi.core.config_classes import Server
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
        for server in self.servers:
            self.server_ids.append(server.id)
            self.team_choose_ids += server.team_choose_ids

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

        for server in self.servers:
            for info_channel in server.info_channels:
                info_channel.channel = await self.fetch_channel(info_channel.id)

        if Cog.RAIDS in self.config.COGS:
            raidcog = self.get_cog("RaidCog")
            await raidcog.final_init()

        log.info("Fully loaded, ready for action")

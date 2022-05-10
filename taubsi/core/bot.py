from __future__ import annotations
from typing import List, Dict, TYPE_CHECKING

import discord
from discord.ext import commands
from taubsi.pogodata import PogoData

from config import Config
from taubsi.core.queries import Queries
from taubsi.core.uicons import UIconManager
from taubsi.core.translator import Translator
from taubsi.core.config_classes import Server, RaidChannel
from taubsi.core.logging import log
from taubsi.core.cogs import Cog
from taubsi.core.emojis import EmojiManager

if TYPE_CHECKING:
    from taubsi.pokebattler import PokeBattler


class TaubsiBot(commands.Bot):
    _startup: bool = True
    config: Config
    mad_db: Queries
    rdm_db: Queries
    taubsi_db: Queries
    uicons: UIconManager
    emoji_manager: EmojiManager
    translate: Translator.translate
    pogodata: PogoData
    pokebattler: PokeBattler
    servers: List[Server]
    server_ids: List[int]
    team_choose_ids: List[int]
    raid_channel_dict: Dict[int, RaidChannel]
    trash_channel: discord.TextChannel
    cog_dict: dict

    def __init__(self):
        intents = discord.Intents(members=True, guild_messages=True, reactions=True, guilds=True)
        super().__init__(command_prefix="!", case_insensitive=True, intents=intents,
                         update_application_commands_at_startup=True)
        self.config = Config()
        self.mad_db = Queries(self.config, self.loop, self.config.MAD_DB_NAME)
        self.taubsi_db = Queries(self.config, self.loop, self.config.TAUBSI_DB_NAME)
        self.rdm_db = Queries(self.config, self.loop, self.config.RDM_DB_NAME)
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
        self.pogodata = PogoData.make_sync(self.config.LANGUAGE.value)

    async def reload_pogodata(self):
        self.pogodata = await PogoData.make_async(self.config.LANGUAGE.value)

    async def on_ready(self):
        if not self._startup:
            return
        self._startup = False
        log.info("Logged in, setting up everything")

        self.trash_channel = await self.fetch_channel(self.config.TRASH_CHANNEL_ID)

        trash_guild = await self.fetch_guild(self.config.TRASH_GUILD_ID)
        self.emoji_manager = EmojiManager(self, trash_guild)

        from taubsi.pokebattler import PokeBattler
        self.pokebattler = PokeBattler()

        log.info("Preparing servers")
        for server in self.servers:
            await server.load(self)
            for info_channel in server.info_channels:
                info_channel.channel = await self.fetch_channel(info_channel.id)

        log.info("Preparing cogs")
        for cog_enum in [Cog.RAIDS, Cog.RAIDINFO, Cog.MAIN_LOOPS, Cog.AUTOSETUP]:
            if cog_enum not in self.config.COGS:
                continue
            cog = self.cog_dict[cog_enum]
            await cog.final_init()

        if Cog.DMAP in bot.config.COGS:
            from taubsi.cogs.dmap.dmap_cog import PermaMap
            for server in bot.config.SERVERS:
                for dmap_message in server.dmap_messages:
                    bot.add_view(PermaMap(dmap_message.id), message_id=dmap_message.id)

        log.info("Fully loaded, ready for action")


bot = TaubsiBot()

from discord.ext import commands
import discord

from taubsi.taubsi_objects import tb
from taubsi.utils.logging import log
from taubsi.taubsi_objects.servers import load_servers
from config.dmap_config import MESSAGES
from taubsi.cogs.dmap.dmap_cog import PermaMap

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
    def __init__(self):
        intents = discord.Intents(members=True, guild_messages=True, reactions=True)
        super().__init__(command_prefix="!", case_insensitive=True, intents=intents)

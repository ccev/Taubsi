from taubsi.taubsi_objects import tb
from taubsi.utils.logging import log
from taubsi.taubsi_objects.servers import load_servers

extensions = ["taubsi.cogs.raids.raid_cog", "taubsi.cogs.setup.setup_cog", "taubsi.cogs.loop"]


@tb.bot.event
async def on_ready():
    await load_servers()
    tb.trash_channel = await tb.bot.fetch_channel(tb.config["trash_channel"])
    for extension in extensions:
        tb.bot.load_extension(extension)
    raidcog = tb.bot.get_cog("RaidCog")
    await raidcog.final_init()
    
    log.info("Fully loaded, ready for action")

tb.bot.run(tb.config["bot_token"])

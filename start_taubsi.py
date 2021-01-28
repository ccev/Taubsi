from taubsi.taubsi_objects import tb
from taubsi.utils.logging import log
from taubsi.taubsi_objects.servers import load_servers

extensions = ["taubsi.cogs.raids.raids"]

@tb.bot.event
async def on_ready():
    await load_servers()
    tb.trash_channel = await tb.bot.fetch_channel(tb.config["trash_channel"])
    for extension in extensions:
        tb.bot.load_extension(extension)
    log.info("Fully loaded, ready for action")

tb.bot.run(tb.config["bot_token"])
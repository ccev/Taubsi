from taubsi.utils.logging import log
from taubsi.taubsi_objects import tb
from discord.ext import tasks, commands

class Loop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.big_loop.start()

    @tasks.loop(hours=12)   
    async def big_loop(self):
        tb.reload_pogodata()
        log.info("Reloaded PogoData")

def setup(bot):
    bot.add_cog(Loop(bot))
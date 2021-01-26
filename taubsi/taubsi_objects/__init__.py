import json
import discord
from pogodata import PogoData
from discord.ext import commands
from .servers import load_servers
from .queries import Queries

class TaubsiVars:
    def __init__(self):
        with open("config/config.json") as f:
            self.config = json.load(f)

        intents = discord.Intents.default()
        intents.reactions = True
        intents.members = True
        intents.messages = True

        self.bot = commands.Bot(command_prefix="!", case_insensitive=1, intents=intents)
        self.queries = Queries(self.config)
        self.reload_pogodata()

    def reload_pogodata(self):
        self.pogodata = PogoData("german")

    async def reload_servers(self):
        await load_servers(self)

tb = TaubsiVars()
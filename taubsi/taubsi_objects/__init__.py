import json
import discord
from pogodata import PogoData
from discord.ext import commands
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

tb = TaubsiVars()
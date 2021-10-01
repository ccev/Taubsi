from typing import Optional, Union

import discord
from discord.ext import commands

from taubsi.utils.checks import is_admin
from taubsi.cogs.dmap.map import Map


class PermaMap(discord.ui.View):
    def __init__(self, message_id: int):
        super().__init__(timeout=None)
        button = discord.ui.Button(label="Map anzeigen",
                                   style=discord.ButtonStyle.blurple,
                                   custom_id=f"pm{message_id}")
        button.callback = self.start_map
        self.add_item(button)

    @staticmethod
    async def start_map(interaction: discord.Interaction):
        dmap = Map(interaction.user.id)
        await dmap.send(interaction)


class DMapCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(slash_command=False)
    @commands.check(is_admin)
    async def permamap(self, ctx: commands.Context):
        await ctx.message.delete()
        message = await ctx.send('Klicke auf "Map anzeigen" um eine interaktive Map zu öffnen')
        await message.edit(view=PermaMap(message.id))


def setup(bot):
    bot.add_cog(DMapCog(bot))

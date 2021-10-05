from typing import Optional, Union

import discord
from discord.ext import commands

from taubsi.utils.checks import is_admin
from taubsi.cogs.dmap.mapmenu import MapMenu


class PermaMap(discord.ui.View):
    def __init__(self, message_id: int):
        super().__init__(timeout=None)
        button = discord.ui.Button(label="Map anzeigen",
                                   style=discord.ButtonStyle.blurple,
                                   custom_id=f"pm{message_id}")
        button.callback = self.start_map
        self.add_item(button)

        help = discord.ui.Button(label="Hilfe",
                                 style=discord.ButtonStyle.grey,
                                 custom_id=f"pmh{message_id}")
        help.callback = self.send_help
        self.add_item(help)

    @staticmethod
    async def start_map(interaction: discord.Interaction):
        dmap = MapMenu(interaction)
        await dmap.send()

    @staticmethod
    async def send_help(interaction: discord.Interaction):
        await interaction.response.send_message("Hier könnte Hilfe stehen", ephemeral=True)


class DMapCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(slash_command=False)
    @commands.check(is_admin)
    async def permamap(self, ctx: commands.Context):
        message = await ctx.send('Klicke auf "Map anzeigen" um eine interaktive Map zu öffnen')
        await message.edit(view=PermaMap(message.id))
        await ctx.reply(f"Please put this message ID in your config: `{message.id}`", delete_after=30)
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(DMapCog(bot))

from typing import Optional, Union

import discord
from discord.ext import commands

from taubsi.utils.checks import is_admin
from taubsi.cogs.dmap.mapmenu import MapMenu
from taubsi.core.bot import bot


class PermaMap(discord.ui.View):
    def __init__(self, message_id: int):
        super().__init__(timeout=None)
        button = discord.ui.Button(label=bot.translate("dmap_open"),
                                   style=discord.ButtonStyle.blurple,
                                   custom_id=f"pm{message_id}")
        button.callback = self.start_map
        self.add_item(button)

        help_button = discord.ui.Button(label=bot.translate("Help"),
                                        style=discord.ButtonStyle.grey,
                                        custom_id=f"pmh{message_id}")
        help_button.callback = self.send_help
        self.add_item(help_button)

    @staticmethod
    async def start_map(interaction: discord.Interaction):
        dmap = MapMenu(interaction)
        await dmap.send()

    @staticmethod
    async def send_help(interaction: discord.Interaction):
        # TODO help
        embed = discord.Embed(
            title="Hilfe bei der Raid Map",
            description=(
                "Die Raid Map ist eine komplett interaktive, funktionsfähige Map in Discord, die Raids anzeigen kann.\n"
            )
        )
        embed.add_field(
            name="Hauptmenü",
            value="Im Hauptmenü der Ma"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class DMapCog(commands.Cog):
    def __init__(self, _):
        pass

    @commands.command(slash_command=False)
    @commands.check(is_admin)
    async def permamap(self, ctx: commands.Context):
        embed = discord.Embed(title=bot.translate("dmap"))
        embed.set_footer(text=bot.translate("dmap_android"))
        message = await ctx.send(embed=embed)
        await message.edit(view=PermaMap(message.id))
        await ctx.reply(f"Please put this message ID in your config: `{message.id}`", delete_after=30)
        await ctx.message.delete()

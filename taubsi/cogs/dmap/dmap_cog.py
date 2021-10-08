from typing import Optional, Union

import discord
from discord.ext import commands

from taubsi.utils.checks import is_admin
from taubsi.cogs.dmap.mapmenu import MapMenu
from taubsi.core.bot import bot, log


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
        # self.add_item(help_button)  # TODO Help

    @staticmethod
    async def start_map(interaction: discord.Interaction):
        log.info(f"User {interaction.user} started a dmap")
        dmap = MapMenu(interaction)
        await dmap.send()

    @staticmethod
    async def send_help(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Hilfe bei der Raid Map",
            description=(
                "Die Raid Map ist eine komplett interaktive Map in Discord. Mit ihr kannst du aktive Raids "
                "sehen und sie auch gleich ansetzen. Es gibt insgesamt drei Menüs.\n\n"
                "Durch Limitation von Discord kann es manchmal zu Fehlern kommen. Normalerweise hilft es dann, "
                "die Filter anzupassen und reinzuzoomen. Ansonsten unter der Nachricht auf \"Nachricht verwerden\""
                "klicken und die Map neu öffnen"
            )
        )
        embed.add_field(
            inline=False,
            name="Hauptmenü",
            value=(
                "Hier kannst du über verschiedene Steuerungen mit der Map interagieren.\n\n"
                "**Raid Level Filter**: Standardmäßig werden Level 5 Raids angezeigt, du kannst dir aber auch alle "
                "anderen Raids anzeigen lassen\n"
                "**Standort Auswahl**: Falls du schnell in deine Nachbarschaft kommen möchtest, kannst du "
                "über diese Auswahl schnell zu ausgewählten Standorten springen\n"
                "**Navigation**: Über die Pfeiltasten kannst du dich über die Map bewegen, mit den +/- Buttons "
                "kannst du rein- und rauszoomen\n"
                "**Raid ansetzen**: Bringt dich in das Raid Ansetzen Menü\n"
                "**Einstellungen**: Bringt dich in das Einstellungen Menü\n"
                "**Speed**: Du kannst einenn Multiplikator für die Navigation wählen, damit du die Map schneller "
                "bewegen kannst"
            )
        )
        embed.add_field(
            inline=False,
            name="Einstellungen",
            value=(
                "In den Einstellungen kannst du vor allem einstellen, wie die Map aussieht.\n\n"
                "**Map Style**: Der Map Style gibt an, wie die reine Karte aussehen soll\n"
                "**Icons**: Du kannst auswählen, welche Icons genutzt werden sollen\n"
                "**Icongröße**: Damit du die Raids besser erkennen kannst, kanns du die Größe der "
                "Icons auch anpassen"
            )
        )
        embed.add_field(
            inline=False,
            name="Raid ansetzen",
            value=(
                "Du kannst direkt in der Map einen Raid ansetzen. Dabei kannst du nur aus Arenen wählen, "
                "die gerade angezeigt werden. Als Startzeit musst du eine Vorgegebene wählen. Falls du den Raid "
                "zu einer anderen Zeit spielen möchtest, musst du ihn manuell über einen Befehl ansetzen."
            )
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

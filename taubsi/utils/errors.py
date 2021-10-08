import asyncio
from typing import Callable
import discord
from discord.ext.commands import CommandError

from taubsi.core import bot
from taubsi.core.logging import log


class TaubsiError(CommandError):
    """?"""
    pass


async def command_error(send: Callable,
                        error="Unbekannter Fehler",
                        delete_error=True,
                        **send_kwargs):
    try:
        log.info(f"Command Error: {error}")
        text = bot.translate("error_" + error)
        error_embed = discord.Embed(description=text, color=16073282)

        if delete_error:
            send_kwargs.update({"delete_after": 20})
        await send(embed=error_embed, **send_kwargs)
    except Exception as e:
        log.exception(e)
        pass


async def app_command_error(self, interaction: discord.Interaction, error: Exception):
    await command_error(interaction.response.send_message, error.__doc__, delete_error=False, ephemeral=True)

import asyncio
from discord import Embed
from taubsi.core.logging import log
from discord.ext.commands import CommandError


class TaubsiError(CommandError):
    """?"""
    pass


async def command_error(bot, message, error="Unbekannter Fehler", delete_error=True, delete_message=False):
    try:
        log.info(f"Command Error: {error}")
        text = bot.translate("error_" + error)
        error_embed = Embed(description=f"{text}", color=16073282)
        error_message = await message.channel.send(embed=error_embed)

        if not delete_error:
            raise

        await asyncio.sleep(20)
        await error_message.delete()

        if not delete_message:
            raise
        await message.delete()
        raise
    except:
        pass
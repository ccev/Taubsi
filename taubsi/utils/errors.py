import asyncio
from discord import Embed
from .logging import log
from discord.ext.commands import CommandError

class TaubsiError(CommandError):
    "?"
    pass

errors = {
    "invalid_time": "❌ Ich konnte deiner Nachricht keine gültige Zeit entnehmen",
    "raid_past": "❌ Du kannst keinen Raid für die Vergangenheit ansetzen",
    "max_lvl": "❌ Das Maximallevel ist 50",
    "raid_exists": "❌ Dieser Raid scheint schon angesetzt zu sein",
    "level_too_high": "❌ Das Level ist zu hoch",
    "level_too_small": "🤨 Sicher?",
    "no_team": "❌ Das Team konnte ich nicht finden. Probier stattdessen mal `rot`, `blau` oder `gelb`",
    "no_code_set": "❌ Dieser Spieler hat noch keinen Trainercode gesetzt",
    "wrong_code_format": "❌ Das Format konnte ich nicht erkennen. Probier stattdessen mal `1234 1234 1234`",
    "name_not_scanned": "😦 Ich konnte deinen Namen leider nicht finden. "
                        "Entweder warst du in letzter Zeit in keiner Arena oder du hast den Namen falsch geschrieben.",
    "user_not_linked": "❌ Dieser Spieler hat sich noch nicht mit einem Pokémon GO Profil gelinkt"
}


async def command_error(message, error="Unbekannter Fehler", delete_error=True, delete_message=False):
    try:
        log.info(f"Command Error: {error}")
        text = errors.get(error, f"❌ {error}")
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
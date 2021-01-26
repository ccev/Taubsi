from discord.ext.commands import CommandError

class NoTime(CommandError):
    "Ich konnte der Nachricht keine gültige Zeit entnehmen."
    pass
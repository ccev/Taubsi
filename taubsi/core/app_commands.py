from typing import Callable
from discord import Interaction
from taubsi.utils.errors import TaubsiError, command_error


async def app_cmd_invoke(interaction: Interaction, command: Callable, *command_args, **command_kwargs):
    try:
        await command(*command_args, **command_kwargs)
    except TaubsiError as e:
        await command_error(interaction.response.send_message, e.__doc__, ephemeral=True)
    return

import discord

from taubsi.utils.utils import reverse_get
from taubsi.utils.logging import logging
from taubsi.cogs.raids.emotes import *
from taubsi.cogs.raids.raidmessage import RaidMessage

log = logging.getLogger("Raids")

"""
class ChoiceButton(discord.ui.Button):
    def __init__(self, gym, choicemessage):
        super().__init__(style=discord.ButtonStyle.grey, label=gym.name)
        self.gym = gym
        self.choicemessage = choicemessage

    async def callback(self, interaction: discord.Interaction):
        await self.choicemessage.button_clicked(self.gym, interaction)


class ChoiceMessageView(discord.ui.View):
    def __init__(self, choicemessage):
        super().__init__()

        for gym in choicemessage.gyms:
            self.add_item(ChoiceButton(gym, choicemessage))
"""


class ChoiceMessage:
    def __init__(self, message, gyms, start_time, cog):
        self.embed = discord.Embed()
        self.init_message = message
        self.start_time = start_time
        self.message = None
        self.gyms = gyms
        self.cog = cog

    def make_embed(self):
        text = "Bitte wähle die, an der der Raid stattfinden soll.\n"
        for i, gym in enumerate(self.gyms, start=1):
            text += f"\n{NUMBER_EMOJIS[i]} **{gym.name}**"
        self.embed.title = f"Es wurden {len(self.gyms)} Arenen gefunden"
        self.embed.description = text

    async def send_message(self):
        self.message = await self.init_message.channel.send(embed=self.embed)

    async def react(self):
        for i in range(1, len(self.gyms)+1):
            try:
                await self.message.add_reaction(NUMBER_EMOJIS[i])
            except Exception as e:
                log.info(f"Error while reacting to choice message: {e} (Probably because it got deleted before finishing)")

    async def reacted(self, payload):
        emote = str(payload.emoji)
        number = reverse_get(NUMBER_EMOJIS, emote)
        await self.message.delete()
        raidmessage = RaidMessage()
        await raidmessage.from_command(self.gyms[number-1], self.start_time, self.init_message)
        return raidmessage

    async def button_clicked(self, gym, interaction):
        await self.message.delete()
        raidmessage = RaidMessage()
        await raidmessage.from_command(gym, self.start_time, self.init_message)

        self.cog.choicemessages.pop(self.message.id)
        await self.cog.create_raid(raidmessage)
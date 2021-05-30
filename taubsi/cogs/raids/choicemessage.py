import discord

from taubsi.utils.logging import logging
from taubsi.cogs.raids.raidmessage import RaidMessage

log = logging.getLogger("Raids")


class ChoiceButton(discord.ui.Button):
    def __init__(self, gym, choicemessage):
        super().__init__(style=discord.ButtonStyle.grey, label=gym.name)
        self.gym = gym
        self.choicemessage = choicemessage

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.choicemessage.init_message.author.id:
            return
        await self.choicemessage.button_clicked(self.gym)


class ChoiceMessageView(discord.ui.View):
    def __init__(self, choicemessage):
        super().__init__()

        for gym in choicemessage.gyms:
            self.add_item(ChoiceButton(gym, choicemessage))


class ChoiceMessage:
    def __init__(self, message, gyms, start_time, cog):
        self.embed = discord.Embed()
        self.init_message = message
        self.start_time = start_time
        self.message = None
        self.gyms = gyms[:25]
        self.cog = cog

    def make_embed(self):
        self.embed.title = f"Es wurden {len(self.gyms)} Arenen gefunden"
        self.embed.description = (
            "Bitte wähle die, an der der Raid stattfinden soll.\n\n"
            "*Falls du die Optionen nicht siehst, update bitte Discord oder setze den Raid "
            "mit einem eindeutigen Namen neu an.*"
        )

    async def send_message(self):
        self.message = await self.init_message.channel.send(embed=self.embed, view=ChoiceMessageView(self))

    async def button_clicked(self, gym):
        await self.message.delete()
        raidmessage = RaidMessage()
        await raidmessage.from_command(gym, self.start_time, self.init_message)

        self.cog.choicemessages.pop(self.message.id)
        await self.cog.create_raid(raidmessage)
import discord

from taubsi.taubsi_objects import tb
from taubsi.cogs.setup.objects import TaubsiUser
from taubsi.utils.enums import Team


class LinkView(discord.ui.View):
    message: discord.Message

    def __init__(self, author, ingame):
        super().__init__(timeout=60*5)

        self.author = author
        self.ingame = ingame
        self.interacted = False

    @discord.ui.button(label=tb.translate("link_accept"), style=discord.ButtonStyle.green)
    async def accept(self, _, interaction: discord.Interaction):
        if interaction.user.id != self.author.id or not self.interacted:
            return
        self.interacted = True
        user = TaubsiUser()
        await user.from_command(self.author)
        user.team, user.level = Team(self.ingame[0][1]), self.ingame[0][2]
        await user.update()

        name = self.ingame[0][0]
        keyvals = {
            "user_id": self.author.id,
            "ingame_name": name
        }
        await tb.intern_queries.insert("users", keyvals)

        embed = discord.Embed(description=tb.translate("link_success").format(self.ingame[0][0]),
                              color=3092790)
        await self.message.edit(embed=embed, view=None)
        await interaction.response.send_message(tb.translate("link_botcode").format(tb.config["botcode"]), ephemeral=True)

    @discord.ui.button(label=tb.translate("link_deny"), style=discord.ButtonStyle.red)
    async def deny(self, _, interaction: discord.Interaction):
        if interaction.user.id != self.author.id or not self.interacted:
            return
        self.interacted = True
        embed = discord.Embed(description=tb.translate("link_denied"), color=3092790)
        await interaction.response.edit_message(embed=embed, view=None)

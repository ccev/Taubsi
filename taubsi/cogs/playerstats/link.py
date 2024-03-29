import discord

from taubsi.cogs.setup.objects import TaubsiUser
from taubsi.core import bot, Team, log


class AcceptView(discord.ui.View):
    def __init__(self, author_id: int):
        self.author_id = author_id
        super().__init__()

    @discord.ui.button(label=bot.translate("link_send_again"), style=discord.ButtonStyle.blurple)
    async def send_code_again(self, _, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return
        content = f"```\n{bot.config.FRIEND_CODE}\n```"
        await interaction.response.send_message(content=content,
                                                ephemeral=True)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class LinkView(discord.ui.View):
    message: discord.Message

    def __init__(self, author, ingame):
        super().__init__(timeout=60*5)

        self.author = author
        self.ingame = ingame
        self.interacted = False

    @discord.ui.button(label=bot.translate("link_accept"), style=discord.ButtonStyle.green)
    async def accept(self, _, interaction: discord.Interaction):
        if interaction.user.id != self.author.id or self.interacted:
            return
        self.interacted = True
        try:
            user = TaubsiUser()
            await user.from_member(self.author)
            user.team, user.level = Team(self.ingame[0][1]), self.ingame[0][2]
            await user.update()
        except Exception as e:
            log.exception(e)

        name = self.ingame[0][0]
        keyvals = {
            "user_id": self.author.id,
            "ingame_name": name
        }
        await bot.taubsi_db.insert("users", keyvals)

        embed = discord.Embed(description=bot.translate("link_success").format(self.ingame[0][0]),
                              color=3092790)
        await self.message.edit(embed=embed, view=AcceptView(self.author.id))
        await interaction.response.send_message(
            bot.translate("link_botcode").format(bot.config.FRIEND_CODE), ephemeral=True)

    @discord.ui.button(label=bot.translate("link_deny"), style=discord.ButtonStyle.red)
    async def deny(self, _, interaction: discord.Interaction):
        if interaction.user.id != self.author.id or self.interacted:
            return
        self.interacted = True
        embed = discord.Embed(description=bot.translate("link_denied"), color=3092790)
        await interaction.response.edit_message(embed=embed, view=None)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

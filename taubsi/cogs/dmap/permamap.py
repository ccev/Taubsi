import discord


class PermaMap(discord.ui.View):
    def __init__(self, message_id: int):
        super().__init__(timeout=None)
        button = discord.ui.Button(label="Map anzeigen",
                                   style=discord.ButtonStyle.blurple,
                                   custom_id=f"pm{message_id}")
        button.callback = self.start_map
        self.add_item(button)

    @staticmethod
    async def start_map(interaction: discord.Interaction):
        dmap = Map(interaction)
        await dmap.send()

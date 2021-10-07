from __future__ import annotations
from typing import TYPE_CHECKING, List
from math import floor
import discord
import arrow
from taubsi.core import bot, Gym
from taubsi.cogs.raids.raidmessage import RaidMessage

if TYPE_CHECKING:
    from taubsi.cogs.dmap.mapmenu import MapMenu
    from taubsi.cogs.dmap.map_pages import StartRaidPage


class RaidSelect(discord.ui.Select):
    def __init__(self, page: StartRaidPage):
        super().__init__(placeholder=bot.translate("dmap_select_raid"),
                         min_values=1,
                         max_values=1)
        self.page = page
        self.set_gyms([])

    def set_gyms(self, display_gyms: List[Gym]):
        gyms = []
        for gym in display_gyms:
            if gym.raid.level in self.page.map_menu.post_to:
                gyms.append(gym)
        if self.page.gym not in gyms:
            self.page.gym = None
            self.page.start = None
            self.page.time_select.no_times()
            self.page.start_button.disabled = True
        self.disabled = len(gyms) == 0
        if len(gyms) == 0:
            self.disabled = True
            self.options = [
                discord.SelectOption(label="-", value="-")
            ]
        else:
            self.options = []
            gyms = sorted(gyms, key=lambda g: g.raid.end)
            for gym in gyms:
                start = gym.raid.start.to("local").strftime(bot.translate("timeformat_short"))
                end = gym.raid.end.to("local").strftime(bot.translate("timeformat_short"))
                default = self.page.gym and self.page.gym.id == gym.id
                self.add_option(label=gym.name,
                                value=gym.id,
                                description=f"{gym.raid.name} {start} – {end}",
                                default=default)

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        for option in self.options:
            option.default = option.value == value
        server = [s for s in bot.servers if s.id == interaction.guild_id][0]
        gym = server.gym_dict.get(value)
        await self.page.set_raid(gym, interaction)


class TimeSelect(discord.ui.Select):
    def __init__(self, page: StartRaidPage):
        super().__init__(placeholder=bot.translate("dmap_select_time"),
                         min_values=1,
                         max_values=1,
                         row=1,
                         disabled=True)
        self.page = page
        self.no_times()

    def no_times(self):
        self.page.start_button.disabled = True
        self.options = [
            discord.SelectOption(label="-", value="-")
        ]
        self.disabled = True

    def set_times(self, gym: Gym):
        seconds_left = gym.raid.end.int_timestamp - arrow.utcnow().int_timestamp
        if floor(seconds_left / 60) < 9:
            return

        if gym.raid.start < arrow.utcnow():
            suggested_times = [arrow.utcnow().shift(minutes=5)]
        else:
            suggested_times = [gym.raid.start]
        for time in arrow.Arrow.range("minute", gym.raid.start, gym.raid.end):
            if time.minute % 5 == 0 and \
                    suggested_times[-1].shift(minutes=4) < time < gym.raid.end.shift(minutes=-6):
                suggested_times.append(time)

        self.options = []
        if len(suggested_times) == 0:
            self.no_times()
        else:
            self.disabled = False
            for time in suggested_times:
                time = time.to("local")
                self.add_option(label=time.strftime(bot.translate("timeformat_short")),
                                value=str(time.int_timestamp))

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        time = arrow.get(int(value)).to("local")

        for option in self.options:
            option.default = option.value == value

        await self.page.set_time(time, interaction)


class StartButton(discord.ui.Button):
    def __init__(self, page: StartRaidPage):
        super().__init__(style=discord.ButtonStyle.blurple,
                         label=bot.translate("dmap_start"),
                         row=4,
                         disabled=True)
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        if not self.page.start > arrow.now().shift(minutes=4):
            await interaction.response.send_message("Sorry, zu dieser Zeit kann kein Raid gespielt werden",
                                                    ephemeral=True)
            return
        self.page.map_menu.set_page(self.page.map_menu.map_nav_page)
        await self.page.map_menu.edit(interaction)
        for message_id in self.page.map_menu.post_to[self.page.gym.raid.level]:
            raidmessage = await RaidMessage.from_raidinfo(self.page.gym, self.page.start,
                                                          interaction, message_id)
            raid_cog = bot.get_cog("RaidCog")
            await raid_cog.create_raid(raidmessage)

from __future__ import annotations

from math import floor
from typing import NoReturn, Callable, Optional, TYPE_CHECKING

import arrow
import discord

from taubsi.cogs.raids.raidmessage import GMAPS_LINK, AMAPS_LINK, RaidMessage
from taubsi.core import bot, Gym, Raid

if TYPE_CHECKING:
    from taubsi.core import InfoChannel


class InfoTimeButton(discord.ui.Button):
    def __init__(self, raidinfo: RaidInfo, time: arrow.Arrow):
        self.time = time.to("local")
        label = self.time.strftime(bot.translate("timeformat_short"))
        self.raidinfo = raidinfo

        super().__init__(style=discord.ButtonStyle.grey, label=label)

    async def callback(self, interaction: discord.Interaction) -> NoReturn:
        self.disabled = True
        await interaction.message.edit(embed=self.raidinfo.embed, view=self.view)
        await interaction.response.defer()

        if self.time < arrow.now().shift(minutes=4):
            return

        for channel_id in self.raidinfo.info_channel.post_to:
            raidmessage = await RaidMessage.from_raidinfo(self.raidinfo.gym, self.time,
                                                          interaction, channel_id)
            await self.raidinfo.create_raid(raidmessage)


class RaidInfoView(discord.ui.View):
    def __init__(self, raidinfo: RaidInfo):
        super().__init__(timeout=None)

        seconds_left = raidinfo.gym.raid.end.int_timestamp - arrow.utcnow().int_timestamp
        if floor(seconds_left / 60) < 9:
            return

        if raidinfo.gym.raid.start < arrow.utcnow():
            self.suggested_times = [arrow.utcnow().shift(minutes=5)]
        else:
            self.suggested_times = [raidinfo.gym.raid.start]
        for time in arrow.Arrow.range("minute", raidinfo.gym.raid.start, raidinfo.gym.raid.end):
            if time.minute % 10 == 0 and \
                    self.suggested_times[-1].shift(minutes=5) < time < raidinfo.gym.raid.end.shift(minutes=-6):
                self.suggested_times.append(time)

        for time in self.suggested_times:
            self.add_item(InfoTimeButton(raidinfo, time))


class RaidInfo:
    gym: Gym
    raid: Raid
    info_channel: InfoChannel

    embed: discord.Embed
    message: discord.Message
    view: Optional[RaidInfoView] = None

    create_raid: Callable

    def __init__(self, gym: Gym, info_channel: InfoChannel):
        self.gym = gym
        self.raid = gym.raid.copy()
        self.info_channel = info_channel
        raid_cog = bot.get_cog("RaidCog")
        self.create_raid = raid_cog.create_raid
        self.embed = discord.Embed()

    @classmethod
    async def make(cls, gym: Gym, info_channel: InfoChannel) -> RaidInfo:
        self = cls(gym, info_channel)
        await self.send_message()
        return self

    async def send_message(self):
        self.make_embed()
        self.make_view()
        self.message = await self.info_channel.channel.send(embed=self.embed, view=self.view)

    def make_embed(self) -> NoReturn:
        formatted_end = self.gym.raid.end.to("local").strftime(bot.translate("timeformat_long"))
        self.embed.title = self.gym.raid.name

        if self.gym.raid.boss and not self.gym.raid.is_predicted:
            self.embed.title += " " + bot.translate("Raid")

            self.embed.description = (
                f"{bot.translate('Bis')} **{formatted_end}** <t:{self.gym.raid.end.int_timestamp}:R>\n"
                f"100%: **{self.gym.raid.cp20}** | **{self.gym.raid.cp25}**\n"
                f"{bot.translate('Moves')}: {str(self.gym.raid.moveset)}"
            )
            self.embed.set_thumbnail(url=bot.uicons.raid(self.gym.raid).url)

        else:
            formatted_start = self.gym.raid.start.to("local").strftime(bot.translate("timeformat_long"))

            self.embed.description = (
                f"{bot.translate('Hatches')} <t:{self.gym.raid.start.int_timestamp}:R>\n"
                f"{bot.translate('Raidzeit')}: **{formatted_start} – {formatted_end}**"
            )
            self.embed.set_thumbnail(url=bot.uicons.egg(self.gym.raid).url)

            if self.gym.raid.boss:
                self.embed.title += " " + bot.translate("Egg")

        self.embed.description += "\n\n" + (
            f"[Google Maps]({GMAPS_LINK.format(self.gym.lat, self.gym.lon)}) | "
            f"[Apple Maps]({AMAPS_LINK.format(self.gym.lat, self.gym.lon)})"
        )

        self.embed.set_author(name=self.gym.name, icon_url=self.gym.img)

    def make_view(self):
        if self.info_channel.post_to:
            self.view = RaidInfoView(self)

    async def update_buttons(self) -> NoReturn:
        if not self.view:
            return
        old_view = self.view
        self.make_view()

        if not self.view:
            await self.edit_message()

        if len(old_view.children) != len(self.view.children):
            await self.edit_message()

    async def edit_message(self, view: bool = False, embed: bool = False) -> NoReturn:
        if view:
            self.make_view()
        if embed:
            self.make_embed()
        await self.message.edit(embed=self.embed, view=self.view)

    async def delete(self) -> NoReturn:
        await self.message.delete()

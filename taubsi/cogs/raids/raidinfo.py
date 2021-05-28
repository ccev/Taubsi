import discord
import arrow

from math import floor

from taubsi.taubsi_objects import tb
from taubsi.cogs.raids.raidmessage import GMAPS_LINK, AMAPS_LINK, RaidMessage
from taubsi.cogs.raids.pogo import ScannedRaid


TIMEFORMAT_SHORT = "%H:%M"
TIMEFORMAT_LONG = "%H:%M:%S"


class InfoTimeButton(discord.ui.Button):
    def __init__(self, raidinfo, time):
        super().__init__(style=discord.ButtonStyle.grey, label="")

        self.time = time.to("local")
        self.label = self.time.strftime(TIMEFORMAT_SHORT)
        self.raidinfo = raidinfo

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        await interaction.message.edit(embed=self.raidinfo.embed, view=self.view)

        if self.time < arrow.now().shift(minutes=4):
            return

        for channel_id in self.raidinfo.post_to:
            raidmessage = RaidMessage()
            await raidmessage.from_raidinfo(self.raidinfo.gym, self.raidinfo.raid, self.time,
                                            interaction, channel_id)
            await self.raidinfo.create_raid(raidmessage)


class RaidInfoView(discord.ui.View):
    def __init__(self, raidinfo):
        super().__init__()

        if raidinfo.time_left(raidinfo.raid.end)[0] < 9:
            return

        if raidinfo.raid.start < arrow.utcnow():
            self.suggested_times = [arrow.utcnow().shift(minutes=5)]
        else:
            self.suggested_times = [raidinfo.raid.start]
        for time in arrow.Arrow.range("minute", raidinfo.raid.start, raidinfo.raid.end):
            if time.minute % 10 == 0 and \
                    self.suggested_times[-1].shift(minutes=5) < time < raidinfo.raid.end.shift(minutes=-6):
                self.suggested_times.append(time)

        for time in self.suggested_times:
            self.add_item(InfoTimeButton(raidinfo, time))


class RaidInfo:
    def __init__(self, gym):
        self.gym = gym

        self.raid = None
        self.embed = discord.Embed()
        self.messages = []
        self.hatched = False

        self.channels = []
        self.post_to = []

        raid_cog = tb.bot.get_cog("RaidCog")
        self.create_raid = raid_cog.create_raid

        self.view = None

    def _make_raid(self, db_raid):
        gym_id, level, mon_id, form, costume, start, end, move_1, move_2, evolution = db_raid

        start = arrow.get(start)
        end = arrow.get(end)

        if mon_id is not None:
            self.hatched = True

        mon = tb.pogodata.get_mon(id=mon_id, form=form, costume=costume, temp_evolution_id=evolution)
        move1 = tb.pogodata.get_move(id=move_1)
        move2 = tb.pogodata.get_move(id=move_2)
        self.raid = ScannedRaid(self.gym, move1, move2, start, end, mon, level)

    async def from_db(self, db_raid, channel_settings):
        for channel_setting in channel_settings:
            if not db_raid[1] in channel_setting.get("levels", []):
                continue

            channel_id = channel_setting["id"]
            channel = await tb.bot.fetch_channel(channel_id)
            self.channels.append(channel)
            self.post_to += channel_setting.get("post_to", [])

        if not self.channels:
            return False

        self._make_raid(db_raid)
        self.make_embed()
        await self.send_message()

        return True
    
    async def has_hatched(self, db_raid):
        self._make_raid(db_raid)
        self.make_embed()
        await self.edit_message()

    @staticmethod
    def time_left(time):
        seconds_between = time.int_timestamp - arrow.utcnow().int_timestamp
        return floor(seconds_between / 60), seconds_between % 60

    def make_embed(self):
        formatted_end = self.raid.end.to("local").strftime(TIMEFORMAT_LONG)
        self.embed.title = self.raid.name

        if self.hatched:
            self.embed.title += " Raid"
            minutes_left, seconds_left = self.time_left(self.raid.end)

            self.embed.description = (
                f"Bis **{formatted_end}** ({minutes_left}m {seconds_left}s)\n"
                f"100%: **{self.raid.cp20}** | **{self.raid.cp25}**\n"
                f"Attacken: " + " | ".join(["**" + m.name + "**" for m in self.raid.moves])
            )
            self.embed.set_thumbnail(url=self.raid.boss_url)

        else:
            minutes_left, seconds_left = self.time_left(self.raid.start)
            formatted_start = self.raid.start.to("local").strftime(TIMEFORMAT_LONG)

            self.embed.description = (
                f"Schlüpft in **{minutes_left}m {seconds_left}s**\n"
                f"Raidzeit: **{formatted_start} – {formatted_end}**"
            )
            self.embed.set_thumbnail(url=self.raid.egg_url)

            if self.raid.boss:
                self.embed.title += " Ei"

        self.embed.description += "\n\n" + (
            f"[Google Maps]({GMAPS_LINK.format(self.gym.lat, self.gym.lon)}) | "
            f"[Apple Maps]({AMAPS_LINK.format(self.gym.lat, self.gym.lon)})"
        )

        self.embed.set_author(name=self.gym.name, icon_url=self.gym.img)

    async def send_message(self):
        if self.post_to:
            self.view = RaidInfoView(self)
        else:
            self.view = None

        for channel in self.channels:
            message = await channel.send(embed=self.embed, view=self.view)
            self.messages.append(message)

    async def edit_message(self):
        for message in self.messages:
            await message.edit(embed=self.embed, view=self.view)

    async def delete(self):
        for message in self.messages:
            await message.delete()

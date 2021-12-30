import asyncio
import re
from typing import Dict, List, TYPE_CHECKING, Tuple, Optional

import arrow
import dateparser
from dateutil import tz
from discord.ext import tasks, commands

from taubsi.cogs.raids.choicemessage import ChoiceMessage
from taubsi.cogs.raids.raidmessage import RaidMessage
from taubsi.cogs.raids.errors import TaubsiError, InvalidTime
from taubsi.core import log
from taubsi.utils.errors import command_error

if TYPE_CHECKING:
    from taubsi.core import TaubsiBot


def match_time(content: str, is_event: bool = False) -> Tuple[Optional[arrow.Arrow], str]:
    possible_times = []
    for text in content.split(" "):
        times = re.split("[:.;,]", text)
        if [n for n in times if not n.isdigit()]:
            continue

        hour = str(times[0])
        minute = "00"
        if len(times) > 1:
            minute = str(times[1])
        time = dateparser.parse(f"{hour}:{minute}", languages=["de"])
        time = arrow.get(time, tz.tzlocal())
        possible_times.append((time, text))

    final_time = (None, "")

    if len(possible_times) == 1:
        final_time = possible_times[0]
    elif len(possible_times) > 1:
        for time, text in possible_times[::-1]:
            if (not is_event) and (not arrow.now().date() == time.date()):
                continue
            if time > arrow.now():
                final_time = (time, text)
                break

    return final_time


class RaidCog(commands.Cog):
    def __init__(self, bot):
        self.bot: TaubsiBot = bot
        self.raidmessages: Dict[int, RaidMessage] = {}
        self.choicemessages = {}

    async def final_init(self):
        try:
            rm_query = """
            SELECT channel_id, message_id, init_message_id, start_time, gym_id, role_id
            FROM raids
            WHERE start_time > utc_timestamp()
            """
            raidmessages_db = await self.bot.taubsi_db.execute(rm_query, as_dict=False)
            for entry in raidmessages_db:
                raidmessage = await RaidMessage.from_db(*entry)
                self.raidmessages[raidmessage.message.id] = raidmessage
        except Exception as e:
            log.error("Error while querying ongoing raids. Existing raids may not be responsive anymore")
            log.exception(e)

        self.raid_loop.start()

    async def cog_command_error(self, ctx, error):
        if not isinstance(error, TaubsiError):
            log.exception(error)
            return
        await command_error(ctx.send, error.__doc__, False)

    async def create_raid(self, raidmessage: RaidMessage):
        for other_message in self.raidmessages.values():
            if other_message.gym.id == raidmessage.gym.id:
                warning = self.bot.translate("warn_other_times").format(other_message.formatted_start)
                raidmessage.static_warnings.add(warning)
                raidmessage.make_warnings()
        self.raidmessages[raidmessage.message.id] = raidmessage
        self.bot.loop.create_task(raidmessage.set_image())
        self.bot.loop.create_task(raidmessage.set_pokebattler())

        emojis = []
        for number in range(1, 7):
            emojis.append(self.bot.config.NUMBER_EMOJIS[number])
        emojis += list(self.bot.config.CONTROL_EMOJIS.values())

        for emoji in emojis:
            await raidmessage.message.add_reaction(emoji)
        await raidmessage.db_insert()
        log.info(f"Created a raid at {raidmessage.gym.name}, {raidmessage.start_time}")

        await asyncio.sleep(60*5)
        await raidmessage.message.clear_reaction("❌")

    @commands.Cog.listener()
    async def on_message(self, message):
        raid_channel = self.bot.raid_channel_dict.get(message.channel.id)
        if not raid_channel:
            return
        
        log.info(f"Trying to create a Raid Message from {message.id}")

        server = [s for s in self.bot.servers if s.id == message.guild.id]
        if not server:
            return
        server = server[0]

        final_time = match_time(message.content, raid_channel.is_event)
        gym_name_to_match = message.content

        raid_start = final_time[0]
        gym_name_to_match = gym_name_to_match.replace(final_time[1], "")

        matched_gyms = server.match_gyms(gym_name_to_match)

        if raid_start is None:
            if matched_gyms[0][1] > 80:
                raise InvalidTime
            return
        
        if len(matched_gyms) > 1:
            too_many_gyms = [g[0] for g in matched_gyms]
            choicemessage = ChoiceMessage(message, too_many_gyms, raid_start, self)
            choicemessage.make_embed()
            await choicemessage.send_message()
            self.choicemessages[choicemessage.message.id] = choicemessage
            return

        gym = matched_gyms[0][0]

        raidmessage = await RaidMessage.from_command(gym, raid_start, message)
        await self.create_raid(raidmessage)
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        raidmessage = self.raidmessages.get(payload.message_id)
        if raidmessage is not None:
            await raidmessage.add_reaction(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        raidmessage = self.raidmessages.get(payload.message_id)
        if not raidmessage:
            return
        await raidmessage.remove_reaction(payload)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        raidmessage: RaidMessage = self.raidmessages.get(message.id)
        if not raidmessage:
            return
        log.info(f"Gracefully deleting Raid at {raidmessage.gym.name}"
                 f"{raidmessage.start_time} {raidmessage.message.id}")
        try:
            await raidmessage.init_message.delete()
        except Exception:
            pass
        await raidmessage.role.delete()
        self.raidmessages.pop(message.id)
        await self.bot.taubsi_db.execute(
            f"delete from raids where message_id = {message.id}", result=False, commit=True)

    @tasks.loop(seconds=10)   
    async def raid_loop(self):
        raidmessages: List[RaidMessage] = list(self.raidmessages.copy().values())
        for raidmessage in raidmessages:
            try:
                message = raidmessage.message

                if arrow.now() > raidmessage.start_time.shift(minutes=6):
                    await raidmessage.end_raid()
                    self.raidmessages.pop(message.id)
                if raidmessage.start_time.shift(minutes=-5) < arrow.now() < raidmessage.start_time.shift(minutes=-4):
                    if not raidmessage.notified_5_minutes:
                        await raidmessage.notify(self.bot.translate("notify_raid_starts"))
                        raidmessage.notified_5_minutes = True

                if not raidmessage.raid.is_scanned or not raidmessage.raid.moves:
                    if raidmessage.raid_channel.is_event:
                        continue
                    if raidmessage.gym.raid is None:
                        continue
                    if raidmessage.gym.raid.end < arrow.utcnow():
                        continue
                    if raidmessage.raid == raidmessage.gym.raid:
                        continue
                    log.info(f"Raid Boss at {raidmessage.message.id} changed. Updating")
                    if not raidmessage.raid.boss and raidmessage.gym.raid.boss:
                        await raidmessage.notify(self.bot.translate("notify_hatched").format(
                            raidmessage.gym.raid.boss.name))

                    raidmessage.raid = raidmessage.gym.raid.copy()
                    raidmessage.make_base_embed()
                    await raidmessage.set_image()
                    await raidmessage.db_insert()
            except Exception as e:
                log.error("Error while Raid looping")
                log.exception(e)

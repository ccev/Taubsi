from typing import TYPE_CHECKING, List, Dict

import arrow
from discord.ext import tasks, commands

from taubsi.cogs.raid_info.raidinfo import RaidInfo
from taubsi.core import log

if TYPE_CHECKING:
    from taubsi.core import TaubsiBot, InfoChannel


class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot: TaubsiBot = bot
        self.raid_infos: Dict[str, RaidInfo] = {}
        self.info_channels: List[InfoChannel] = []

    def final_init(self):
        for server in self.bot.servers:
            now = arrow.utcnow()
            server.gyms = list(sorted(server.gyms, key=lambda g: g.raid.end if g.raid else now))
            for info_channel in server.info_channels:
                info_channel.set_gyms(server.gyms)
                self.info_channels.append(info_channel)

        if self.info_channels:
            self.info_loop.start()

    @tasks.loop(seconds=10)
    async def info_loop(self):
        for info_channel in self.info_channels:
            for gym in info_channel.gyms:
                try:
                    if not gym.raid:
                        continue
                    if not gym.raid.is_scanned:
                        continue
                    if gym.raid.end < arrow.utcnow():
                        continue
                    if gym.raid.level not in info_channel.levels:
                        continue

                    raidinfo = self.raid_infos.get(gym.id)

                    if raidinfo is None:
                        raidinfo = await RaidInfo.make(gym, info_channel)
                        self.raid_infos[gym.id] = raidinfo
                except Exception as e:
                    log.error("Exception in RaidInfo loop")
                    log.exception(e)

        try:
            for raidinfo in list(self.raid_infos.values()):
                await raidinfo.update_buttons()
                if raidinfo.gym.raid.end < arrow.utcnow():
                    await raidinfo.delete()
                    self.raid_infos.pop(raidinfo.gym.id)
        except Exception as e:
            log.error("Exception in RaidInfo Loop")
            log.exception(e)

    @info_loop.before_loop
    async def info_purge(self):
        for info_channel in self.info_channels:
            await info_channel.channel.purge(limit=1000)


def setup(bot):
    bot.add_cog(InfoCog(bot))

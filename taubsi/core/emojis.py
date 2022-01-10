from __future__ import annotations

from asyncio import Queue
from typing import List, TYPE_CHECKING

import discord
from arrow import Arrow

from taubsi.utils.utils import asyncget

if TYPE_CHECKING:
    from taubsi.core.bot import TaubsiBot
    from taubsi.core.uicons import UIcon


class TaubsiEmoji:
    last_used: Arrow
    static: bool
    emoji: discord.Emoji

    def __init__(self, emoji: discord.Emoji, static: bool = False):
        self.use()
        self.static = static
        self.emoji = emoji

    def use(self):
        self.last_used = Arrow.utcnow()


class EmojiJob:
    manager: EmojiManager

    def __init__(self, manager: EmojiManager):
        self.manager = manager

    async def process(self):
        pass


class EmojiAddJob(EmojiJob):
    url: str
    name: str
    static: bool

    def __init__(self, manager: EmojiManager, name: str, url: str, static: bool):
        super(EmojiAddJob, self).__init__(manager)
        self.url = url
        self.name = name
        self.static = static

    async def process(self):
        image = await asyncget(self.url)
        emoji = await self.manager.guild.create_custom_emoji(name=self.name, image=image)
        self.manager.emojis.append(TaubsiEmoji(emoji, static=self.static))
        self.manager.processing.remove(self.name)


class EmojiRemoveJob(EmojiJob):
    emoji: TaubsiEmoji

    def __init__(self, manager: EmojiManager, emoji: TaubsiEmoji):
        super(EmojiRemoveJob, self).__init__(manager)
        self.emoji = emoji

    async def process(self):
        await self.emoji.emoji.delete()
        self.manager.emojis.remove(self.emoji)


class EmojiManager:
    _bot: TaubsiBot
    processing: List[str]
    queue: Queue
    guild: discord.Guild
    emojis: List[TaubsiEmoji]

    def __init__(self, bot: TaubsiBot, guild: discord.Guild):
        self._bot = bot
        self.processing = []
        self.queue = Queue(maxsize=guild.emoji_limit)
        self.guild = guild

        self.emojis = []
        for emoji in guild.emojis:
            self.emojis.append(TaubsiEmoji(emoji))

        self._bot.loop.create_task(self._process_queue())

    @property
    def free_slots(self) -> bool:
        return len(self.emojis) + self.queue.qsize() < self.guild.emoji_limit

    async def _process_queue(self):
        while True:
            job: EmojiJob = await self.queue.get()
            await job.process()
            self.queue.task_done()

    def freeup(self):
        now = Arrow.utcnow().shift(days=-2)
        amount_freed = 0

        for emoji in self.emojis:
            if emoji.last_used < now:
                amount_freed += 1
                self.queue.put_nowait(EmojiRemoveJob(self, emoji))

        if amount_freed == 0:
            emojis = sorted(self.emojis, key=lambda e: e.last_used)
            for emoji in emojis[:5]:
                self.queue.put_nowait(EmojiRemoveJob(self, emoji))

    async def get_emoji(self, name: str, url: str, static: bool = False) -> discord.Emoji:
        if name in self.processing:
            await self.queue.join()

        for emoji in self.emojis:
            if name == emoji.emoji.name:
                emoji.use()
                return emoji.emoji

        if not self.free_slots:
            self.freeup()

        self.queue.put_nowait(EmojiAddJob(self, name, url, static))
        self.processing.append(name)
        await self.queue.join()
        return await self.get_emoji(name, url)

    async def get_from_uicon(self, uicon: UIcon):
        name = f"{uicon.category.value[0]}{uicon.name.replace('_', '')}{uicon.iconset.value.id}"
        return await self.get_emoji(name=name, url=uicon.url)

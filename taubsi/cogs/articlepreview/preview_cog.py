from __future__ import annotations
import re
import json
import logging

import arrow
import discord
from discord.ext import commands

from taubsi.utils.utils import asyncget

log = logging.getLogger("Preview")


class NextButton(discord.ui.Button):
    def __init__(self, view: ArticleView):
        super().__init__(
            emoji="▶️"
        )
        self.aview = view

    async def callback(self, interaction: discord.Interaction):
        self.aview.current_page += 1
        await self.aview.edit()
        await interaction.response.defer()


class PrevButton(discord.ui.Button):
    def __init__(self, view: ArticleView):
        super().__init__(
            emoji="◀️"
        )
        self.aview = view

    async def callback(self, interaction: discord.Interaction):
        self.aview.current_page -= 1
        await self.aview.edit()
        await interaction.response.defer()


class ArticleView(discord.ui.View):
    message: discord.Message

    def __init__(self, super_message: discord.Message, embed: discord.Embed, text: str):
        super().__init__(timeout=6*60)
        self.super_message = super_message
        self.embed = embed
        self.text = text
        self.texts = []
        self.current_page = 0
        self.make_texts()

        self.add_item(PrevButton(self))
        self.add_item(NextButton(self))
        self.disable_buttons()

    def disable_buttons(self):
        if self.current_page == 0:
            self.children[0].disabled = True
        else:
            self.children[0].disabled = False

        if self.current_page == len(self.texts) - 1:
            self.children[1].disabled = True
        else:
            self.children[1].disabled = False

    def make_texts(self):
        temp = ""
        i = 0
        splits = self.text.split(" ")
        self.texts.append(splits[0] + " ")
        for word in splits[1:]:
            word += " "
            temp += word
            if len(temp) >= 4000:
                temp = ""
                i += 1
                self.texts.append(word)
            self.texts[i] += word

    def update_text(self):
        self.embed.description = self.texts[self.current_page]
        self.embed.set_footer(text="Seite " + str(self.current_page + 1) + "/" + str(len(self.texts)))

    async def send(self):
        self.update_text()
        self.message = await self.super_message.reply(embed=self.embed, mention_author=False, view=self)

    async def edit(self):
        self.update_text()
        self.disable_buttons()
        await self.message.edit(embed=self.embed, view=self)


class PreviewCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.id == 211562278800195584:
            return
        match = re.search(r"(https)[^\s]*(ostsee-zeitung\.de)(\/[^\s]*?){3}[^\s]*", message.content)
        if not match:
            return
        link = match.group()
        source = await asyncget(link)
        source = source.decode("utf-8")

        json_match = re.search(r"{.*?@type\":\"NewsArticle\".*?\n", source)
        if not json_match:
            return
        article_json = json.loads(json_match.group())

        text = ""
        created = article_json.get("datePublished")
        if created:
            text += "Veröffentlicht: <t:" + str(int(arrow.get(created).timestamp())) + ">\n"
        modified = article_json.get("dateModified")
        if modified:
            text += "Zuletzt geändert: <t:" + str(int(arrow.get(modified).timestamp())) + ">\n"
        text += "\n"

        text += "**" + article_json.get("description", "") + "**\n\n" + article_json.get("articleBody", "")

        embed = discord.Embed(
            url=article_json.get("mainEntityOfPage", {}).get("@id", ""),
            title=article_json.get("headline", ""),
            description=text
        )
        embed.set_image(url=article_json.get("thumbnailUrl", ""))
        embed.set_author(name=article_json.get("author", {}).get("name", ""))

        if len(text) < 4096:
            await message.reply(embed=embed, mention_author=False)
        else:
            view = ArticleView(message, embed, text)
            await view.send()


def setup(bot):
    bot.add_cog(PreviewCog(bot))

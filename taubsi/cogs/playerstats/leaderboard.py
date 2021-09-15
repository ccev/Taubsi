from __future__ import annotations
from typing import List, Dict

import discord

from taubsi.taubsi_objects import tb
from taubsi.cogs.playerstats.objects import Stat, Badge


class Player:
    def __init__(self, name: str, value: int, pos: int):
        self.name = name
        self.value = value
        self.pos = pos


class LBPage:
    players: List[Player]
    index: int

    def __init__(self, players: List[Player]):
        self.players = players
        self.index = int(self.players[-1].pos // 10)

    def get_text(self) -> str:
        text = "```\n"
        for player in self.players:
            left = f"{player.pos}. {player.name}"
            right = f"{player.value:,}".replace(",", tb.translate("dot"))
            text += f"{left:<23}{right:>14} \n"
        return text + "```"


class _LBCategory(discord.SelectOption):
    stat: Badge
    name: str
    pages: List[LBPage]
    selected_page: int = 0

    def __init__(self, stat: Badge):
        self.stat = stat
        value = self.stat.value
        lang_key = "lb_category_" + value
        self.name = tb.translate(lang_key)

        super().__init__(label=self.name, value=value)

    def get_current_text(self):
        return self.pages[self.selected_page].get_text()

    async def prepare(self):
        self.pages = []
        players = await tb.queries.execute(
            f"select t.name, t.{self.value} from {tb.config['db_taubsiname']}.users u "
            f"left join {tb.config['db_dbname']}.cev_trainer t on u.ingame_name = t.name "
            f"where ingame_name is not null and {self.value} is not null "
            f"order by {self.value} desc",
            loop=tb.bot.loop
        )

        n = 10
        i = 1
        split_players = (players[i:i + n] for i in range(0, len(players), n))
        for page_players in split_players:
            final_players = []
            for name, stat in page_players:
                final_players.append(Player(name, stat, i))
                i += 1
            self.pages.append(LBPage(final_players))


class LeaderboardSelect(discord.ui.Select):
    def __init__(self, view: LeaderboardView):
        self.lb_view = view
        self.categories: Dict[str, _LBCategory] = {}

        super().__init__(custom_id="lb_select", placeholder=tb.translate("lb_placeholder"),
                         min_values=0, max_values=1)

    async def prepare(self):
        for stat in [Stat.XP, Stat.TOTAL_BATTLES_WON, Stat.CAUGHT_POKEMON, Stat.STOPS, Stat.UNIQUE_STOPS,
                     Stat.HATCHED, Stat.QUESTS, Stat.TRADES, Stat.GBL_RANK, Stat.LEGENDARY_RAIDS_WON,
                     Stat.GRUNTS, Stat.UNIQUE_UNOWN]:
            category = _LBCategory(stat)
            await category.prepare()

            self.categories[category.value] = category
            self.options.append(category)

    async def callback(self, interaction: discord.Interaction):
        if self.lb_view.author_id != interaction.user.id:
            return
        self.lb_view.current_category = self.categories[self.values[0]]
        self.lb_view.check_buttons()
        self.lb_view.update_embed()
        for option in self.options:
            if option.value == self.values[0]:
                option.default = True
            else:
                option.default = False
        await interaction.response.edit_message(embed=self.lb_view.embed, view=self.lb_view)


class _LBButton(discord.ui.Button):
    view: LeaderboardView
    emoji: str

    def __init__(self, view: LeaderboardView):
        self.lb_view = view
        super().__init__(emoji=self.emoji, row=1)
        self.check_disabled()

    def check_disabled(self):
        pass

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.author_id:
            return
        self.lb_view.check_buttons()
        self.lb_view.update_embed()
        await interaction.response.edit_message(embed=self.lb_view.embed, view=self.lb_view)


class NextButton(_LBButton):
    emoji = "▶"

    def __init__(self, view: LeaderboardView):
        super().__init__(view)

    def check_disabled(self):
        if self.lb_view.current_category.selected_page >= len(self.lb_view.current_category.pages) - 1:
            self.disabled = True
        else:
            self.disabled = False

    async def callback(self, interaction: discord.Interaction):
        self.lb_view.current_category.selected_page += 1
        await super().callback(interaction)


class BackButton(_LBButton):
    emoji = "◀"

    def __init__(self, view: LeaderboardView):
        super().__init__(view)

    def check_disabled(self):
        if self.lb_view.current_category.selected_page <= 0:
            self.disabled = True
        else:
            self.disabled = False

    async def callback(self, interaction: discord.Interaction):
        self.lb_view.current_category.selected_page -= 1
        await super().callback(interaction)


class LeaderboardView(discord.ui.View):
    select: LeaderboardSelect
    buttons: List[_LBButton]
    embed: discord.Embed
    current_category: _LBCategory

    def __init__(self, author_id: int):
        super().__init__()
        self.author_id = author_id
        self.embed = discord.Embed()

    def update_embed(self):
        self.embed.description = self.current_category.get_current_text()
        self.embed.title = self.current_category.name
        current_page = self.current_category.selected_page + 1
        total_pages = len(self.current_category.pages)
        self.embed.set_footer(text=tb.translate("Page").format(current_page, total_pages))

    def check_buttons(self):
        for button in self.buttons:
            button.check_disabled()

    async def prepare(self):
        self.select = LeaderboardSelect(self)
        await self.select.prepare()
        self.current_category = list(self.select.categories.values())[0]
        self.update_embed()

        self.buttons = []
        self.add_item(self.select)
        for button in [BackButton, NextButton]:
            button = button(self)
            self.buttons.append(button)
            self.add_item(button)

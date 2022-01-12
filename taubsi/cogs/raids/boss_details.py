from __future__ import annotations
from typing import TYPE_CHECKING, Optional

import discord
from taubsi.utils.errors import command_error
from taubsi.cogs.raids.errors import PokebattlerNotLoaded
from taubsi.core import bot
from taubsi.utils.image_manipulation import BossDetailsImage
from taubsi.pokebattler.models import Difficulty
from taubsi.core.uicons import IconSet

if TYPE_CHECKING:
    from taubsi.pokebattler.models import RaidPayload
    from taubsi.pogodata import Pokemon
    from taubsi.cogs.raids.raidmessage import RaidMessage


PBATTLER_LINK = "https://www.pokebattler.com/raids/{}"


class BossDetailsView(discord.ui.View):
    def __init__(self, raidmessage: RaidMessage):
        super(BossDetailsView, self).__init__()

        if raidmessage.raid.boss:
            if raidmessage.raid.level == 6:
                pb_level = "MEGA"
            else:
                pb_level = str(raidmessage.raid.level)
        pb_link = PBATTLER_LINK.format(raidmessage.raid.pokebattler_name, pb_level)

        self.add_item(discord.ui.Button(
            url=pb_link,
            label=bot.translate("more_on_pokebattler"),
            style=discord.ButtonStyle.link)
        )


class BossDetailsButton(discord.ui.Button):
    def __init__(self, raidmessage: RaidMessage):
        super(BossDetailsButton, self).__init__(
            label=bot.translate("boss_details"),
            custom_id=f"{raidmessage.message.id}pb"
        )
        self.raidmessage = raidmessage

    async def callback(self, interaction: discord.Interaction):
        pokebattler = self.raidmessage.pokebattler
        pokemon = self.raidmessage.raid.boss

        if not pokebattler or not self.raidmessage.raid.boss:
            await command_error(
                send=interaction.response.send_message,
                error=PokebattlerNotLoaded.__doc__,
                delete_error=False,
                ephemeral=True
            )
            return

        loading_embed = discord.Embed()
        loading_embed.set_footer(
            text=bot.translate("loading"),
            icon_url="https://mir-s3-cdn-cf.behance.net/project_modules/disp/c3c4d331234507.564a1d23db8f9.gif"
        )
        await interaction.response.send_message(
            embed=loading_embed,
            ephemeral=True
        )

        embed = discord.Embed()
        embed.set_thumbnail(url=bot.uicons.pokemon(pokemon).url)
        embed.title = pokemon.name

        type_emojis = ""
        weak_emojis = ""
        weather_emojis = ""
        weak_against = set()

        is_dual_type = len(pokemon.types) > 1
        for i, type_ in enumerate(pokemon.types):
            if is_dual_type:
                other_type = pokemon.types[abs(i-1)]
                for weak_against_type in type_.weak_to:
                    if weak_against_type.id not in other_type.resists_ids:
                        weak_against.add(weak_against_type)
            else:
                weak_against = set(type_.weak_to)
            emoji = await bot.emoji_manager.get_from_uicon(bot.uicons.type(type_))
            type_emojis += str(emoji)

            w = type_.boosted_by
            w_emoji = await bot.emoji_manager.get_from_uicon(bot.uicons.weather(w))
            weather_emojis += str(w_emoji)

        for type_ in weak_against:
            emoji = await bot.emoji_manager.get_from_uicon(bot.uicons.type(type_))
            weak_emojis += str(emoji)

        embed.description = (
            f"{bot.translate('catch_cp')}: {pokemon.cp(20, [10, 10, 10])} - **{pokemon.cp(20, [15, 15, 15])}**\n"
            f"{bot.translate('boosted_cp')}: {pokemon.cp(25, [10, 10, 10])} - "
            f"**{pokemon.cp(25, [15, 15, 15])}**  {weather_emojis}"
        )

        quicks = ""
        charges = ""
        for move in pokemon.moves:
            emoji = await bot.emoji_manager.get_from_uicon(bot.uicons.type(move.type, iconset=IconSet.POGO))
            name = f"{emoji} {move.name}\n"
            if move.proto.name.endswith("FAST"):
                quicks += name
            else:
                charges += name

        embed.add_field(name=bot.translate("quick_moves"), value=quicks)
        embed.add_field(name=bot.translate("charge_moves"), value=charges)

        min_players = 1
        max_players = 1
        last_difficulty = Difficulty.IMPOSSIBLE
        for i in range(1, 7):
            difficulty = pokebattler.get_difficulty(i)

            if last_difficulty.value <= Difficulty.IMPOSSIBLE.value and difficulty.value >= Difficulty.HARD.value:
                min_players = i

            if difficulty == Difficulty.VERY_EASY or i == 6:
                max_players = i
                break
            last_difficulty = difficulty

        embed.add_field(
            name="Raid Guide",
            value=bot.translate("raid_guide").format(
                name=pokemon.name,
                types=type_emojis,
                weak=weak_emojis,
                min=min_players,
                max=max_players
            ),
            inline=False
        )
        embed.set_footer(text=bot.translate("no_megas_cryptos"))

        attackers = pokebattler.best_attackers
        counters = await BossDetailsImage.get_counter_image(attackers)
        embed.set_image(url=counters)
        await interaction.edit_original_message(embed=embed, view=BossDetailsView(self.raidmessage))

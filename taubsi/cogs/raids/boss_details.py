from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import discord

from typing import List

from taubsi.pogodata import Pokemon
from taubsi.utils.utils import asyncget
from taubsi.core import bot
from taubsi.pokebattler.models import Defender


class BossDetails:
    @staticmethod
    async def pokemon_image(pokemon: Pokemon):
        mask = Image.open("counter.png").convert("L")
        data = await asyncget(bot.uicons.pokemon(pokemon))
        stream = BytesIO(data)
        mon = Image.open(stream)

        background = Image.new("RGBA", mask.size, (255, 0, 0, 0))
        size = 120
        multiplier = size / max(mon.size)
        mon_size = tuple([int(round(multiplier * s)) for s in mon.size])
        mon = mon.resize(mon_size, Image.ANTIALIAS)

        position_x = (mask.size[0] - mon.size[0]) // 2
        position_y = (mask.size[1] - mon.size[1]) // 2

        background.paste(mon, (position_x + 10, position_y + 10))

        # replace transparent pixels with color
        alpha = background.convert('RGBA').split()[-1]
        bg = Image.new("RGBA", background.size, (37, 38, 41) + (255,))
        bg.paste(background, mask=alpha)

        bg.putalpha(mask)
        stream.close()

        return bg

    @staticmethod
    async def get_counter_image(defenders: List[Defender]):
        mons = []
        count = 0
        for defender in defenders:
            if defender.pokemon.mega_id or defender.pokemon.is_shadow:
                continue
            if count >= 6:
                break
            count += 1
            mon_img = await BossDetails.pokemon_image(defender.pokemon)
            mons.append(mon_img)

        margin = 10
        width = len(mons) * mons[0].size[0] + ((len(mons) - 1) * margin)

        height = mons[0].size[1]
        end_result = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        pos = 0
        for mon in mons:
            end_result.paste(mon, (pos, 0))
            pos += mon.size[0] + margin

        with BytesIO() as stream:
            end_result.save(stream, "PNG")
            stream.seek(0)
            image_msg = await bot.trash_channel.send(file=discord.File(stream, filename=f"counters.png"))
            final_link = image_msg.attachments[0].url

        return final_link

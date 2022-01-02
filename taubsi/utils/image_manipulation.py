from io import BytesIO
from typing import List, Union

import discord
from PIL import Image, ImageDraw

from taubsi.core import bot
from taubsi.core.logging import log
from taubsi.core.pogo import Raid, Gym
from taubsi.pogodata import Pokemon
from taubsi.pokebattler.models import Defender
from taubsi.utils.utils import asyncget


async def upload(image: Image, name: str = "image") -> str:
    with BytesIO() as stream:
        image.save(stream, "PNG")
        stream.seek(0)
        image_msg = await bot.trash_channel.send(file=discord.File(stream, filename=f"{name}.png"))
        final_link = image_msg.attachments[0].url
    return final_link


async def download_image(url: str, mode: Union[str, bool] = "RGBA") -> Image:
    result = await asyncget(url)
    with BytesIO(result) as stream:
        image = Image.open(stream)
        if mode:
            image = image.convert(mode)
    return image


async def get_raid_image(gym: Gym, raid: Raid) -> str:
    """
    Generate a circuar Gym Img with the boss in front of it.
    Similiar to how it'd show on the in-game nearby view.
    """

    log.info(f"Creating a Raid Icon for Gym {gym.name}")

    gym_img = await download_image(gym.img)
    mon = await download_image(bot.uicons.raid(raid, shiny_chance=30))


    # gym resizing
    size = min(gym_img.size)
    gym_img = gym_img.crop(((gym_img.width - size) // 2,
                            (gym_img.height - size) // 2,
                            (gym_img.width + size) // 2,
                            (gym_img.height + size) // 2))

    mask = Image.new("L", (size * 2, size * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size * 2 - 2, size * 2 - 2), fill=255)
    mask = mask.resize(gym_img.size, Image.ANTIALIAS)

    result = gym_img.copy()
    result.putalpha(mask)

    gym_img = result.resize((128, 128), Image.ANTIALIAS)
    bg = Image.new("RGBA", (150, 150), 0)
    bg.paste(gym_img)

    # boss resizing & combining

    if raid.boss:
        size = 105
    else:
        size = 95
    multiplier = size / max(mon.size)
    mon_size = tuple([int(round(multiplier * s)) for s in mon.size])

    monbg = Image.new("RGBA", bg.size, 0)
    mon = mon.resize(mon_size, Image.ANTIALIAS)
    monbg.paste(mon, (bg.size[0] - mon.width, bg.size[1] - mon.height))

    final_img = Image.alpha_composite(bg, monbg)
    final_link = await upload(final_img, gym.name)

    return final_link


class BossDetails:
    @staticmethod
    async def pokemon_image(pokemon: Pokemon):
        mask = Image.open("assets/counter.png").convert("L")
        mon = await download_image(bot.uicons.pokemon(pokemon), mode=False)

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
        bg = Image.new("RGBA", background.size, (37, 38, 41, 255))
        bg.paste(background, mask=alpha)

        bg.putalpha(mask)

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

        final_link = await upload(end_result, "counters")

        return final_link
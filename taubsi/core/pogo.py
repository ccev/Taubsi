from __future__ import annotations
from typing import Union, Dict, Any, Optional, TYPE_CHECKING, List
from io import BytesIO
from enum import Enum
from datetime import datetime

import arrow
import discord
from PIL import Image, ImageDraw
from pogodata.objects import Move
from pogodata.pokemon import Pokemon

from taubsi.core import bot
from taubsi.utils.utils import asyncget, calculate_cp
from taubsi.core.logging import log

if TYPE_CHECKING:
    from taubsi.core.bot import TaubsiBot


class Team(Enum):
    NOTEAM = 0
    MYSTIC = 1
    VALOR = 2
    INSTINCT = 3


class Raid:
    is_scanned: bool
    is_predicted: bool = False

    boss: Optional[Pokemon]

    level: int
    cp20: int = 0
    cp25: int = 0
    boss: Optional[Pokemon]
    name: str = "?"
    pokebattler_name: str = "UNOWN"

    start: Optional[arrow.Arrow]
    end: Optional[arrow.Arrow]
    moves: Optional[List[Move]] = None

    def __init__(self, bot: TaubsiBot, raid_data: Dict[str, Any]):
        """
        raid_data:
        {
            "level": int,
            "start": any,
            "end": any,
            "move_1": none/id,
            "move_2": none/id,
            "pokemon_id" ...
        }
        """
        self.level = raid_data["level"]
        self.is_scanned = bool(raid_data.get("start"))

        if self.is_scanned:
            self.start = arrow.get(raid_data.get("start"))
            self.end = arrow.get(raid_data.get("end"))
            if raid_data.get("pokemon_id"):
                move1 = bot.pogodata.get_move(id=raid_data.get("move_1"))
                move2 = bot.pogodata.get_move(id=raid_data.get("move_2"))
                self.moves = [move1, move2]
                self.boss = bot.pogodata.get_mon(id=raid_data.get("pokemon_id"),
                                                 form=raid_data.get("form"),
                                                 costume=raid_data.get("costume"),
                                                 temp_evolution_id=raid_data.get("evolution"))
        else:
            available_bosses = bot.pogodata.raids[self.level]
            if len(available_bosses) == 1:
                self.boss = available_bosses[0]
                self.is_predicted = True

        if self.boss:
            self.name = self.boss.name

            self.pokebattler_name = self.boss.base_template
            if self.boss.temp_evolution_id > 0:
                self.pokebattler_name += "_MEGA"

            if self.boss.temp_evolution_id > 0:
                stats = bot.pogodata.get_mon(template=self.boss.base_template).stats
            else:
                stats = self.boss.stats
            self.cp20 = calculate_cp(20, stats, [15, 15, 15])
            self.cp25 = calculate_cp(25, stats, [15, 15, 15])
        else:
            if self.level != 6:
                self.name = f"Level {self.level} Ei"
            else:
                self.name = "Mega Ei"

    def __eq__(self, other: Raid):
        return True

    @property
    def has_hatched(self) -> bool:
        if not self.is_scanned:
            return self.is_predicted
        return self.start < arrow.utcnow()


class Gym:
    raid: Optional[Raid] = None
    id: str
    name: str = ""
    img: str = ""
    lat: float = 0
    lon: float = 0
    team: Team = Team.NOTEAM

    def __init__(self, bot: TaubsiBot, data: Dict[str, Any]):
        self._bot = bot
        self.id = data.get("id")
        self.update(data)

    def update(self, data: Dict[str, Any], raid_data: Optional[dict] = None):
        self.name = data.get("name", self.name)
        self.img = data.get("url", self.img)
        self.lat = data.get("latitude", self.lat)
        self.lon = data.get("longitude", self.lon)
        self.team = Team(data.get("team", self.team.value))

        if raid_data and raid_data["end"] > datetime.utcnow():
            self.set_raid(raid_data)
        else:
            if self.raid and self.raid.is_scanned:
                self.raid = None

    async def set_raid(self, raid_data: Optional[dict] = None):
        if raid_data:
            self.raid = Raid(self._bot, raid_data)
        else:
            query = (
                f"select level, pokemon_id, form, costume, start, end, move_1, move_2, evolution "
                f"from raid "
                f"where gym_id = '{self.id}' and end > utc_timestamp()"
            )
            raid = await self._bot.mad_db.execute(query)
            if not raid:
                return
            self.raid = Raid(self._bot, raid)

    def get_raid(self, level: int = 0) -> Raid:
        """
        Returns current raid or makes one up
        """
        if not self.raid or (level and self.raid.level != level):
            return Raid(self._bot, {"level": level})
        else:
            return self.raid

    async def get_raid_image(self) -> str:
        """
        Generate a circuar Gym Img with the boss in front of it.
        Similiar to how it'd show on the in-game nearby view.
        """
        if not self.raid:
            return ""

        if self.raid.boss:
            mon_size = (105, 105)
        else:
            mon_size = (95, 95)
        boss_result = await asyncget(self._bot.uicons.raid(self.raid, shiny_chance=30))
        log.info(f"Creating a Raid Icon for Gym {self.name}")
        gym_result = await asyncget(self.img)

        gymstream = BytesIO(gym_result)
        bossstream = BytesIO(boss_result)
        gym = Image.open(gymstream).convert("RGBA")

        # gym resizing
        size = min(gym.size)
        gym = gym.crop((gym.width - size) // 2,
                       (gym.height - size) // 2,
                       (gym.width + size) // 2,
                       (gym.height + size) // 2)

        mask = Image.new("L", (size*2, size*2), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size*2-2, size*2-2), fill=255)
        mask = mask.resize(gym.size, Image.ANTIALIAS)

        result = gym.copy()
        result.putalpha(mask)

        gym = result.resize((128, 128), Image.ANTIALIAS)
        bg = Image.new("RGBA", (150, 150), 0)
        bg.paste(gym)

        # boss resizing & combining
        mon = Image.open(bossstream).convert("RGBA")

        monbg = Image.new("RGBA", bg.size, 0)
        mon = mon.resize(mon_size, Image.ANTIALIAS)
        monbg.paste(mon, (bg.size[0]-mon.width, bg.size[1]-mon.height))

        final_img = Image.alpha_composite(bg, monbg)

        with BytesIO() as stream:
            final_img.save(stream, "PNG")
            stream.seek(0)
            image_msg = await self._bot.trash_channel.send(file=discord.File(stream, filename="raid-icon.png"))
            final_link = image_msg.attachments[0].url

        gymstream.close()
        bossstream.close()

        return final_link


class Badge:
    value: str
    targets: List[int]

    def __init__(self, value: str, targets: List[int]):
        self.value = value
        self.targets = targets

    def next_target(self, number: int) -> str:
        for target in self.targets:
            if target > number:
                return f"/{target:,}"
        return ""

    def get_tier_prefix(self, number: int) -> str:
        level = sum([1 for t in self.targets if t <= number])
        emoji = bot.config.BADGE_LEVELS[level]
        return emoji


class Stat:
    XP = Badge("xp", [])
    KM_WALKED = Badge("km_walked", [10, 100, 1000, 10000])
    CAUGHT_POKEMON = Badge("caught_pokemon", [30, 500, 2000, 50000])
    STOPS = Badge("stops_spun", [100, 1000, 2000, 50000])
    EVOLVED = Badge("evolved", [3, 20, 200, 2000])
    HATCHED = Badge("hatched", [10, 100, 500, 2500])
    QUESTS = Badge("quests", [10, 100, 1000, 2500])
    TRADES = Badge("trades", [10, 100, 1000, 2500])
    UNIQUE_STOPS = Badge("unique_stops_spun", [10, 100, 1000, 2000])
    BEST_FRIENDS = Badge("best_friends", [1, 2, 3, 20])

    TOTAL_BATTLES_WON = Badge("battles_won", [])
    NORMAL_RAIDS_WON = Badge("normal_raids_won", [10, 100, 1000, 2000])
    LEGENDARY_RAIDS_WON = Badge("legendary_raids_won", [10, 100, 1000, 2000])
    FRIEND_RAIDS = Badge("raids_with_friends", [10, 100, 1000, 2000])
    RAID_ACHIEVEMENTS = Badge("raid_achievements", [1, 50, 200, 500])
    UNIQUE_RAIDS = Badge("unique_raid_bosses", [2, 10, 50, 150])
    GRUNTS = Badge("grunts_defeated", [10, 100, 1000, 2000])
    GIOVANNI = Badge("giovanni_defeated", [1, 5, 20, 50])
    PURIFIED = Badge("purified", [5, 50, 500, 1000])
    GYM_BATTLES_WON = Badge("gym_battles_won", [10, 100, 1000, 4000])
    BERRIES_FED = Badge("berries_fed", [10, 100, 1000, 15000])
    HOURS_DEFENDED = Badge("hours_defended", [10, 100, 1000, 15000])
    TRAININGS_WON = Badge("trainings_won", [10, 100, 1000, 2000])
    GREAT_WON = Badge("league_great_won", [5, 50, 200, 1000])
    ULTRA_WON = Badge("league_ultra_won", [5, 50, 200, 1000])
    MASTER_WON = Badge("league_master_won", [5, 50, 200, 1000])
    GBL_RANK = Badge("gbl_rank", [])
    GBL_RATING = Badge("gbl_rating", [])

    BEST_BUDDIES = Badge("best_buddies", [1, 10, 100, 200])
    MEGA_EVOS = Badge("mega_evos", [1, 50, 500, 1000])
    COLLECTIONS = Badge("collections_done", [])
    UNIQUE_MEGA_EVOS = Badge("unique_mega_evos", [1, 24, 36, 46])
    STREAKS = Badge("7_day_streaks", [1, 10, 50, 100])
    TRADE_KM = Badge("trade_km", [1000, 100000, 1000000, 10000000])
    LURE_CAUGHT = Badge("caught_at_lure", [5, 25, 500, 2500])
    WAYFARER = Badge("wayfarer_agreements", [50, 500, 1000, 1500])
    REFERRED = Badge("trainers_referred", [1, 10, 20, 50])
    PHOTOBOMBS = Badge("photobombs", [10, 50, 200, 400])

    UNIQUE_UNOWN = Badge("unique_unown", [3, 10, 26, 28])
    XL_KARPS = Badge("xl_karps", [3, 50, 300, 1000])
    XS_RATS = Badge("xs_rats", [3, 50, 300, 1000])
    PIKACHU = Badge("pikachu_caught", [3, 50, 300, 1000])
    DEX_1 = Badge("dex_gen1", [5, 50, 100, 151])
    DEX_2 = Badge("dex_gen2", [5, 30, 70, 100])
    DEX_3 = Badge("dex_gen3", [5, 40, 90, 135])
    DEX_4 = Badge("dex_gen4", [5, 30, 80, 107])
    DEX_5 = Badge("dex_gen5", [5, 50, 100, 156])
    DEX_6 = Badge("dex_gen6", [5, 25, 50, 72])
    DEX_7 = Badge("dex_gen7", [])
    DEX_8 = Badge("dex_gen8", [5, 25, 50, 89])
    NORMAL = Badge("caught_normal", [10, 50, 200, 2500])
    FIGHTING = Badge("caught_fighting", [10, 50, 200, 2500])
    FLYING = Badge("caught_flying", [10, 50, 200, 2500])
    POISON = Badge("caught_poison", [10, 50, 200, 2500])
    GROUND = Badge("caught_ground", [10, 50, 200, 2500])
    ROCK = Badge("caught_rock", [10, 50, 200, 2500])
    BUG = Badge("caught_bug", [10, 50, 200, 2500])
    GHOST = Badge("caught_ghost", [10, 50, 200, 2500])
    STEEL = Badge("caught_steel", [10, 50, 200, 2500])
    FIRE = Badge("caught_fire", [10, 50, 200, 2500])
    WATER = Badge("caught_water", [10, 50, 200, 2500])
    GRASS = Badge("caught_grass", [10, 50, 200, 2500])
    ELECTRIC = Badge("caught_electric", [10, 50, 200, 2500])
    PSYCHIC = Badge("caught_psychic", [10, 50, 200, 2500])
    ICE = Badge("caught_ice", [10, 50, 200, 2500])
    DRAGON = Badge("caught_dragon", [10, 50, 200, 2500])
    DARK = Badge("caught_dark", [10, 50, 200, 2500])
    FAIRY = Badge("caught_fairy", [10, 50, 200, 2500])

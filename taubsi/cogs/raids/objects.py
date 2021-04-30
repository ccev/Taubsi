import random
from io import BytesIO
import json
from math import floor, ceil
from enum import Enum

import discord
import arrow
from PIL import Image, ImageDraw
from pogodata.objects import Move
from pogodata.pokemon import Pokemon

from taubsi.utils.utils import asyncget, calculate_cp, reverse_get
from taubsi.utils.enums import Team
from taubsi.utils.logging import logging
from taubsi.taubsi_objects import tb
from taubsi.cogs.raids.emotes import *

log = logging.getLogger("Raids")
timeformat = "%H:%M"

TOTAL_LIMIT = 20
REMOTE_LIMIT = 10

RAID_WARNINGS = {
    "TOO_MANY_REMOTE": f"‼️ An einem Raid können maximal {REMOTE_LIMIT} Fern Raider teilnehmen. Passt darauf auf und sprecht euch ab!",
    "TOO_MANY_TOTAL": f"‼️ An einem Raid können maximal {TOTAL_LIMIT} Spieler teilnehmen. Passt darauf auf und sprecht euch ab!",
    "TOO_MANY_BOTH": f"‼️ An einem Raid können maximal {TOTAL_LIMIT} Spieler und {REMOTE_LIMIT} Fern Raider teilnehmen. Passt darauf auf und sprecht euch ab!",
    "IS_LATE": "‼️ Es kommt jemand maximal fünf Minuten zu spät. Wartet auf die Person und sprecht euch ggf. ab!",
    "OTHER_TIMES": "‼️ Dieser Raid wurde bereits zu {TIME} Uhr angesetzt"
}





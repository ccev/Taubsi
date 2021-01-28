import random
from io import BytesIO
import json
from math import floor, ceil

import discord
import arrow
from PIL import Image, ImageDraw
from pogodata.objects import Pokemon, Move

from taubsi.utils.utils import asyncget, calculate_cp, reverse_get
from taubsi.utils.enums import Team
from taubsi.utils.logging import logging
from taubsi.taubsi_objects import tb
from taubsi.cogs.raids.emotes import *

log = logging.getLogger("Raids")
timeformat = "%H:%M"

class Gym:
    def __init__(self, id_: int = 0, name: str = "?", img: str = "", lat: float = 0, lon: float = 0):
        self.id = id_
        self.name = name
        self.img = img
        self.lat = lat
        self.lon = lon

    async def get_active_raid(self, level):
        result = await tb.queries.execute(f"select level, pokemon_id, form, costume, start, end, move_1, move_2, evolution from raid where gym_id = '{self.id}'")
        db_level, mon_id, form, costume, start, end, move_1, move_2, evolution = result[0]
        start = arrow.get(start)
        end = arrow.get(end)

        if end > arrow.utcnow() and db_level == level:
            if mon_id:
                mon = tb.pogodata.get_mon(id=mon_id, form=form, costume=costume, temp_evolution_id=evolution)
                move1 = tb.pogodata.get_move(id=move_1)
                move2 = tb.pogodata.get_move(id=move_2)
            else:
                mon = None
                move1 = None
                move2 = None
            return ScannedRaid(self, move1, move2, start, end, mon, level)

        return BaseRaid(self, level)

class BaseRaid:
    def __init__(self, gym: Gym, level: int = 5):
        self.level = level
        self.gym = gym

        available_bosses = tb.pogodata.raids[level]
        boss = None
        if len(available_bosses) == 1:
            boss = available_bosses[0]
        self.make_boss(boss)

    def make_boss(self, boss=None):
        if boss:
            self.boss = boss
            self.name = self.boss.name
            self.cp20 = calculate_cp(20, boss.stats, [15, 15, 15])
            self.cp25 = calculate_cp(25, boss.stats, [15, 15, 15])
        else:
            self.boss = None
            if self.level != 6:
                self.name = f"Level {self.level} Ei"
            else:
                self.name = "Mega Ei"

    @property
    def compare(self):
        if self.boss:
            return str(self.boss.id) + "f" + str(self.boss.form) + "e" + str(self.boss.temp_evolution_id)
        else:
            return ""

    async def get_image(self):
        """
        Generate a circuar Gym Img with the boss in front of it.
        Similiar to how it'd show on the in-game nearby view.
        """
        if self.boss:
            mon_size = (105, 105)
            shiny = ""
            if random.randint(1, 30) == 20:
                shiny = "_shiny"
            boss_result = await asyncget(f"https://raw.githubusercontent.com/PokeMiners/pogo_assets/master/Images/Pokemon%20-%20256x256/{self.boss.asset}{shiny}.png")
        else:
            mon_size = (95, 95)
            boss_result = await asyncget(f"https://raw.githubusercontent.com/ccev/dp-assets/master/emotes/egg{self.level}.png")
        log.info(f"Creating a Raid Icon for Gym {self.gym.name}")
        gym_result = await asyncget(self.gym.img)

        gymstream = BytesIO(gym_result)
        bossstream = BytesIO(boss_result)
        gym = Image.open(gymstream).convert("RGBA")

        # gym resizing
        size = min(gym.size)
        gym = gym.crop(((gym.width - size) // 2, (gym.height - size) // 2, (gym.width + size) // 2, (gym.height + size) // 2))

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
            final_img.save(stream, 'PNG')
            stream.seek(0)
            image_msg = await tb.trash_channel.send(file=discord.File(stream, filename="raid-icon.png"))
            final_link = image_msg.attachments[0].url

        gymstream.close()
        bossstream.close()

        return final_link

class ScannedRaid(BaseRaid):
    def __init__(self, gym: Gym, move_1: Move, move_2: Move, start: arrow.Arrow, end: arrow.Arrow, mon: Pokemon, level: int = 5):
        super().__init__(gym, level)
        self.moves = [move_1, move_2]
        self.start = start
        self.end = end

        if mon:
            self.make_boss(mon)

    @property
    def compare(self):
        compare = super().compare
        if self.moves[0]:
            return str(self.moves[0].id) + "-" + str(self.moves[1].id)
        else:
            return "s" + compare

class RaidMember:
    def __init__(self, raidmessage, payload, amount):
        self.raidmessage = raidmessage

        self.member = raidmessage.message.guild.get_member(payload.user_id)
        
        self.team = None
        roles = [role.name.lower() for role in self.member.roles]
        for team in Team:
            if team.name.lower() in roles:
                self.team = team
                break
        
        if "raidnachrichten" in roles:
            self.is_subscriber = True
        else:
            self.is_subscriber = False

        self.update(amount)

    def update(self, amount):
        self.is_late = self.member.id in self.raidmessage.lates
        self.is_remote = self.member.id in self.raidmessage.remotes

        if amount is not None:
            self.amount = amount

    async def make_role(self):
        if self.amount > 0:
            if self.raidmessage.role not in self.member.roles:
                await self.member.add_roles(self.raidmessage.role)
        else:
            if self.raidmessage.role in self.member.roles:
                await self.member.remove_roles(self.raidmessage.role)

    def make_text(self):
        text = self.member.display_name + f" ({self.amount})"
        if self.is_late:
            text = CONTROL_EMOJIS["late"] + " " + text
        if self.is_remote:
            text = CONTROL_EMOJIS["remote"] + " " + text
        return text + "\n"

class ChoiceMessage:
    def __init__(self, message, gyms, start_time):
        self.embed = discord.Embed()
        self.init_message = message
        self.start_time = start_time
        self.message = None
        self.gyms = gyms

    def make_embed(self):
        text = "Bitte wähle die, an der der Raid stattfinden soll.\n"
        for i, gym in enumerate(self.gyms, start=1):
            text += f"\n{NUMBER_EMOJIS[i]} **{gym.name}**"
        self.embed.title = f"Es wurden {len(self.gyms)} Arenen gefunden"
        self.embed.description = text

    async def react(self):
        for i in range(1, len(self.gyms)+1):
            try:
                await self.message.add_reaction(NUMBER_EMOJIS[i])
            except Exception as e:
                log.info(f"Error while reacting to choice message: {e} (Probably because it got deleted before finishing)")

    async def reacted(self, payload):
        emote = str(payload.emoji)
        number = reverse_get(NUMBER_EMOJIS, emote)
        await self.message.delete()
        raidmessage = RaidMessage()
        await raidmessage.from_command(self.gyms[number-1], self.start_time, self.init_message)
        return raidmessage

class RaidMessage:
    def __init__(self):
        self.embed = discord.Embed()

        self.channel_id = 0
        self.message_id = 0
        self.message = None
        self.init_message_id = 0
        self.init_message = None
        self.start_time = arrow.get(2020, 1, 1, 12, 0)
        self.role = None

        self.gym = Gym()
        self.raid = None

        self.members = []
        self.remotes = []
        self.lates = []

        self.notified_5_minutes = False

    @property
    def total_amount(self):
        return sum([m.amount for m in self.members])

    async def from_command(self, gym, start_time, init_message):
        self.gym = gym

        self.start_time = start_time
        self.channel_id = init_message.channel.id
        self.channel_settings = tb.raid_channels[self.channel_id]

        self.init_message = init_message
        self.init_message_id = init_message.id

        self.raid = await self.gym.get_active_raid(self.channel_settings["level"])
        await self.send_message()

    async def get_message(self):
        channel = await tb.bot.fetch_channel(self.channel_id)
        message = await channel.fetch_message(self.message_id)
        return message

    def get_member(self, user_id: int):
        for member in self.members:
            if member.member.id == user_id:
                return member
        return None

    async def add_reaction(self, payload):
        emote = str(payload.emoji)
        amount = 1
        member = self.get_member(payload.user_id)
        if not member:
            member = RaidMember(self, payload, 1)
            self.members.append(member)

        if emote in CONTROL_EMOJIS.values():
            control = reverse_get(CONTROL_EMOJIS, emote)

            if control == "remove":
                if payload.user_id == self.init_message.author.id:
                    await self.message.delete()
                    return
            elif control == "late":
                self.lates.append(payload.user_id)
                await self.notify(f"🕐 {member.member.display_name}", member.member)
            elif control == "remote":
                self.remotes.append(payload.user_id)

        elif emote in NUMBER_EMOJIS.values():
            amount = reverse_get(NUMBER_EMOJIS, emote)
            await self.notify(f"▶️ {member.member.display_name} ({amount})", member.member)

        else:
            return

        member.update(amount)
        await self.make_member_fields()
        await member.make_role()

    async def remove_reaction(self, payload):
        member = self.get_member(payload.user_id)
        if not member:
            return

        #code duplication :thumbsdown:
        amount = None
        emote = str(payload.emoji)
        if emote in CONTROL_EMOJIS.values():
            control = reverse_get(CONTROL_EMOJIS, emote)

            if control == "late":
                self.lates.remove(payload.user_id)
                if member.amount > 0:
                    await self.notify(f"{member.member.display_name} kommt doch pünktlich", member.member)
            elif control == "remote":
                self.remotes.remove(payload.user_id)

        elif emote in NUMBER_EMOJIS.values():
            if member.amount > 0:
                await self.notify(f"❌ {member.member.display_name} ({member.amount})", member.member)
                amount = 0

        member.update(amount)
        await self.make_member_fields()
        await member.make_role()

    async def notify(self, message: str, user=None):
        log.info(f"Raid notification: {message}")
        for member in self.members:
            if not member.is_subscriber:
                continue
            if member.amount == 0:
                continue
            if user is not None and user.id == member.member.id:
                continue
            
            embed = discord.Embed()
            embed.title = self.gym.name
            embed.url = self.message.jump_url
            embed.description = message

            await member.member.send(embed=embed)

    async def get_difficulty(self):
        if not self.raid.boss:
            return None
        try:
            pb_mon_name = self.raid.boss.base_template
            if self.raid.boss.temp_evolution_id > 0:
                pb_mon_name += "_" + self.raid.boss.temp_evolution_template
            path = f"config/pokebattler/{pb_mon_name}.json"
            try:
                with open(path, "r") as f:
                    pb_data = json.load(f)
            except FileNotFoundError:
                if self.raid.level == 6:
                    level = "MEGA"
                else:
                    level = self.raid.level
                url = f"https://fight.pokebattler.com/raids/defenders/{pb_mon_name}/levels/RAID_LEVEL_{level}/attackers/levels/35/strategies/CINEMATIC_ATTACK_WHEN_POSSIBLE/DEFENSE_RANDOM_MC?sort=ESTIMATOR&weatherCondition=NO_WEATHER&dodgeStrategy=DODGE_REACTION_TIME&aggregation=AVERAGE&randomAssistants=-1&includeLegendary=true&includeShadow=false&attackerTypes=POKEMON_TYPE_ALL"
                pb_data_raw = await asyncget(url)
                pb_data_raw = json.loads(pb_data_raw.decode("utf-8"))
                pb_data = {}

                attackers = pb_data_raw["attackers"][0]
                for data in attackers["byMove"]:
                    move1 = data["move1"]
                    move2 = data["move2"]
                    pb_data[move1 + "+" + move2] = data["total"]
                pb_data["?"] = attackers["randomMove"]["total"]

                with open(path, "w+") as f:
                    f.write(json.dumps(pb_data))


            if isinstance(self.raid, BaseRaid) or not self.raid.moves[0]:
                estimator = pb_data["?"]
            else:
                estimator = pb_data["+".join([m.template for m in self.raid.moves])]
                
            estimator = estimator["estimator"]

            if self.total_amount < estimator:
                if self.total_amount < estimator - 0.3:
                    difficulty = 0
                else:
                    difficulty = 1
            else:
                if self.total_amount <= ceil(estimator):
                    difficulty = 2
                elif self.total_amount <= ceil(estimator) + 1:
                    difficulty = 3
                else:
                    difficulty = 4

            if self.total_amount < floor(estimator):
                difficulty = 0
            
            if self.total_amount == 0:
                difficulty = 0

            self.embed.color = DIFFICULTY_COLORS[difficulty]
            
            return DIFFICULTY_NAMES[difficulty] + "\n\n"
            

        except Exception as e:
            log.exception(e)
            return None

    async def make_base_embed(self):
        self.embed.title = self.raid.name + ": " + self.gym.name
        #difficulty = await self.get_difficulty()

        # Description based on what info is available
        self.embed.description = f"Start: **{self.start_time.strftime(timeformat)}**\n\n"
        if self.raid.boss:
            self.embed.description += f"100%: **{self.raid.cp20}** | **{self.raid.cp25}**\n"
        if isinstance(self.raid, ScannedRaid):
            if self.raid.moves[0]:
                self.embed.description += "Attacken: " + " | ".join(["**"+m.name+"**" for m in self.raid.moves]) + "\n"
            self.embed.description += f"Raidzeit: **{self.raid.start.to('local').strftime(timeformat)}** – **{self.raid.end.to('local').strftime(timeformat)}**"

    async def set_image(self):
        url = await self.raid.get_image()
        self.embed.set_thumbnail(url=url)

    def make_footer(self, amount: int = 0):
        self.embed.set_footer(text=f"Insgesamt: {amount}")

    async def make_member_fields(self):
        self.embed.clear_fields()
        for team in Team:
            emoji = TEAM_EMOJIS[team.value]

            index = 0
            for field in self.embed.fields:
                if emoji in field.name:
                    break
                index += 1

            members = [m for m in self.members if m.team == team]
            team_amount = sum([m.amount for m in members])
            
            if team_amount > 0:
                field_name = f"{emoji} ({team_amount})"
                field_value = ""
                for member in members:
                    if member.amount > 0:
                        field_value += member.make_text()
                self.embed.insert_field_at(index=index, name=field_name, value=field_value, inline=False)

        self.make_footer(self.total_amount)
        await self.edit_message()
            
    async def edit_message(self):
        log.info(f"Editing message {self.message_id}")
        await self.message.edit(embed=self.embed)

    async def send_message(self):
        channel = await tb.bot.fetch_channel(self.channel_id)
        await self.make_base_embed()
        self.make_footer()
        self.embed.timestamp = self.start_time.datetime
        self.message = await channel.send(embed=self.embed)
        self.message_id = self.message.id

        self.role = await channel.guild.create_role(name=f"{self.gym.name} ({self.start_time.strftime(timeformat)})", mentionable=True)
    
    async def delete_role(self):
        await self.role.delete()

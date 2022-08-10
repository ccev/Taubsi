import re
from typing import Optional

import discord

from taubsi.core import log, Team, bot


def name_level_from_nick(nick):
    match = re.match(r"^\[([0-5][0-9]|[0-9])\] .*", nick)
    if match:
        splits = nick.split("] ")
        level = int(splits[0].split("[")[1])
        name = splits[1]
    else:
        level = None
        name = nick
    return level, name


class TaubsiUser:
    user_id: int
    team: Team
    level: Optional[int]
    friendcode: Optional[int]
    name: str

    def from_db(self, user_id, team_id=0, level=None, friendcode=None, name=""):
        self.user_id = user_id
        self.team = Team(team_id)
        self.level = level
        self.friendcode = friendcode
        self.name = name
    
    async def from_member(self, member):
        self.friendcode = None
        result = await bot.taubsi_db.execute(
            f"select level, ifnull(team_id, 0), friendcode, name from users where user_id = %s;",
            args=member.id, as_dict=False)
        self.user_id = member.id
        if not result:
            nick = member.display_name
            self.level, self.name = name_level_from_nick(nick)
            
            for role in member.roles:
                for team in Team:
                    if team.name.lower() in role.name.lower():
                        self.team = team
                        break
        
        else:
            self.level, team_id, self.friendcode, self.name = result[0]
            if team_id is None:
                team_id = 0
            self.team = Team(team_id)

    @property
    def nickname(self):
        level = ""
        if self.level is not None:
            level = f"[{self.level}] "
        return level + self.name
    
    async def update(self):
        for server in bot.servers:
            guild = server.guild
            try:
                try:
                    member = await guild.fetch_member(self.user_id)
                except discord.DiscordException:
                    member = None
                
                if member is None:
                    continue

                team_roles = {}
                for role in guild.roles:
                    for team in Team:
                        if team.name.lower() in role.name.lower():
                            team_roles[team.value] = role

                await member.edit(nick=self.nickname)

                for role in team_roles.values():
                    await member.remove_roles(role)
                
                teamrole = team_roles.get(self.team.value)
                if teamrole:
                    await member.add_roles(teamrole)
            except Exception as e:
                log.error(f"Exception while trying to update user {self.user_id}")
                log.exception(e)

        keyvals = {
            "user_id": self.user_id,
        }

        if self.level is not None:
            keyvals["level"] = self.level
        if self.team.value > 0:
            keyvals["team_id"] = self.team.value
        if self.friendcode is not None:
            keyvals["friendcode"] = self.friendcode
        if self.name:
            keyvals["name"] = self.name
        
        await bot.taubsi_db.insert("users", keyvals)

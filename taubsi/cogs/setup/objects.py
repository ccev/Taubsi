import re
from taubsi.taubsi_objects import tb
from taubsi.utils.enums import Team
from taubsi.utils.logging import logging

log = logging.getLogger("Setup")

class TaubsiUser:
    def __init__(self):
        self.user_id = 0
        self.name = ""
        self.team = Team(0)
        self.level = None
        self.friendcode = None

    def from_db(self, user_id, team_id, level, friendcode, name):
        self.user_id = user_id
        self.team = Team(team_id)
        self.level = level
        self.friendcode = friendcode
        self.name = name
    
    async def from_command(self, member):
        result = await tb.intern_queries.execute(f"select level, team_id, level, friendcode, name from users where user_id = {member.id};")
        self.user_id = member.id
        if not result:
            nick = member.display_name
            match = re.match(r"^\[([0-5][0-9]|[0-9])\] .*", nick)
            if match:
                splits = nick.split("] ")
                self.level = int(splits[0].split("[")[1])
                self.name = splits[1]
            else:
                self.name = nick
            
            for role in member.roles:
                for team in Team:
                    if team.name.lower() in role.name.lower():
                        self.team = team
                        break
        
        if result:
            self.level, team_id, self.level, self.friendcode, self.name = result[0]
            self.team = Team(team_id)

    @property
    def nickname(self):
        level = ""
        if self.level is not None:
            level = f"[{self.level}] "
        return level + self.name
    
    async def update(self):
        for guild in tb.guilds:
            try:
                member = await guild.fetch_member(self.user_id)
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
            "level": self.level,
            "team_id": self.team.value,
            "friendcode": self.friendcode,
            "name": self.name
        }
        
        await tb.intern_queries.insert("users", keyvals)
        

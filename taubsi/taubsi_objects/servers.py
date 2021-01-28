import json
from . import tb
from taubsi.cogs.raids.objects import Gym

def _convert_path_sql(fence):
    sql_fence = []
    for lat, lon in fence:
        sql_fence.append(f"{lat} {lon}")
    sql_fence.append(f"{fence[0][0]} {fence[0][1]}")

    return "(" + ",".join(sql_fence) + ")"

async def load_servers():
    with open("config/servers.json", "r") as f:
        raw_servers = json.load(f)
    with open("config/geofence.json", "r") as f:
        raw_fences = json.load(f)

    tb.gyms = {}
    tb.friendcode_channels = []
    tb.raid_channels = {}

    for settings in raw_servers:
        for fence in raw_fences:
            if fence["name"].lower() == settings["geofence"].lower():
                sql_fence = _convert_path_sql(fence["path"])
                break

        gyms = await tb.queries.execute(f"select name, gym.gym_id, url, latitude, longitude from gymdetails left join gym on gym.gym_id = gymdetails.gym_id where ST_CONTAINS(ST_GEOMFROMTEXT('POLYGON({sql_fence})'), point(latitude, longitude))")
        
        gym_list = []
        for name, gid, url, lat, lon in gyms:
            gym_list.append(Gym(gid, name, url, lat, lon))
        tb.gyms[settings["id"]] = gym_list
        
        tb.friendcode_channels += settings["friendcodes_allowed"]

        for channel_settings in settings["raid_channels"]:
            tb.raid_channels[channel_settings["id"]] = channel_settings
        
        


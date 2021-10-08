from taubsi.core.config_classes import *


class Config(BaseConfig):
    TRASH_CHANNEL_ID = 124556432123  # ID of a channel to upload picture to
    LANGUAGE = Language.GERMAN  # Language.ENGLISH / Language.GERMAN
    BOT_TOKEN = ""  # Your Discord Bot Token
    ADMIN_IDS = []  # List of User IDs

    MAD_DB_NAME = "mad"
    TAUBSI_DB_NAME = "taubsi"
    DB_HOST = "0.0.0.0"
    DB_PORT = 3306
    DB_USER = ""
    DB_PASS = ""

    # Dmap section
    TILESERVER_URL = "https://tiles.map.com/"
    DMAP_MARKER_LIMIT = 200
    DMAP_STYLES = [
        Style("osm-bright", "Standard")
    ]
    DMAP_AREAS = [
        Area("Main", 50.134, 13.123, 13)  # name, lat, lon, zoom
    ]

    SERVERS = [
        Server(name="Server name", id_=12329038108391, geofence="fence name",
               raid_channels=[
                   RaidChannel(id_=132423131313, level=5),
                   RaidChannel(id_=432131342313, level=6)
               ],
               info_channels=[
                   InfoChannel(id_=156387823, levels=[5], post_to=[132423131313]),
                   InfoChannel(id_=91729182, levels=[1, 3])
               ],
               dmap_messages=[
                   DMapMessage(id_=27192793791371, post_to={5: [132423131313]})
               ],
               team_choose=[28912863981739, 123198739827917]
               )
    ]

    # only touch this if you know what you're doing
    COGS = Cog.default()
    FRIEND_CODE = ""

    NUMBER_EMOJIS = {
        1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣",
    }

    CONTROL_EMOJIS = {
        "late": "🕐",
        "remote": "<:remote:1234567899323215>",
        "remove": "❌"
    }

    TEAM_EMOJIS = {
        1: "<:mystic:1234567899323212>",
        2: "<:valor:1234567899323213>",
        3: "<:instinct:1234567899323214>"
    }

    TEAM_COLORS = {
        0: 38536,
        1: 4367861,
        2: 15684432,
        3: 16635957
    }

    BADGE_LEVELS = {
        0: "<:blank:123>",
        1: "<:bronze:123>",
        2: "<:silver:123>",
        3: "<:gold:123>",
        4: "<:platinum:123>"
    }

    DMAP_EMOJIS = {
        "settings": "<:settings:12134352452342>",
        "blank": BADGE_LEVELS[0],
        "up": "<:up:123>",
        "down": "<:down:123>",
        "left": "<:left:123>",
        "right": "<:right:880876867522027530>",
        "out": "<:minus:880883007685275719>",
        "in": "<:plus:880883007727226930>"
    }

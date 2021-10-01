from enum import Enum


class Cog(Enum):
    RAIDS = "taubsi.cogs.raids.raid_cog"
    SETUP = "taubsi.cogs.setup.setup_cog"
    MAIN_LOOPS = "taubsi.cogs.loops.loop"
    RAIDINFO = "taubsi.cogs.raid_info.info_cog"
    DMAP = "taubsi.cogs.dmap.dmap_cog"
    AUTOSETUP = "taubsi.cogs.auto_setup.auto_setup_cog"
    PLAYERSTATS = "taubsi.cogs.playerstats.playerstats_cog"
    ARTICLEPREVIEW = "taubsi.cogs.articlepreview.preview_cog"

    @classmethod
    def all(cls):
        return list(cls)

    @classmethod
    def basic(cls):
        return [cls.RAIDS, cls.SETUP, cls.MAIN_LOOPS, cls.RAIDINFO, cls.DMAP]

    @classmethod
    def v(cls):
        return [cls.PLAYERSTATS]

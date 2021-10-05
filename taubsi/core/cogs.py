from enum import Enum


class Cog(Enum):
    RAIDS = 0
    SETUP = 1
    MAIN_LOOPS = 2
    RAIDINFO = 3
    DMAP = 4
    AUTOSETUP = 5
    PLAYERSTATS = 6
    ARTICLEPREVIEW = 7

    @classmethod
    def all(cls):
        return list(cls)

    @classmethod
    def basic(cls):
        return [cls.RAIDS, cls.SETUP, cls.MAIN_LOOPS, cls.RAIDINFO, cls.DMAP]

    @classmethod
    def v(cls):
        return [cls.PLAYERSTATS]

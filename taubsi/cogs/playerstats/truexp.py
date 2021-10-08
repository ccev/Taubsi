from __future__ import annotations

from taubsi.cogs.playerstats.objects import Player, Badge, Stat


class TrueXP:
    player: Player

    curveball = 10
    mon_flee = 25
    throw_nice = 10
    throw_great = 50
    throw_excellent = 100
    first_throw = 50
    catch_mon = 100
    catch_bonus_100 = 100

    spin_stop = 50
    stop_bonus_10 = 100
    first_stop = 250

    egg_2km = 200
    egg_5km = 500
    egg_7km = 500
    egg_10km = 1000
    egg_12km = 2000

    new_mon = 500
    evolve = 500

    daily_stop = 500
    daily_mon = 500
    weekly_stop = 2500
    weekly_mon = 2500

    raid_1 = 3000
    raid_2 = 3500
    raid_3 = 4000
    raid_4 = 5000
    raid_5 = 10000

    defeat_gym_mon = 100
    empty_gym = 100
    feed_defender = 20

    best_friend = 100000 + 50000 + 10000 + 3000

    def __init__(self, player: Player):
        self.player = player

    def __get_stat(self, stat: Badge) -> int:
        value = self.player.stats[stat.value]
        if not value:
            return 0
        return value

    def catch(self) -> float:
        caught = self.__get_stat(Stat.CAUGHT_POKEMON)
        base = caught * self.catch_mon
        curveballs = caught * 0.9 * self.curveball
        fleed = caught * 0.05 * self.mon_flee
        first = caught * 0.6 * self.first_throw
        nice = caught * 0.2 * self.throw_nice
        great = caught * 0.1 * self.throw_great
        excellent = caught * 0.03 * self.throw_excellent
        bonus = caught * 0.005 * self.catch_bonus_100

        return base + curveballs + fleed + first + nice + great + excellent + bonus

    def dex(self) -> int:
        gen1 = self.__get_stat(Stat.DEX_1)
        gen2 = self.__get_stat(Stat.DEX_2)
        gen3 = self.__get_stat(Stat.DEX_3)
        gen4 = self.__get_stat(Stat.DEX_4)
        gen5 = self.__get_stat(Stat.DEX_5)
        gen6 = self.__get_stat(Stat.DEX_6)
        gen7 = self.__get_stat(Stat.DEX_7)
        gen8 = self.__get_stat(Stat.DEX_8)
        return gen1 + gen2 + gen3 + gen4 + gen5 + gen6 + gen7 + gen8 * self.new_mon

    def new_stops(self) -> int:
        return self.__get_stat(Stat.UNIQUE_STOPS) * self.first_stop

    def spun_stops(self) -> float:
        stops = self.__get_stat(Stat.STOPS)
        base = stops * self.spin_stop
        bonus = stops / 15 * self.stop_bonus_10
        return base + bonus

    def eggs(self) -> float:
        eggs = self.__get_stat(Stat.HATCHED)
        km2 = eggs * 0.46 * self.egg_2km
        km5 = eggs * 0.26 * self.egg_5km
        km10 = eggs * 0.16 * self.egg_10km
        km7 = eggs * 0.06 * self.egg_7km
        km12 = eggs * 0.06 * self.egg_12km
        return km2 + km5 + km7 + km10 + km12

    def legendary_raids(self) -> int:
        return self.__get_stat(Stat.LEGENDARY_RAIDS_WON) * self.raid_5

    def normal_raids(self) -> float:
        normal = self.__get_stat(Stat.NORMAL_RAIDS_WON)
        lvl1 = normal * 0.225 * self.raid_1
        lvl2 = normal * 0.225 * self.raid_2
        lvl3 = normal * 0.225 * self.raid_3
        lvl4 = normal * 0.225 * self.raid_4
        lvl6 = normal * 0.1 * self.raid_5
        return lvl1 + lvl2 + lvl3 + lvl4 + lvl6

    def best_friends(self) -> int:
        return self.__get_stat(Stat.BEST_FRIENDS) * self.best_friend

    def berries(self) -> int:
        return self.__get_stat(Stat.BERRIES_FED) * self.feed_defender

    def gyms(self) -> float:
        battles = self.__get_stat(Stat.GYM_BATTLES_WON)
        empty = battles / 3 * self.empty_gym
        defeat = battles / 2 * self.defeat_gym_mon
        return empty + defeat


class TrueXP2020(TrueXP):
    curveball = 20
    throw_nice = 20
    throw_great = 100
    throw_excellent = 1000

    spin_stop = 100
    stop_bonus_10 = 100
    first_stop = 250

    egg_2km = 500
    egg_5km = 1000
    egg_7km = 1500
    egg_10km = 2000
    egg_12km = 4000

    new_mon = 1000
    evolve = 1000

    daily_mon = 1500
    weekly_mon = 6000

    raid_1 = 3500
    raid_2 = raid_1
    raid_3 = 5000
    raid_4 = raid_3
    raid_5 = 10000

    defeat_gym_mon = 300
    empty_gym = 1000
    feed_defender = 50

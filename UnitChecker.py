import random
from enum import Enum

import sc2
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.units import Units

from IPython import embed

MARINE = 0
MEDIVAC = 1
MARAUDER = 2
REAPER = 3
SIEGETANK = 4

ATTACK = True
DEFENSE = False

class checker(object):
    def __init__(self, bot_ai):
        self.bot = bot_ai

        self.our_tags = dict()
        self.enemy_tags = dict()

        self.our_total = 0
        self.enemy_total = 0

        self.our_units = [5, 0, 0, 0, 0]        # 맨 처음 마린 5기씩
        self.enemy_units = [5, 0, 0, 0, 0]

        self.unit_turn = (MARINE, MEDIVAC,
                            MARINE, MARAUDER,
                            MARINE, MARAUDER,
                            MARINE, REAPER,
                            MARINE, SIEGETANK)
        self.enemy_unit_turn = 0
        self.our_unit_turn = 0

        #  A     B
        #     C
        #  D     E
        self.strategic_points = [
            #        x   y   z
            Point3((28, 60, 12)),  # A
            Point3((63, 65, 10)),  # B
            Point3((44, 44, 10)),  # C
            Point3((24, 22, 10)),  # D
            Point3((59, 27, 12)),  # E
        ]
    
    def state_in_float(self):
        list_in_float = self.make_data()

        for i in range(15):
            list_in_float[i] = float(list_in_float[i])

        return list_in_float

    def step(self):
        enemy = self.bot.known_enemy_units()
        for unit in enemy:
            if unit.tag not in self.enemy_tags.keys():
                self.enemy_tags[unit.tag] = unit.type_id

        self.our_units[0] = self.bot.units.of_type(UnitTypeId.MARINE).owned().amount
        self.our_units[1] = self.bot.units.of_type(UnitTypeId.MEDIVAC).owned().amount
        self.our_units[2] = self.bot.units.of_type(UnitTypeId.MARAUDER).owned().amount
        self.our_units[3] = self.bot.units.of_type(UnitTypeId.REAPER).owned().amount
        self.our_units[4] = self.bot.units.of_type(UnitTypeId.SIEGETANK).owned().amount + \
            self.bot.units.of_type(UnitTypeId.SIEGETANKSIEGED).owned().amount

    def make_data(self):
        # 아군
        result = list()

        center_foes = list()
        center_foes.append(self.bot.known_enemy_units.of_type(UnitTypeId.MARINE).closer_than(9,self.strategic_points[2]).amount)
        center_foes.append(self.bot.known_enemy_units.of_type(UnitTypeId.MEDIVAC).closer_than(9,self.strategic_points[2]).amount)
        center_foes.append(self.bot.known_enemy_units.of_type(UnitTypeId.MARAUDER).closer_than(9,self.strategic_points[2]).amount)
        center_foes.append(self.bot.known_enemy_units.of_type(UnitTypeId.REAPER).closer_than(9,self.strategic_points[2]).amount)
        center_foes.append(self.bot.known_enemy_units.of_type(UnitTypeId.SIEGETANK).closer_than(9,self.strategic_points[2]).amount + \
            self.bot.known_enemy_units.of_type(UnitTypeId.SIEGETANKSIEGED).closer_than(9,self.strategic_points[2]).amount)

        if self.bot.start_location.distance2_to(self.strategic_points[0]) < 3:
            base = self.strategic_points[0]
            forecourt = self.strategic_points[1]
        else:
            base = self.strategic_points[4]
            forecourt = self.strategic_points[3]

        rushed_foes = list()
        rushed_foes.append((self.bot.known_enemy_units.of_type(UnitTypeId.MARINE).closer_than(15,base) | self.bot.known_enemy_units.of_type(UnitTypeId.MARINE).closer_than(15,forecourt)).amount)
        rushed_foes.append((self.bot.known_enemy_units.of_type(UnitTypeId.MEDIVAC).closer_than(15,base) | self.bot.known_enemy_units.of_type(UnitTypeId.MEDIVAC).closer_than(15,forecourt)).amount)
        rushed_foes.append((self.bot.known_enemy_units.of_type(UnitTypeId.MARAUDER).closer_than(15,base) | self.bot.known_enemy_units.of_type(UnitTypeId.MARAUDER).closer_than(15,forecourt)).amount)
        rushed_foes.append((self.bot.known_enemy_units.of_type(UnitTypeId.REAPER).closer_than(15,base) | self.bot.known_enemy_units.of_type(UnitTypeId.REAPER).closer_than(15,forecourt)).amount)
        rushed_foes.append((self.bot.known_enemy_units.of_type(UnitTypeId.SIEGETANK).closer_than(15,base) | self.bot.known_enemy_units.of_type(UnitTypeId.SIEGETANK).closer_than(15,forecourt)).amount + \
            (self.bot.known_enemy_units.of_type(UnitTypeId.SIEGETANKSIEGED).closer_than(15,base) | self.bot.known_enemy_units.of_type(UnitTypeId.SIEGETANKSIEGED).closer_than(15,forecourt)).amount)


        base_foes = list()
        for i in range(5):
            base_foes.append(self.enemy_units[i] - center_foes[i] - rushed_foes[i])

        result = self.our_units + center_foes + rushed_foes + base_foes
        return result


    def eval(self):     # 미네랄양이 바뀔때마다 실행
        enemy_gas = 0
        for point in self.strategic_points:
            if ( self.bot.units.closer_than(7, point).amount ) <= 0:
                enemy_gas += 1
                if point[0] == 63 or point[0] == 24:
                    enemy_gas += 1

        self.enemy_total += enemy_gas

        if self.enemy_total >= 10:
            self.enemy_total -= 10
            self.enemy_units[self.unit_turn[self.enemy_unit_turn] % 5] += 1
            self.enemy_unit_turn = (self.enemy_unit_turn + 1) % 10

    def remove_killed_unit(self, corpse: int):
        killed_type = None
        killed_enemy = False

        if corpse in self.enemy_tags.keys():
            killed_enemy = True
            killed_type = self.enemy_tags[corpse]
            if killed_type == UnitTypeId.MARINE:
                self.enemy_units[MARINE] -= 1
            elif killed_type == UnitTypeId.MARAUDER:
                self.enemy_units[MARAUDER] -= 1
            elif killed_type == UnitTypeId.MEDIVAC:
                self.enemy_units[MEDIVAC] -= 1
            elif killed_type == UnitTypeId.REAPER:
                self.enemy_units[REAPER] -= 1
            elif killed_type == UnitTypeId.SIEGETANK or \
                killed_type == UnitTypeId.SIEGETANKSIEGED:
                self.enemy_units[SIEGETANK] -= 1
            del self.enemy_tags[corpse]

        return killed_enemy, killed_type

    def power_calc(self):
        our_power = self.our_units[MARINE] + 2 * self.our_units[MARAUDER] + 3 * self.our_units[REAPER] + \
            5 * self.our_units[SIEGETANK] + 4 * self.our_units[MEDIVAC]

        enemy_power = self.enemy_units[MARINE] + 2 * self.enemy_units[MARAUDER] + 3 * self.enemy_units[REAPER] + \
            5 * self.enemy_units[SIEGETANK] + 4 * self.enemy_units[MEDIVAC]

        return (our_power - enemy_power)
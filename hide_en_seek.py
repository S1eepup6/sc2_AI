import random
from enum import Enum

import sc2
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.units import Units

from IPython import embed

#  A     B
#     C
#  D     E
strategic_points = [
    #        x   y   z
    Point3((28, 60, 12)),  # A
    Point3((63, 65, 10)),  # B
    Point3((44, 44, 10)),  # C
    Point3((24, 22, 10)),  # D
    Point3((59, 27, 12)),  # E
]

class disturb_and_defense(object):
    def __init__(self, bot_ai):
        self.bot = bot_ai
        self.troop_names = ["disturb", "defense"]
        self.troops = dict()        # unit_tag(int) : troop_name
        self.inv_troops = {"disturb" : list(), "defense" : list()}

        self.watchers = [-1, -1, -1]

        self.complete = False
        self.medivac_time = dict()

        self.opposite_saw = False

        self.end = False

    def reset(self):
        pass

    def decide_troop(self, unit):
        if (unit.type_id == UnitTypeId.MEDIVAC):
            self.medivac_time[unit.tag] = -14
            already = False
            for t in self.inv_troops["disturb"]:
                temp = self.bot.units.owned.filter(lambda u : u.tag == t)
                if (temp.amount > 0) and (temp.first.type_id == UnitTypeId.MEDIVAC):
                    already = True
                    break

            if already is False:
                self.assign("disturb", unit.tag)

        elif unit.type_id == UnitTypeId.MARINE:
            if self.complete is False:
                if len(self.inv_troops["disturb"]) < 2:
                    self.assign("disturb", unit.tag)
            else:
                self.assign("defense", unit.tag)
                if (self.watchers[0] == -1) and (unit.type_id == UnitTypeId.MARINE):
                    self.watchers[0] = unit.tag
                elif (self.watchers[1] == -1) and (unit.type_id == UnitTypeId.MARINE):
                    self.watchers[1] = unit.tag
                elif (self.watchers[2] == -1) and (unit.type_id == UnitTypeId.MARINE):
                    self.watchers[1] = unit.tag

        else:
            self.assign("defense", unit.tag)


    def assign(self, troop_name, unit_tag):
        if unit_tag in self.troops.keys():
            self.inv_troops[self.troops[unit_tag]].remove(unit_tag)
            del self.troops[unit_tag]
        if troop_name in self.troop_names:
            self.troops[unit_tag] = troop_name
            self.inv_troops[troop_name].append(unit_tag)
        else:
            print("Error in strategy/assign")

    async def step(self):
        if self.bot.start_location.distance2_to(strategic_points[0]) < 3:
            wait_point = Point2((21.21, 51.56))
            hide_point = Point2((19.89, 18.56))
        else:
            wait_point = Point2((67.57, 36.68))
            hide_point = Point2((68.16, 69.35))

        if self.complete is True:
            for t in self.inv_troops["disturb"]:
                temp = self.bot.units.owned.filter(lambda u : u.tag == t)
                if temp.amount > 0:
                    temp = temp.first
                    if (temp.type_id == UnitTypeId.MARINE and temp.position3d[2] > 11) or \
                         temp.type_id == UnitTypeId.MEDIVAC and temp.distance_to( wait_point ) < 3:
                        self.assign("defense", temp.tag)
        if (self.complete is True) and ( self.bot.units.closer_than(5, hide_point).of_type(UnitTypeId.MARINE).amount <= 0 ):
            self.end = True
        if (self.complete is False) and (self.bot.known_enemy_units.filter(lambda u : u.is_structure is False).closer_than(8, hide_point).amount > 3):
            self.opposite_saw = True
        actions = list()
        units = self.bot.units.owned
        for unit_tag in units.tags:
            a = self.get_orders(unit_tag)
            if a is not None:
                actions.append(a)
        return actions

    def get_orders(self, unit_tag):
        enemy = self.bot.known_enemy_units
        ################### postions #####################
        center = strategic_points[2]
        base = self.bot.start_location
        upper_bush = Point3(((base.x + center.x) / 2, (base.y + center.y) / 2, 12))
        our_bush = Point2(
                    (
                        (base.x + center.x * 4) / 5, (base.y + center.y * 4) / 5
                    )
                )
        bush_backward = Point3(
                    ((base.x * 2 + center.x * 3) / 5, (base.y * 2 + center.y * 3) / 5, 10)
                )
        bush_center = Point2(
            (
                (bush_backward.x + our_bush.x) / 2, (bush_backward.y + our_bush.y) / 2
            )
        )

        if self.bot.start_location.distance2_to(strategic_points[0]) < 3:   # base is upper
            wait_point = Point2((21.21, 51.56))
            hide_point = Point2((19.89, 18.56))
            deeper_point = Point2((18.84, 17.86))
            doghole = Point2((15.21, 28.99))
            dest = Point2((15.6, 18.84))
            bunkerplace=Point3((47.5,47.5,9.999828))
            rally_point = Point2((50.61, 49.56))
            when_seen = Point3((28.6, 46, 10))
        else:                                                               # base is lower
            wait_point = Point2((67.57, 36.68))
            hide_point = Point2((68.16, 69.35))
            deeper_point = Point2((69.75, 71.33))
            doghole = Point2((73.91, 59.28))
            dest = Point2((72.83, 69.28))
            bunkerplace=Point3((40.5,40.5,10))
            rally_point = Point2((38.83, 38.88))
            when_seen = Point3((59.4, 41.3, 10))
        ###################### postions #####################

        ############ Condition for Medivac ############
        if self.bot.units.closer_than(5, hide_point).of_type(UnitTypeId.MARINE).amount > 1:
            self.complete = True
        ############ Condition for Medivac ############

        unit = self.bot.units.owned.filter(lambda u : u.tag == unit_tag).first
        action = None

        if unit_tag in self.troops.keys():
            if self.troops[unit_tag] == "disturb":

                ############### MARINE ################
                if unit.type_id == UnitTypeId.MARINE:
                    if unit.distance_to(self.bot.start_location) < 13:
                        action = unit.move( wait_point )
                    else:
                        action = unit.move( hide_point )

                ############### MEDIVAC ###############
                elif unit.type_id == UnitTypeId.MEDIVAC:
                    target_pssn = self.bot.units.filter(lambda u: u.position3d.z > 11).of_type(UnitTypeId.MARINE)
                    target_pssn = target_pssn.closer_than(3, wait_point)

                    if unit.distance_to(self.bot.start_location) <= 13 and target_pssn.amount > 0 and self.opposite_saw is False:
                        action = unit(AbilityId.LOAD, target_pssn.closest_to(unit.position))        #마린 태우기
                    else:
                        if self.complete is True:
                            if unit.distance_to( dest ) < 2:
                                action = unit.move( doghole )
                            elif unit.distance_to( doghole ) < 1:
                                action = unit.move( upper_bush )

                        elif self.opposite_saw is True:
                            if unit.distance_to( base ) < 15:
                                action = unit.move( upper_bush )
                                if unit.distance_to(upper_bush) < 1:
                                    action = unit(AbilityId.UNLOADALLAT_MEDIVAC, upper_bush)
                            else:
                                action = unit.move( when_seen )

                        else:
                            if unit.distance_to(self.bot.start_location) <= 13 and len(unit.passengers) > 0:
                                action = unit.move( doghole )                               # 우회해서
                            elif unit.distance_to( doghole ) < 1:
                                action = unit(AbilityId.UNLOADALLAT, dest)

                        if enemy.filter(lambda u : u.is_structure is False).closer_than(6, unit.position).amount > 3:
                            if self.complete is False:
                                self.opposite_saw = True
                            if self.bot.time - self.medivac_time[unit.tag] > 14:
                                action = unit(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS)
                                self.medivac_time[unit.tag] = self.bot.time
                            else:
                                action = unit.move( self.bot.start_location )               # 적 오면 도망

                        if self.bot.time - self.medivac_time[unit.tag] > 14:
                            action = unit(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS)
                            self.medivac_time[unit.tag] = self.bot.time

            elif self.troops[unit_tag] == "defense":
                if unit.type_id == UnitTypeId.MARINE:
                    if base.distance2_to(strategic_points[0]) < 3:
                        action = unit.attack(upper_bush)
                        if self.bot.known_enemy_units.closer_than(13, base):
                            action = unit.attack(self.bot.known_enemy_units.closest_to(base))
                        elif ( self.bot.known_enemy_units.closer_than(12, strategic_points[1]) or self.bot.vespene <= 2 ) and \
                            ( self.watchers[0] == unit.tag or self.watchers[1] == unit.tag or self.watchers[2] == unit.tag ):
                            spy = self.bot.known_enemy_units.closer_than(12, strategic_points[1])
                            if spy.amount > 0:
                                action = unit.attack(spy.closest_to(unit))
                            else:
                                action = unit.attack(strategic_points[1])
                    else:
                        action = unit.attack(upper_bush)
                        if self.bot.known_enemy_units.closer_than(13, base):
                            action = unit.attack(base)
                        elif ( self.bot.known_enemy_units.closer_than(12, strategic_points[3]) or self.bot.vespene <= 2 ) and \
                            ( self.watchers[0] == unit.tag or self.watchers[1] == unit.tag or self.watchers[2] == unit.tag ):
                            spy = self.bot.known_enemy_units.closer_than(12, strategic_points[3])
                            if spy.amount > 0:
                                action = unit.attack(spy.closest_to(unit))
                            else:
                                action = unit.attack(strategic_points[3])

                elif unit.type_id == UnitTypeId.MARAUDER:
                    if unit.position3d.z > 11:
                        action = unit.move(upper_bush)
                        if self.bot.known_enemy_units.closer_than(13, base).amount > 0:
                            action = unit.attack(self.bot.known_enemy_units.closest_to(base))
                    else:
                        action = unit.move(bunkerplace)
                    bunker = self.bot.units.owned.of_type(UnitTypeId.BUNKER).filter(lambda u : u.position3d.x > 40 and u.position3d.x < 50)
                    if bunker.amount == 0:
                        action = unit.move(base)

                elif unit.type_id == UnitTypeId.BUNKER and unit.position3d.x > 40 and unit.position3d.x < 50:
                    action = unit(AbilityId.RALLY_BUILDING, rally_point)

                    target_pssn = self.bot.units.filter(lambda u: u.distance_to(unit.position) <= 3).of_type(UnitTypeId.MARAUDER)
                    enemy = self.bot.known_enemy_units.filter(lambda u : u.distance_to(unit.position) <= 9 and u.is_structure is False)
                    enemy_structure = self.bot.known_enemy_structures.filter(lambda u : u.distance_to(unit.position) <= 13)
                    if target_pssn.amount > 0:
                        action = unit(AbilityId.LOAD, target_pssn.closest_to(unit.position))
                    elif enemy.amount > 0:
                        action = unit.attack(enemy.closest_to(unit))
                    elif enemy_structure.amount > 0:
                        action = unit.attack(enemy_structure.closest_to(unit))

                elif unit.type_id == UnitTypeId.MEDIVAC:
                    if unit.distance_to(upper_bush) > 3:
                        action = unit.move(upper_bush)
                    else:
                        if self.bot.known_enemy_units.closer_than(13, base).amount > 0:
                            action = unit.move(base)
                        else:
                            target_pssn = self.bot.units.filter(lambda u: u.position3d.z > 11).of_type(UnitTypeId.MARAUDER)
                            target_pssn = target_pssn.closer_than(2, upper_bush)
                            if len(unit.passengers) > 0:
                                action = unit(AbilityId.UNLOADALLAT,bush_backward)
                            if target_pssn and len(unit.passengers) < 1:
                                action = unit(AbilityId.LOAD, target_pssn.closest_to(unit.position))

                elif unit.type_id == UnitTypeId.SIEGETANK:
                    if self.bot.known_enemy_units.closer_than(13, base).amount > 0:
                        action = unit.attack(self.bot.known_enemy_units.closest_to(base))
        else:
            self.assign("defense", unit.tag)
            if (self.watchers[0] == -1) and (unit.type_id == UnitTypeId.MARINE):
                self.watchers[0] = unit.tag
            elif (self.watchers[1] == -1) and (unit.type_id == UnitTypeId.MARINE):
                self.watchers[1] = unit.tag
            elif (self.watchers[2] == -1) and (unit.type_id == UnitTypeId.MARINE):
                self.watchers[2] = unit.tag


        if action is not None:
            return action
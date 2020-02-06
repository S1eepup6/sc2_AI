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

class min_atk(object):
    def __init__(self, bot_ai):
        self.bot = bot_ai
        self.end = False

        center = strategic_points[2]
        base = self.bot.start_location

        self.debug_position_unit = Point3(((base.x + center.x) / 2, (base.y + center.y) / 2, 12))
        self.debug_position_medi = Point2(
                    (
                        (base.x + center.x * 4) / 5, (base.y + center.y * 4) / 5
                    )
                )

        self.line = 0

        self.base_reaper = list()
        self.fore_reaper = list()

    def reset(self, possibly_end):
        ################### postions #####################
        center = strategic_points[2]
        base = self.bot.start_location
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

        if base.distance2_to(strategic_points[0]) < 3:
            enemy_base = strategic_points[4]
            forecourt = strategic_points[1]
            enemy_another = Point2((43.90, 34.22))
        else:
            enemy_base = strategic_points[0]
            forecourt = strategic_points[3]
            enemy_another = Point2((42.96, 53.79))

        enemy_bush = Point2(
                    (
                        (enemy_base.x + center.x * 4) / 5, (enemy_base.y + center.y * 4) / 5
                    )
                )
        enemy_front = Point3(
                    ((enemy_base.x * 2 + center.x * 3) / 5, (enemy_base.y * 2 + center.y * 3) / 5, 10)
                )                             
        ###################### postions ######################
        if self.bot.units.closer_than(3, self.debug_position_unit).amount > 3:
            if self.bot.known_enemy_units.exclude_type({UnitTypeId.MEDIVAC}).closer_than(7, center).amount < 5 and self.bot.known_enemy_units.of_type({UnitTypeId.SIEGETANKSIEGED}).amount == 0:
                self.line = 1

        if self.bot.units.owned.closer_than(9, center).amount >= 15 and self.bot.units.owned.of_type({UnitTypeId.SIEGETANK, UnitTypeId.SIEGETANKSIEGED}).amount >= 2 and \
            self.bot.known_enemy_units.closer_than(6, enemy_bush).amount == 0 and self.bot.known_enemy_units.closer_than(2, enemy_another).amount == 0 and \
                self.bot.units.owned.of_type(UnitTypeId.MEDIVAC).closer_than(3, enemy_bush).amount >= 1 and \
                possibly_end is True :
            self.line = 2


    async def step(self):
        if self.bot.start_location.distance2_to(strategic_points[0]) < 3:
            wait_point = Point2((21.21, 51.56))
            hide_point = Point2((19.89, 18.56))
        else:
            wait_point = Point2((67.57, 36.68))
            hide_point = Point2((68.16, 69.35))

        actions = list()
        units = self.bot.units.owned
        for unit_tag in units.tags:
            a = await self.get_orders(unit_tag)
            if a is not None:
                actions.append(a)
        return actions

    async def get_orders(self, unit_tag):
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

        if base.distance2_to(strategic_points[0]) < 3:
            enemy_base = strategic_points[4]
        else:
            enemy_base = strategic_points[0]

        enemy_bush = Point2(
                    (
                        (enemy_base.x + center.x * 4) / 5, (enemy_base.y + center.y * 4) / 5
                    )
                )
        enemy_front = Point3(
                    ((enemy_base.x * 2 + center.x * 3) / 5, (enemy_base.y * 2 + center.y * 3) / 5, 10)
                )
        if self.bot.start_location.distance2_to(strategic_points[0]) < 3:   # base is upper
            wait_point = Point2((21.21, 51.56))
            hide_point = Point2((19.89, 18.56))
            deeper_point = Point2((18.84, 17.86))
            dest = Point2((15.6, 18.84))
            bunkerplace=Point3((47.5,47.5,9.999828))
            rally_point = Point2((50.61, 49.56))
            forecourt = strategic_points[1]
            ready_point = Point3((28.6, 46, 10))
            defense_ready = Point2((29.15, 49.27))
            center_watch = Point2((38.30, 36.37))
            another_tank = Point2((42.96, 53.79))
            enemy_another = Point2((43.90, 34.22))
        else:                                                               # base is lower
            wait_point = Point2((67.57, 36.68))
            hide_point = Point2((68.16, 69.35))
            deeper_point = Point2((69.75, 71.33))
            dest = Point2((72.83, 69.28))
            bunkerplace=Point3((40.5,40.5,10))
            rally_point = Point2((38.83, 38.88))
            forecourt = strategic_points[3]
            ready_point = Point3((59.4, 41.3, 10))
            defense_ready = Point2((58.72, 37.98))
            center_watch = Point2((49.15, 51.71))
            another_tank = Point2((43.90, 34.22))
            enemy_another = Point2((42.96, 53.79))

        forecourt_def = Point2(
            ((enemy_base.x + forecourt.x) / 2, (enemy_base.y + forecourt.y * 3) / 4)
        )
        ###################### postions ######################

        if self.line == 0:
            units_line = upper_bush
            medivac_line = our_bush
        elif self.line == 1:
            units_line = bush_center
            medivac_line = enemy_bush
        elif self.line == 2:
            units_line = enemy_front
            medivac_line = enemy_front

        self.debug_position_unit = units_line
        self.debug_position_medi = medivac_line

        unit = self.bot.units.owned.filter(lambda u : u.tag == unit_tag).first
        action = None

        if unit.type_id == UnitTypeId.MARINE:
            if base.distance2_to(strategic_points[0]) < 3:
                action = unit.attack(units_line)
                if self.bot.known_enemy_units.closer_than(13, base):
                    action = unit.attack(self.bot.known_enemy_units.closest_to(base))
                elif ( self.bot.known_enemy_units.closer_than(12, strategic_points[1]) or self.bot.vespene <= 2 ):
                    spy = self.bot.known_enemy_units.closer_than(12, strategic_points[1])
                    if spy.amount > 0:
                        action = unit.attack(spy.closest_to(unit))
                    else:
                        action = unit.attack(strategic_points[1])
            else:
                action = unit.attack(units_line)
                if self.bot.known_enemy_units.closer_than(13, base):
                    action = unit.attack(base)
                elif ( self.bot.known_enemy_units.closer_than(12, strategic_points[3]) or self.bot.vespene <= 2 ):
                    spy = self.bot.known_enemy_units.closer_than(12, strategic_points[3])
                    if spy.amount > 0:
                        action = unit.attack(spy.closest_to(unit))
                    else:
                        action = unit.attack(strategic_points[3])

            if unit.distance_to(hide_point) < 3:
                action = unit.hold_position()

        elif unit.type_id == UnitTypeId.MARAUDER:
            if unit.position3d.z > 11:
                action = unit.move(units_line)
                if self.bot.known_enemy_units.closer_than(13, base).amount > 0:
                    action = unit.attack(self.bot.known_enemy_units.closest_to(base))
            else:
                action = unit.move(bunkerplace)
            bunker = self.bot.units.owned.of_type(UnitTypeId.BUNKER).filter(lambda u : u.position3d.x > 40 and u.position3d.x < 50)
            if bunker.amount == 0:
                if self.bot.known_enemy_units.closer_than(9, center).amount < 3:
                    action = unit.attack(our_bush)
                else:
                    action = unit.attack(forecourt)


        elif unit.type_id == UnitTypeId.BUNKER and unit.position3d.x > 40 and unit.position3d.x < 50:
            action = unit(AbilityId.RALLY_BUILDING, rally_point)

            target_pssn = self.bot.units.filter(lambda u: u.distance_to(unit.position) <= 3).of_type(UnitTypeId.MARAUDER)
            enemy = self.bot.known_enemy_units.filter(lambda u : u.distance_to(unit.position) <= 9 and u.is_structure is False)
            enemy_structure = self.bot.known_enemy_structures.filter(lambda u : u.distance_to(unit.position) <= 13)
            if target_pssn.amount > 0:
                action = unit(AbilityId.LOAD, target_pssn.closest_to(unit.position))
            elif enemy_structure.amount > 0:
                action = unit.attack(enemy_structure.closest_to(unit))
            elif enemy.amount > 0:
                action = unit.attack(enemy.closest_to(unit))

        elif unit.type_id == UnitTypeId.MEDIVAC:
            injured = self.bot.units.exclude_type({UnitTypeId.MEDIVAC})
            if injured.empty is False:
                injured = injured.filter(lambda u: u.health_percentage < 1 and u.is_structure is False)
            enemy_bunker = self.bot.known_enemy_structures.filter(lambda u: u.type_id == UnitTypeId.BUNKER and u.position3d.x > 40 and u.position3d.x < 50)

            if enemy_bunker.amount == 0 and unit.distance_to(medivac_line) > 3:
                action = unit.move(medivac_line)
            elif enemy_bunker.amount > 0 and unit.distance_to(units_line) > 3:
                action = unit.move(units_line)

            if injured.empty is False and unit.distance_to(injured.closest_to(unit)) < 15:
                action = unit(AbilityId.MEDIVACHEAL_HEAL, injured.closest_to(unit))

            if self.bot.known_enemy_structures.closer_than(6, unit).empty is False:
                action = unit.move(units_line)

        elif unit.type_id == UnitTypeId.SIEGETANK:
            if self.bot.known_enemy_units.closer_than(13, base).amount > 0:
                action = unit.attack(self.bot.known_enemy_units.closest_to(base))
            elif unit.distance_to(units_line) > 3 or (unit.position3d.z > 11 and self.line == 1):
                action = unit.move(units_line)
            else:
                action = unit(AbilityId.SIEGEMODE_SIEGEMODE)

        elif unit.type_id == UnitTypeId.SIEGETANKSIEGED:
            if self.bot.known_enemy_units.closer_than(13, base).amount > 0 and self.bot.known_enemy_units.closer_than(13, unit.position).amount < 1:
                action = unit(AbilityId.UNSIEGE_UNSIEGE)
            if self.line == 1 and unit.position3d.z > 11:
                action = unit(AbilityId.UNSIEGE_UNSIEGE)
            if self.line == 2 and unit.distance_to(our_bush) < unit.distance_to(enemy_front):
                action = unit(AbilityId.UNSIEGE_UNSIEGE)

        elif unit.type_id == UnitTypeId.REAPER:
            if unit.tag not in self.base_reaper and unit.tag not in self.fore_reaper:
                if len(self.base_reaper) <= len(self.fore_reaper):
                    self.base_reaper.append(unit.tag)
                else:
                    self.fore_reaper.append(unit.tag)

            threaten = self.bot.known_enemy_units.closer_than(10, unit.position)
            center_threat = self.bot.known_enemy_units.closer_than(8, center) | self.bot.known_enemy_units.closer_than(8, center_watch)
            rushed_enemy = self.bot.known_enemy_units.closer_than(13, base)

            min_mana = 50

            if unit.distance_to(forecourt_def) < 5 and unit.tag in self.fore_reaper and self.bot.known_enemy_units.of_type(UnitTypeId.AUTOTURRET).closer_than(5, forecourt_def).amount > 0 and \
                self.bot.units.of_type(UnitTypeId.AUTOTURRET).closer_than(5, forecourt_def).amount >= self.bot.known_enemy_units.of_type(UnitTypeId.AUTOTURRET).closer_than(5, forecourt_def).amount:
                action = unit.move(forecourt)
            if unit.distance_to(ready_point) < 3 and self.bot.known_enemy_units.of_type(UnitTypeId.MEDIVAC).closer_than(5, unit.position).amount > 0 and unit.energy > 100:
                closest_threat = self.bot.known_enemy_units.of_type(UnitTypeId.MEDIVAC).closer_than(5, unit.position).closest_to(unit.position)
                pos = ready_point
                pos = await self.bot.find_placement(UnitTypeId.AUTOTURRET, pos)
                action = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
            elif unit.health_percentage > 0.3 and unit.energy > 50:
                if threaten.amount > 0:
                    if unit.energy >= min_mana and \
                        unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                        closest_threat = threaten.closest_to(unit.position)
                        pos = Point2(
                            ((unit.position3d.x + closest_threat.position3d.x) / 2 , (unit.position3d.y + closest_threat.position3d.y) / 2)
                        )
                        pos = await self.bot.find_placement(
                            UnitTypeId.AUTOTURRET, pos)
                        action = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                    else:
                        action = unit.attack(threaten.closest_to(unit.position))
                else:
                    if unit.tag in self.base_reaper and unit.distance_to(ready_point) > 5:
                        action = unit.attack(ready_point)
                    elif unit.tag in self.fore_reaper and unit.distance_to(forecourt_def) > 7:
                        action = unit.attack(forecourt_def)
            else:
                if unit.tag in self.base_reaper and unit.distance_to(ready_point) > 5:
                    action = unit.attack(ready_point)
                elif unit.tag in self.fore_reaper and unit.distance_to(forecourt_def) > 7:
                    action = unit.attack(forecourt_def)

            if center_threat.amount > 5:
                if unit.distance_to(center) > 4:
                    action = unit.attack(center)
                
            if rushed_enemy.amount > 0:
                if unit.energy >= min_mana:
                    if rushed_enemy.amount >= 1 and \
                        unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                            closest_threat = rushed_enemy.closest_to(unit.position)
                            pos = Point2(
                                ((unit.position3d.x + closest_threat.position3d.x) / 2 , (unit.position3d.y + closest_threat.position3d.y) / 2)
                            )
                            pos = await self.bot.find_placement(UnitTypeId.AUTOTURRET, pos)
                            action = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                    else:
                        action = unit.attack(rushed_enemy.closest_to(unit.position))
                else:
                    action = unit.attack(rushed_enemy.closest_to(unit.position))

            if unit.energy >= min_mana and \
                unit.orders and unit.orders[0].ability.id == AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                if not(unit.distance_to(ready_point) < 3 and self.bot.known_enemy_units.of_type(UnitTypeId.MEDIVAC).closer_than(5, unit.position).amount > 0 and unit.energy > 100):
                    action = None

        if action is not None:
            return action
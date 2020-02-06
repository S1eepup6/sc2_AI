import random
from enum import Enum

import sc2
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.units import Units

from IPython import embed

from .UnitChecker import checker

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


class target_attack(object):
    def __init__(self, bot_ai, target):
        self.bot = bot_ai
        self.target = None
        self.perimeter_radius = 13

        self.units = None
        self.enemy = None

        self.push_to_forecourt = False
        self.push_to_base = False

        self.arrival = list()
        self.atk_start = False

        self.reset(target)

    def reset(self, target):
        self.target = target

        if self.target == Point2((68.16, 69.35)) or self.target == Point2((19.89, 18.56)):
            self.push_to_forecourt = True
        elif self.target == Point3((28, 60, 12)) or self.target == Point3((59, 27, 12)):
            self.push_to_base = True
        else:
            self.push_to_forecourt = False
            self.push_to_base = False

        self.enemy = self.bot.known_enemy_units
        self.units = self.bot.units.owned

    async def step(self):
        actions = list()
        if len(self.arrival) >= self.units.owned.filter(lambda u : u.is_structure is False).amount - 3:
            self.atk_start = True
        for u in self.bot.units:
            plus = await self.common_step(u, self.units.owned.filter(lambda u : u.is_structure is False), self.enemy)
            actions += plus

        return actions


    async def common_step(self, unit, friends, foes):
        actions = list()
        ###################### postions #####################
        center = strategic_points[2]
        if self.bot.start_location.distance2_to(strategic_points[0]) < 3:
            base = strategic_points[0]
            forecourt = strategic_points[1]
            base = strategic_points[0]
            enemy_base = strategic_points[4]
            ready_point = Point3((23.89, 42.65, 10))
            hide_point = Point2((19.89, 18.56))
        else:
            base = strategic_points[4]
            forecourt = strategic_points[3]
            base = strategic_points[4]
            enemy_base = strategic_points[0]
            ready_point = Point3((63.64, 45.36, 10))
            hide_point = Point2((68.16, 69.35))
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

        if (self.push_to_forecourt == True or self.push_to_base == True) and self.atk_start == False and \
            (self.bot.known_enemy_units.closer_than(9, unit).amount < 1):
            if unit.distance_to(ready_point) <= 6:
                exist = False
                for i in self.arrival:
                    if i == unit.tag:
                        exist = True
                if exist == False:
                    self.arrival.append(unit.tag)

            elif unit.distance_to(ready_point) > 5:
                if unit.type_id == UnitTypeId.SIEGETANKSIEGED:
                    actions.append(unit(AbilityId.UNSIEGE_UNSIEGE))
                else:
                    actions.append(unit.move(ready_point))

        elif unit.type_id == UnitTypeId.BUNKER:
            if self.bot.units.closer_than(2, unit).of_type(UnitTypeId.MARAUDER).amount > 0:
                actions.append(unit(AbilityId.LOAD_BUNKER, self.bot.units.closer_than(2, unit).of_type(UnitTypeId.MARAUDER).closest_to(unit)))
            elif self.bot.units.closer_than(2, unit).of_type(UnitTypeId.MARINE).amount > 0:
                actions.append(unit(AbilityId.LOAD_BUNKER, self.bot.units.closer_than(2, unit).of_type(UnitTypeId.MARINE).closest_to(unit)))


        elif unit.type_id == UnitTypeId.MARINE:
            can_atk = self.bot.known_enemy_units.in_attack_range_of(unit)

            order = None
            if foes.amount > 0:
                if unit.health_percentage > 0.8 and \
                    not unit.has_buff(BuffId.STIMPACK) :
                    # 스팀팩 사용
                    order = unit(AbilityId.EFFECT_STIM)
                else:
                    # 가장 가까운 목표 공격
                    if (foes.of_type(UnitTypeId.MEDIVAC) & can_atk) :
                        order = unit.attack(foes.of_type({UnitTypeId.MEDIVAC}).closest_to(unit.position))
                    else:
                        if (foes.of_type(UnitTypeId.SIEGETANK) & can_atk) :
                            order = unit.attack(foes.of_type({UnitTypeId.SIEGETANK}).closest_to(unit.position))
                        elif (foes.of_type(UnitTypeId.SIEGETANKSIEGED) & can_atk) :
                            order = unit.attack(foes.of_type({UnitTypeId.SIEGETANKSIEGED}).closest_to(unit.position))
                        else:
                            order = unit.attack(foes.closest_to(unit.position))
            else:
                if unit.distance_to(self.target) > 5:
                    # 어택땅으로 집결지로 이동
                    order = (unit.move(self.target.to2))
                if self.target.distance2_to(center) < 3 and self.bot.units.of_type(UnitTypeId.BUNKER).filter(lambda u: u.position3d.x > 40 and u.position3d.x < 50).empty is False:
                    bunker = self.bot.units.of_type(UnitTypeId.BUNKER).filter(lambda u: u.position3d.x > 40 and u.position3d.x < 50).first
                    if bunker.cargo_used <= bunker.cargo_max - 1:
                        order = unit.move(bunker.position3d)

            if (unit.distance_to(hide_point) < 3) and (self.push_to_forecourt is False):
                order = unit.hold_position()
            if order is not None:
                actions.append(order)

        elif unit.type_id == UnitTypeId.MARAUDER:
            if foes.amount > 0:
                if unit.health_percentage > 0.8 and \
                    not unit.has_buff(BuffId.STIMPACKMARAUDER):
                    # 스팀팩 사용
                    order = unit(AbilityId.EFFECT_STIM_MARAUDER)
                else:
                    # 가장 가까운 목표 공격
                    if foes.of_type(UnitTypeId.SIEGETANKSIEGED).closer_than(10, unit):
                        order = unit.attack(foes.of_type({UnitTypeId.SIEGETANKSIEGED}).closest_to(unit.position))
                    elif foes.of_type(UnitTypeId.SIEGETANK).closer_than(10, unit):
                        order = unit.attack(foes.of_type({UnitTypeId.SIEGETANK}).closest_to(unit.position))
                    else:
                        order = unit.attack(foes.closest_to(unit.position))
                actions.append(order)
            else:
                order = None
                if unit.distance_to(self.target) > 5:
                    # 어택땅으로 집결지로 이동
                    order = (unit.move(self.target.to2))
                if self.target.distance2_to(center) < 3 and self.bot.units.of_type(UnitTypeId.BUNKER).filter(lambda u: u.position3d.x > 40 and u.position3d.x < 50).empty is False:
                    bunker = self.bot.units.of_type(UnitTypeId.BUNKER).filter(lambda u: u.position3d.x > 40 and u.position3d.x < 50).first
                    if bunker.cargo_used <= bunker.cargo_max - 1:
                        order = unit.move(bunker.position3d)
                if order is not None:
                    actions.append(order)

        elif unit.type_id == UnitTypeId.SIEGETANK:
            if foes.amount > 0:
                # 근처에 적이 3이상 있으면 시즈모드
                targets = self.bot.known_enemy_units.closer_than(13, unit.position3d)
                if targets.amount > 3:
                    if len(unit.orders) == 0 or \
                        len(unit.orders) > 0 and unit.orders[0].ability.id not in (AbilityId.SIEGEMODE_SIEGEMODE, AbilityId.UNSIEGE_UNSIEGE):
                        order = unit(AbilityId.SIEGEMODE_SIEGEMODE)
                        actions.append(order)
                else:
                    order = unit.attack(foes.closest_to(unit.position))
                    actions.append(order)
            else:
                if unit.distance_to(self.target) > 5:
                    # 어택땅으로 집결지로 이동
                    order = unit.move(self.target.to2)
                    actions.append(order)
                else:
                    # 대기할 때는 시즈모드로
                    if len(unit.orders) == 0 or \
                        len(unit.orders) > 0 and unit.orders[0].ability.id not in (AbilityId.SIEGEMODE_SIEGEMODE, AbilityId.UNSIEGE_UNSIEGE):
                        order = unit(AbilityId.SIEGEMODE_SIEGEMODE)
                        actions.append(order)

        elif unit.type_id == UnitTypeId.SIEGETANKSIEGED:
            enemys = self.bot.known_enemy_units.closer_than(13, friends.center)
            if enemys.amount < 2:
                if len(unit.orders) == 0 or \
                    len(unit.orders) > 0 and unit.orders[0].ability.id not in (AbilityId.SIEGEMODE_SIEGEMODE, AbilityId.UNSIEGE_UNSIEGE):
                    order = unit(AbilityId.UNSIEGE_UNSIEGE)
                    actions.append(order)

        elif unit.type_id == UnitTypeId.MEDIVAC:
            order = unit.move(friends.center)
            if self.units.owned.closer_than(10, self.target).amount > 5 and unit.distance_to(self.target) > 5:
                order = unit.move(self.target)
            if unit.distance_to(self.target) < 5 and self.units.owned.closer_than(6, unit).amount < 3:
                order = unit.move(self.units.owned.filter(lambda u : u.is_structure is False).center)
            actions.append(order)

        elif unit.type_id == UnitTypeId.REAPER:
            threaten = self.bot.known_enemy_units.closer_than(9, unit.position)
            action = None
            if unit.energy >= 50:
                if threaten.amount > 0:
                    if unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                        closest_threat = threaten.closest_to(unit.position)
                        pos = Point2(
                            ((unit.position3d.x + closest_threat.position3d.x) / 2 , (unit.position3d.y + closest_threat.position3d.y) / 2)
                        )
                        pos = await self.bot.find_placement(UnitTypeId.AUTOTURRET, pos)
                        action = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                else:
                    if unit.distance_to(self.target) > 5:
                        action = unit.attack(self.target)
            else:
                if unit.distance_to(self.target) > 5:
                    action = unit.attack(self.target)

            if unit.energy >= 50 and \
                unit.orders and unit.orders[0].ability.id == AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                action = None

            if unit.health_percentage < 0.3:
                action = unit.move(self.bot.start_location)

            if action is not None:
                actions.append(action)

        
        return actions
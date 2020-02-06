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


class defense(object):
    def __init__(self, bot_ai):
        self.bot = bot_ai
        self.perimeter_radius = 13

        self.units = None
        self.enemy = None

        self.reset()

    def reset(self):

        self.enemy = self.bot.known_enemy_units
        self.units = self.bot.units.owned

    async def step(self):
        actions = list()
        for u in self.bot.units:
            plus = await self.common_step(u, self.units, self.enemy)
            actions += plus

        return actions


    async def common_step(self, unit, friends, foes):
        ###################### postions #####################
        center = strategic_points[2]
        if self.bot.start_location.distance2_to(strategic_points[0]) < 3:
            base = strategic_points[0]
        else:
            base = strategic_points[4]
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
            rally_point = Point2((50.61, 49.56))
            forecourt = strategic_points[1]
            ready_point = Point3((28.6, 46, 10))
            defense_ready = Point2((29.15, 49.27))
        else:                                                               # base is lower
            wait_point = Point2((67.57, 36.68))
            hide_point = Point2((68.16, 69.35))
            deeper_point = Point2((69.75, 71.33))
            doghole = Point2((73.91, 59.28))
            dest = Point2((72.83, 69.28))
            rally_point = Point2((38.83, 38.88))
            forecourt = strategic_points[3]
            ready_point = Point3((59.4, 41.3, 10))
            defense_ready = Point2((58.72, 37.98))
        ###################### postions #####################

        foes = self.bot.known_enemy_units.closer_than(13, forecourt) | self.bot.known_enemy_units.closer_than(13, base)
        enemy_medivacs = self.bot.known_enemy_units.of_type(UnitTypeId.MEDIVAC).closer_than(15, base) | \
            self.bot.known_enemy_units.of_type(UnitTypeId.MEDIVAC).closer_than(5, ready_point)

        actions = list()
        if unit.type_id == UnitTypeId.MARINE:
            can_atk = self.bot.known_enemy_units.in_attack_range_of(unit)

            order = None
            if self.bot.known_enemy_units.closer_than(5, ready_point).amount > 0 or \
                self.bot.known_enemy_units.closer_than(5, defense_ready).amount > 0:
                if unit.position3d.z < 11:
                    order = unit.attack(ready_point)
                else:
                    order = unit.attack(defense_ready)
            elif foes.amount > 0:
                if unit.health_percentage > 0.8 and \
                    not unit.has_buff(BuffId.STIMPACK) :
                    # 스팀팩 사용
                    order = unit(AbilityId.EFFECT_STIM)
                else:
                    # 가장 가까운 목표 공격
                    if (foes.of_type(UnitTypeId.SIEGETANK) & can_atk) :
                        order = unit.attack(foes.of_type({UnitTypeId.SIEGETANK}).closest_to(unit.position))
                    elif (foes.of_type(UnitTypeId.SIEGETANKSIEGED) & can_atk) :
                        order = unit.attack(foes.of_type({UnitTypeId.SIEGETANKSIEGED}).closest_to(unit.position))
                    else:
                        order = unit.attack(foes.closest_to(unit.position))
            else:
                if unit.distance_to(upper_bush) > 3:
                    # 어택땅으로 집결지로 이동
                    order = unit.move(upper_bush)

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
                    if self.bot.known_enemy_units.closer_than(3, ready_point).amount > 0:
                        order = unit.attack(ready_point)
                    if foes.of_type(UnitTypeId.SIEGETANKSIEGED).closer_than(10, unit).amount > 0:
                        order = unit.attack(foes.of_type({UnitTypeId.SIEGETANKSIEGED}).closest_to(unit.position))
                    elif foes.of_type(UnitTypeId.SIEGETANK).closer_than(10, unit).amount > 0:
                        order = unit.attack(foes.of_type({UnitTypeId.SIEGETANK}).closest_to(unit.position))
                    else:
                        order = unit.attack(foes.closest_to(unit.position))
                actions.append(order)
            else:
                if unit.distance_to(forecourt) > 5:
                    # 어택땅으로 집결지로 이동
                    order = unit.move(forecourt)
                    actions.append(order)

        elif unit.type_id == UnitTypeId.SIEGETANK:
            target = base
            if self.bot.known_enemy_units.closer_than(13, base).amount > 0:
                target = base
            elif self.bot.known_enemy_units.closer_than(13, forecourt).amount > 0:
                target = forecourt

            targets = self.bot.known_enemy_units.closer_than(7, friends.center)

            if targets.amount > 3:
                # 근처에 적이 3이상 있으면 시즈모드
                if len(unit.orders) == 0 or \
                    len(unit.orders) > 0 and unit.orders[0].ability.id not in (AbilityId.SIEGEMODE_SIEGEMODE, AbilityId.UNSIEGE_UNSIEGE):
                    order = unit(AbilityId.SIEGEMODE_SIEGEMODE)
                    actions.append(order)
                else:
                    order = unit.attack(foes.closest_to(unit.position))
                    actions.append(order)
            else:
                if target is not None and unit.distance_to(target) > 5:
                    # 어택땅으로 집결지로 이동
                    order = unit.move(target.to2)
                    actions.append(order)
                else:
                    # 대기할 때는 시즈모드로
                    if len(unit.orders) == 0 or \
                        len(unit.orders) > 0 and unit.orders[0].ability.id not in (AbilityId.SIEGEMODE_SIEGEMODE, AbilityId.UNSIEGE_UNSIEGE):
                        order = unit(AbilityId.SIEGEMODE_SIEGEMODE)
                        actions.append(order)

        elif unit.type_id == UnitTypeId.SIEGETANKSIEGED:
            target = None
            if self.bot.known_enemy_units.closer_than(13, base).amount > 0:
                target = base
            elif self.bot.known_enemy_units.closer_than(13, forecourt).amount > 0:
                target = forecourt

            # 목표지점에서 너무 멀리 떨어져 있으면 시즈모드 해제
            if target is not None and unit.distance_to(target.to2) > 10:
                if len(unit.orders) == 0 or \
                    len(unit.orders) > 0 and unit.orders[0].ability.id not in (AbilityId.SIEGEMODE_SIEGEMODE, AbilityId.UNSIEGE_UNSIEGE):
                    order = unit(AbilityId.UNSIEGE_UNSIEGE)
                    actions.append(order)

        elif unit.type_id == UnitTypeId.MEDIVAC:
            injured = self.bot.units.owned.filter(lambda u : u.health_percentage < 1)
            if injured.empty is False:
                if injured.of_type(UnitTypeId.MARAUDER).empty is False:
                    actions.append(unit(AbilityId.MEDIVACHEAL_HEAL, injured.of_type(UnitTypeId.MARAUDER).closest_to(unit)))
                elif injured.of_type(UnitTypeId.MARINE).empty is False:
                    actions.append(unit(AbilityId.MEDIVACHEAL_HEAL, injured.of_type(UnitTypeId.MARINE).closest_to(unit)))
                else:
                    actions.append(unit(AbilityId.MEDIVACHEAL_HEAL, injured.closest_to(unit)))
            elif unit.distance_to(friends.center) > 5:
                actions.append(unit.move(friends.center))

        elif unit.type_id == UnitTypeId.REAPER:
            threaten = self.bot.known_enemy_units.closer_than(
                    13, unit.position)
            if unit.distance_to(base) < 5:
                threaten = threaten | self.bot.known_enemy_units.closer_than(5, defense_ready)
            base_friends = self.bot.units.owned.filter(lambda u: u.distance_to(base) < 5).of_type(UnitTypeId.REAPER)
            forecourt_friends = self.bot.units.owned.filter(lambda u: u.distance_to(forecourt) < 5).of_type(UnitTypeId.REAPER)

            if unit.health_percentage > 0.2 and unit.energy >= 50:
                if threaten.amount > 0:
                    if unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                        closest_threat = threaten.closest_to(unit.position)
                        pos = unit.position.towards(closest_threat.position, 5)
                        pos = await self.bot.find_placement(
                            UnitTypeId.AUTOTURRET, pos)
                        order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                        actions.append(order)
                else:
                    if forecourt_friends.amount < base_friends.amount:
                        actions.append(unit.attack(base))
                    else:
                        actions.append(unit.attack(forecourt))

            else:
                order = unit.move(self.bot.start_location)
                actions.append(order)

        return actions
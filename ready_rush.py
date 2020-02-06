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

class ready_rush(object):
    def __init__(self, bot_ai):
        self.bot = bot_ai
        self.troops = dict()
        self.boost_times = dict()

        self.marauder_join = False

    def reset(self):
        for u in self.bot.units.owned:
            self.troops[u.tag] = "rush"

    async def step(self):
        actions = list()
        units = self.bot.units.owned

        for u in units:
            order = await self.get_order(u)
            if order is not None:
                actions.append(order)

        if actions is not None:
            return actions

    async def get_order(self, unit):
        ###################### postions #####################
        if self.bot.start_location.distance2_to(strategic_points[0]) < 3:   # base is upper
            forecourt = strategic_points[1]
            base = strategic_points[0]
            enemy_base = strategic_points[4]
            ready_point = Point3((59.4, 41.3, 10))
            hide_point = Point2((19.89, 18.56))
        else:                                                               # base is lower
            forecourt = strategic_points[3]
            base = strategic_points[4]
            enemy_base = strategic_points[0]
            ready_point = Point3((28.6, 46, 10))
            hide_point = Point2((68.16, 69.35))

        center = strategic_points[2]

        drop_point = Point3(
                    (
                        (forecourt.x * 3 + enemy_base.x * 7) / 10, (forecourt.y * 3 + enemy_base.y * 7) / 10, 12
                    )
                )
        ###################### postions #####################

        order = None

        foes = self.bot.known_enemy_units.closer_than(13, unit)
        friends = self.bot.units.owned


        if unit.type_id == UnitTypeId.MARINE:
            if unit.distance_to(hide_point) < 3:
                order = unit.move(hide_point)
            elif unit.distance_to(enemy_base) >= 13.0:
                order = unit.move(ready_point)
            else:
                can_atk = self.bot.known_enemy_units.in_attack_range_of(unit)

                if unit.health_percentage < 0.3:
                    if self.bot.units.of_type(UnitTypeId.MEDIVAC).empty is False:
                        order = unit.move(self.bot.units.of_type(UnitTypeId.MEDIVAC).closest_to(unit.position))
                elif unit.health_percentage > 0.7:
                    if unit.health_percentage > 0.8 and \
                        not unit.has_buff(BuffId.STIMPACK) :
                    # 스팀팩 사용
                        order = unit(AbilityId.EFFECT_STIM)
                    else:
                    # 가장 가까운 목표 공격
                        if (foes.of_type(UnitTypeId.AUTOTURRET) & can_atk).amount > 0 and (foes.amount < friends.amount):
                            order = unit.attack(foes.of_type({UnitTypeId.AUTOTURRET}).closest_to(unit.position))
                        if (foes.of_type(UnitTypeId.MEDIVAC) & can_atk).amount > 0 :
                            order = unit.attack(foes.of_type({UnitTypeId.MEDIVAC}).closest_to(unit.position))
                        else:
                            if (foes.of_type(UnitTypeId.SIEGETANK) & can_atk).amount > 0 :
                                order = unit.attack(foes.of_type({UnitTypeId.SIEGETANK}).closest_to(unit.position))
                            elif (foes.of_type(UnitTypeId.SIEGETANKSIEGED) & can_atk).amount > 0 :
                                order = unit.attack(foes.of_type({UnitTypeId.SIEGETANKSIEGED}).closest_to(unit.position))
                            else:
                                order = unit.attack(enemy_base)

        elif unit.type_id == UnitTypeId.MARAUDER:
            if self.marauder_join is False and unit.distance_to(enemy_base) > 13:
                marines = self.bot.units.owned.of_type(UnitTypeId.MARINE).filter(lambda u : u.distance_to(hide_point) > 5)
                marauders = self.bot.units.owned.of_type(UnitTypeId.MARAUDER)
                order = unit.move(marines.center)
                if marines.center.distance2_to(marauders.center) < 5:
                    self.marauder_join = True
            else:
                if unit.distance_to(enemy_base) >= 13.0:
                    order = unit.move(ready_point)
                elif unit.distance_to(enemy_base) < 13.0 and unit.position3d.z > 11:
                    order = unit.attack(enemy_base)

        elif unit.type_id == UnitTypeId.REAPER:
            threaten = self.bot.known_enemy_units.filter(lambda u: u.is_visible).closer_than(
                    13, unit.position)

            via = Point2(( (center.x + forecourt.x) / 2, (center.y + forecourt.y) / 2 ))

            if unit.distance_to(base) <= 13.0:
                order = unit.move(via)
            elif unit.distance_to(via) <= 2:
                order = unit.move(drop_point)
            elif unit.distance_to(enemy_base) < 13.0 and unit.position3d.z > 11:
                if unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET and unit.energy >= 50:
                    pos = Point2(( (unit.position3d.x * 2 + enemy_base.x ) / 3,  (unit.position3d.y * 2 + enemy_base.y) / 3 ))
                    pos = await self.bot.find_placement(UnitTypeId.AUTOTURRET, pos)
                    order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                else:
                    order = unit.attack(enemy_base)

        elif unit.type_id == UnitTypeId.SIEGETANK:
            if unit.distance_to(enemy_base) >= 13.0:
                order = unit.move(ready_point)
            if unit.distance_to(ready_point) <= 3:
                order = unit(AbilityId.SIEGEMODE_SIEGEMODE)

        elif unit.type_id == UnitTypeId.SIEGETANKSIEGED:
            if unit.distance_to(enemy_base) >= 13.0:
                order = unit(AbilityId.SIEGEMODE_SIEGEMODE)

        # 의료선 : 언덕 아래 리퍼 제외한 유닛들을 무조건 언덕 위로 배달 / 힐은 자동 힐
        elif unit.type_id == UnitTypeId.MEDIVAC:
            target_pssn = self.bot.units.exclude_type({UnitTypeId.REAPER, UnitTypeId.SIEGETANK}).closer_than(2, ready_point).filter(lambda u : u.position3d.z < 11)
            first_target = target_pssn.of_type(UnitTypeId.MARAUDER)
            second_target = target_pssn.of_type(UnitTypeId.SIEGETANK)
            last_target = target_pssn.of_type(UnitTypeId.MARINE)

            if unit.distance_to(ready_point) > 5:
                targets = self.bot.units.owned.of_type(UnitTypeId.MARINE).filter(lambda u : u.distance_to(hide_point) > 5) | \
                    self.bot.units.owned.of_type(UnitTypeId.MARAUDER)
                if targets.empty is False:
                    order = unit.move(targets.center)
            else:
                if target_pssn.amount >= 6:
                    if len(unit.passengers) > 2:
                        order = unit(AbilityId.UNLOADALLAT,drop_point)
                    elif first_target.amount > 0:
                        order = unit(AbilityId.LOAD, first_target.closest_to(unit.position))
                    #elif second_target.amount > 0:
                    #    order = unit(AbilityId.LOAD, second_target.closest_to(unit.position))
                    elif last_target.amount > 0:
                        order = unit(AbilityId.LOAD, last_target.closest_to(unit.position))
                else:
                    if len(unit.passengers) > 0:
                        order = unit(AbilityId.UNLOADALLAT,drop_point)
                    elif first_target.amount > 0:
                        order = unit(AbilityId.LOAD, first_target.closest_to(unit.position))
                    elif second_target.amount > 0:
                        order = unit(AbilityId.LOAD, second_target.closest_to(unit.position))
                    elif last_target.amount > 0:
                        order = unit(AbilityId.LOAD, last_target.closest_to(unit.position))


        if order is not None:
            return order
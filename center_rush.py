from enum import Enum

import sc2
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.units import Units

from IPython import embed

strategic_points = [
            #        x   y   z
            Point3((28, 60, 12)),  # A
            Point3((63, 65, 10)),  # B
            Point3((44, 44, 10)),  # C
            Point3((24, 22, 10)),  # D
            Point3((59, 27, 12)),  # E
        ]

class center_rush(object):
    def __init__(self, bot_ai):
        self.bot = bot_ai

        self.watcher = None
        self.enemy_attacked = False

    def reset(self):
        pass

    async def step(self):
        actions = list()
        base = self.bot.start_location

        if self.watcher is None:
            self.watcher = self.bot.units.owned.of_type(UnitTypeId.MARINE).first.tag
        if self.enemy_attacked is False and self.bot.known_enemy_units.closer_than(13, base):
            self.enemy_attacked = True

        for u in self.bot.units:
            plus = await self.common_step(u, self.bot.units, self.bot.known_enemy_units)
            actions += plus

        return actions

    async def common_step(self, unit, friends, foes):
        actions = list()

        base = self.bot.start_location  #우리 기지
        #기지 위치 따라 우리 벙커 위치 바뀜
        if base.x<50:
            bunkerplace=Point3((47.5,47.5,9.999828))
            shieldline=Point3((58.5,63.5,10))
        else:
            bunkerplace=Point3((40.5,40.5,10))
            shieldline=Point3((29.5,24.5,10))
        #맵 중앙
        center = strategic_points[2]
        #우리 앞쪽 부쉬 상세 위치들
        our_bush = Point2(
                    (
                        (base.x + center.x * 4) / 5, (base.y + center.y * 4) / 5
                    )
                )
        upper_bush = Point3(((base.x + center.x) / 2, (base.y + center.y) / 2, 12))
        bush_backward = Point3(
                    ((base.x * 2 + center.x * 3) / 5, (base.y * 2 + center.y * 3) / 5, 10)
                )
        bush_center = Point2(
            (
                (bush_backward.x + our_bush.x) / 2, (bush_backward.y + our_bush.y) / 2
            )
        )

        in_bunker = self.bot.units.owned.of_type(UnitTypeId.BUNKER)
        if in_bunker.amount > 0:
            in_bunker = in_bunker.first.passengers
            bunker_space = 8 - len(in_bunker)
            for u in in_bunker:
                if u.type_id is UnitTypeId.MARAUDER:
                    bunker_space -= 1
        else:
            bunker_space = 0

        if self.bot.start_location.distance2_to(strategic_points[0]) < 3:
            forecourt = strategic_points[1]
        else:
            forecourt = strategic_points[3]

        if self.watcher == unit.tag and self.enemy_attacked is False:
            order = unit.move(forecourt)
            actions.append(order)

        #벙커
        elif unit.type_id == UnitTypeId.BUNKER and unit.position3d.x > 40 and unit.position3d.x < 50:
            if self.bot.units.owned.of_type(UnitTypeId.MARAUDER).closer_than(2, unit):
                actions.append(unit(AbilityId.LOAD_BUNKER, self.bot.units.owned.of_type(UnitTypeId.MARAUDER).closer_than(2, unit).first))


        #해병은 언덕 위에서 먼저 뛰고, 언덕 아래에 있으면 싸우고
        elif unit.type_id == UnitTypeId.MARINE:
            rushed_enemy = self.bot.known_enemy_units.closer_than(13, base)
            if unit.position3d.z > 10:
                if rushed_enemy:
                    actions.append(unit.attack(rushed_enemy.closest_to(unit.position)))
                else:
                    first_move = upper_bush
                    actions.append(unit.move(first_move))
            else:
                can_atk = self.bot.known_enemy_units.in_attack_range_of(unit)
                if rushed_enemy and self.bot.units.filter(lambda u : u.position3d.z < 11).amount > 1:
                    order = unit.move(bush_backward)
                elif unit.health_percentage > 0.7 and foes.amount > 0 and foes.amount < friends.amount:
                    if unit.health_percentage > 0.8 and \
                        not unit.has_buff(BuffId.STIMPACK) :
                    # 스팀팩 사용
                        order = unit(AbilityId.EFFECT_STIM)
                    else:
                    # 가장 가까운 목표 공격
                        if (foes.of_type(UnitTypeId.AUTOTURRET) & can_atk) and (foes.amount < friends.amount):
                            order = unit.attack(foes.of_type({UnitTypeId.AUTOTURRET}).closest_to(unit.position))
                        if (foes.of_type(UnitTypeId.MEDIVAC) & can_atk) :
                            order = unit.attack(foes.of_type({UnitTypeId.MEDIVAC}).closest_to(unit.position))
                        else:
                            if (foes.of_type(UnitTypeId.SIEGETANK) & can_atk) :
                                order = unit.attack(foes.of_type({UnitTypeId.SIEGETANK}).closest_to(unit.position))
                            elif (foes.of_type(UnitTypeId.SIEGETANKSIEGED) & can_atk) :
                                order = unit.attack(foes.of_type({UnitTypeId.SIEGETANKSIEGED}).closest_to(unit.position))
                            else:
                                order = unit.attack(foes.closest_to(unit.position))
                elif foes.amount > 0 and foes.amount >= friends.amount:
                    order = unit.move(bush_center)
                else:
                    order = unit.attack(center)
                actions.append(order)

        # 불곰 : 긴 사거리를 활용해서 오토터렛 철거
        elif unit.type_id == UnitTypeId.MARAUDER:
            if unit.position3d.z > 10:
                rushed_enemy = self.bot.known_enemy_units.closer_than(13, base)
                if rushed_enemy:
                    actions.append(unit.attack(rushed_enemy.closest_to(unit.position)))
                else:
                    actions.append(unit.move(upper_bush))
            elif bunker_space > 0 and unit.distance_to(bunkerplace) > 2:
                actions.append(unit.move(bunkerplace))
            elif unit.health_percentage <= 0.4:
                if self.bot.units.owned.of_type(UnitTypeId.BUNKER):
                    actions.append(unit.move(bunkerplace))
                else:
                    actions.append(unit.move(bush_backward))
            else:
                can_atk = self.bot.known_enemy_units.filter(lambda u : u.is_visible).in_attack_range_of(unit)
                if (foes.of_type(UnitTypeId.AUTOTURRET) & can_atk):
                    actions.append(unit.attack(foes.of_type({UnitTypeId.AUTOTURRET}).closest_to(unit.position)))
                else:
                    actions.append(unit.attack(our_bush))

        # 의료선 : 언덕위의 해병과 불곰들을 무조건 언덕 아래로 배달 / 힐은 자동 힐
        elif unit.type_id == UnitTypeId.MEDIVAC:
            rushed_enemy = self.bot.known_enemy_units.closer_than(13, base)
            #적군 러쉬 오면
            if rushed_enemy and self.bot.units.filter(lambda u : u.position3d.z < 11).amount > 1:
                target_pssn = self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.MARINE) \
                    | self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.MARAUDER)
                target_pssn = target_pssn.closer_than(1, bush_backward)

                if len(unit.passengers) > 0:
                    actions.append(unit(AbilityId.UNLOADALLAT, upper_bush))
                if target_pssn and len(unit.passengers) < 1:
                    actions.append(unit(AbilityId.LOAD, target_pssn.closest_to(unit.position)))
            #평상시
            else:
                target_pssn = self.bot.units.filter(lambda u: u.position3d.z > 11).of_type(UnitTypeId.MARINE) \
                    | self.bot.units.filter(lambda u: u.position3d.z > 11).of_type(UnitTypeId.MARAUDER)
                target_pssn = target_pssn.closer_than(1, upper_bush)

                if len(unit.passengers) > 0:
                    actions.append(unit(AbilityId.UNLOADALLAT,bush_backward))
                if target_pssn and len(unit.passengers) < 1:
                    actions.append(unit(AbilityId.LOAD, target_pssn.closest_to(unit.position)))

        # 리퍼 : 센터에 터렛 설치
        elif unit.type_id == UnitTypeId.REAPER:
            threaten = self.bot.known_enemy_units.filter(lambda u: u.is_visible).closer_than(13, unit.position)
            rushed_enemy = self.bot.known_enemy_units.closer_than(13, base)
            if rushed_enemy.amount > 0:
                if unit.energy >= 50:
                    if threaten.amount >= 1 and \
                        unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                            pos = unit.position.towards(threaten.closest_to(unit.position), 4)
                            pos = await self.bot.find_placement(UnitTypeId.AUTOTURRET, pos)
                            order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                    else:
                        order = unit.attack(rushed_enemy.closest_to(unit.position))
                else:
                    order = unit.attack(rushed_enemy.closest_to(unit.position))
            elif unit.health_percentage > 0.8 and unit.energy >= 50:
                if threaten.amount > 0:
                    if unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                        closest_threat = threaten.closest_to(unit.position)
                        pos = unit.position.towards(closest_threat.position, 6)
                        pos = await self.bot.find_placement(
                            UnitTypeId.AUTOTURRET, pos)
                        order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                        actions.append(order)
                else:
                    if unit.distance_to(center) > 5:
                        order = unit.attack(center)
                        actions.append(order)
            else:
                if unit.distance_to(self.bot.start_location) > 5:
                    order = unit.move(base)
                    actions.append(order)

        elif unit.type_id == UnitTypeId.SIEGETANK:
            base = self.bot.start_location
            center = strategic_points[2]
            if base.x < 50:
                TANKLIST=[Point2((32.49,51.81)),Point2((39.14,53.81)),Point2((31.21,49.81))]
                shieldline=Point3((58.5,63.5,10))
            else:
                TANKLIST=[Point2((52.14,35.99)),Point2((55.44,37.24)),Point2((45.69,35.89))]
                shieldline=Point3((29.5,24.5,10))

            bush_backward = Point3(
                ((base.x * 2 + center.x * 3) / 5, (base.y * 2 + center.y * 3) / 5, 10)
            )

            units = self.bot.units.of_type(UnitTypeId.SIEGETANK).owned | self.bot.units.of_type(UnitTypeId.SIEGETANKSIEGED).owned
            if units.amount == 1:
                if unit.position.distance2_to(TANKLIST[0]) ** 0.5 < 1:
                    order = unit(AbilityId.SIEGEMODE_SIEGEMODE)
                    actions.append(order)
                elif unit.position3d.z > 10:
                    actions.append(unit.move(TANKLIST[0]))

            elif units.amount == 2:
                if unit.position.distance2_to(TANKLIST[1]) ** 0.5 < 1:
                    order = unit(AbilityId.SIEGEMODE_SIEGEMODE)
                    actions.append(order)
                else:
                    actions.append(unit.move(TANKLIST[1]))

            elif units.amount == 3:
                if unit.position.distance2_to(TANKLIST[2]) ** 0.5 < 1:
                    order = unit(AbilityId.SIEGEMODE_SIEGEMODE)
                    actions.append(order)
                else:
                    actions.append(unit.move(TANKLIST[2]))
            else:
                if units.amount >= 4 and units.amount <= 6:
                    actions.append(unit.move(bush_backward))
                else:
                    if unit.position.distance2_to(shieldline) ** 0.5 <1:
                        order = unit(AbilityId.SIEGEMODE_SIEGEMODE)
                        actions.append(order)
                    else:
                        actions.append(unit.move(shieldline))

        return actions
# __author__ = "박정인"

import random
from enum import Enum

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions import Categorical

import sc2
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.units import Units
from sc2.data import Result

from IPython import embed

from .hide_en_seek import disturb_and_defense
from .target_atk import target_attack
from .min_atk import min_atk
from .defense import defense
from .ready_rush import ready_rush
from .center_rush import center_rush

from .UnitChecker import checker

from .network import net

import math
import os

dirname = os.path.dirname(__file__)
PT_NAME = os.path.join(dirname, 'module.pt')

class Bot(sc2.BotAI):
    def __init__(self, debug = False):
        super().__init__()
        self.strategy = disturb_and_defense(self)
        self.checker = checker(self)

        self.min_atk = None
        self.target_atk = None
        self.defense = None

        self.switch_cnt = 0
        self.succ = False
        self.last_mineral = 0
        self.center_occupied = False

        self.model = net()
        self.last_update = -10
        self.after = False

        self.preprocessed = False

        self.a = 0

    async def on_unit_created(self, unit):
        if self.switch_cnt == 0:
            self.strategy.decide_troop(unit)

    async def on_unit_destroyed(self, unit_tag):
        killed_enemy, killed_type = self.checker.remove_killed_unit(unit_tag)

    async def on_step(self, iteration : int):
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

        if self.start_location.distance2_to(strategic_points[4]) < 3:
            strategic_points = [
                #        x   y   z
                Point3((59, 27, 12)),  # E
                Point3((24, 22, 10)),  # D
                Point3((44, 44, 10)),  # C
                Point3((63, 65, 10)),  # B
                Point3((28, 60, 12)),  # A
            ]

        target = strategic_points[4]
        for i in range(5):
            if self.known_enemy_units.closer_than(9, strategic_points[i]).amount == 0 or \
                (self.units.closer_than(9 ,strategic_points[i]).amount > self.known_enemy_units.closer_than(9, strategic_points[i]).amount + 3):
                pass
            else:
                if i == 2:
                    base = self.start_location
                    center = strategic_points[2]

                    if self.center_occupied is True:
                        continue
                    target = Point2(( (base.x + center.x * 4) / 5, (base.y + center.y * 4) / 5 ))
                else:
                    target = strategic_points[i]
                break
        if target == strategic_points[3] and self.start_location.distance2_to(Point3((59, 27, 12))) < 3:
            target = Point2((68.16, 69.35))
        if target == strategic_points[3] and self.start_location.distance2_to(Point3((59,27,12))) > 13:
            target = Point2((19.89, 18.56))

        end_by_min_atk = False
        ###########################################
        if self.time < 10 and self.preprocessed == False:
            self.model.load_state_dict(torch.load(PT_NAME))
            self.min_atk = min_atk(self)
            self.target_atk = target_attack(self, target)
            self.defense =  defense(self)

            self.preprocessed = True

        if self.minerals != self.last_mineral:
            self.checker.eval()
            self.last_mineral = self.minerals % 10

        dif = False

        base = strategic_points[0]
        center = strategic_points[2]
        upper_bush = Point3(((base.x + center.x) / 2, (base.y + center.y) / 2, 12))

        if self.switch_cnt == 0:
            tank = self.units.of_type(UnitTypeId.SIEGETANK) | self.units.of_type(UnitTypeId.SIEGETANKSIEGED)
            bunker = self.units.of_type(UnitTypeId.BUNKER).filter(lambda u : u.position3d.x > 40 and u.position3d.x < 50)
            self.after = (self.strategy.end) or (self.strategy.opposite_saw is False and bunker.amount == 0) or (tank.amount > 0)
            if self.after == True:
                self.strategy.end = True
                self.strategy = min_atk(self)
                if tank.amount > 0 and self.checker.enemy_units[4] < 1:
                    self.switch_cnt = 2
                    dif = True
                else:
                    self.switch_cnt = 1
                    dif = True
            if self.after is False and self.strategy.opposite_saw is True:
                self.strategy = center_rush(self)
                self.switch_cnt = -1

        elif self.switch_cnt == -1:
            if self.known_enemy_units.closer_than(8, strategic_points[2]).amount < 1:
                self.switch_cnt = 1
                self.strategy = self.min_atk

        elif self.switch_cnt == 1:
            tank = self.units.of_type(UnitTypeId.SIEGETANK) | self.units.of_type(UnitTypeId.SIEGETANKSIEGED)
            friends = self.units.owned.filter(lambda u : u.is_structure is False).amount

            data = self.checker.make_data()

            our_units = torch.tensor( [ data[0], data[1], data[2], data[3], data[4] ], dtype=torch.float )
            our_units = round(self.model.forward(our_units).item(), 3) * 1000

            center_foes = torch.tensor([ data[5] , data[6] , data[7] , data[8] , data[9] ], dtype=torch.float)
            center_foes = round(self.model.forward(center_foes).item(), 3) * 1000

            rushed_foes = 0
            if data[10] > 0 or data[11] > 0 or data[12] > 0 or data[13] > 0 or data[14] > 0:
                rushed_foes = torch.tensor([ data[10] , data[11] , data[12] , data[13] , data[14] ], dtype=torch.float)
                rushed_foes = round(self.model.forward(rushed_foes).item(), 3) * 1000

            base_foes = torch.tensor([data[15] , data[16] , data[17] , data[18] , data[19]], dtype=torch.float)
            base_foes = round(self.model.forward(base_foes).item(), 3) * 1000

            enemy_total = center_foes + rushed_foes + base_foes

            
            if enemy_total * 3 <= our_units:
                end_by_min_atk = True

            if (tank.amount > 0 and self.checker.enemy_units[4] < 1 and (friends / 3 > base_foes)) and target != Point3((59, 27, 12)) and target != Point3((28, 60, 12)):
                self.switch_cnt = 2
                dif = True
            if (self.time - self.last_update >= 0.3):
                ans = 0
                if center_foes >= rushed_foes and center_foes >= base_foes:
                    ans = 0
                elif our_units + 10 < center_foes + rushed_foes + base_foes:
                    ans = 0
                elif our_units > 150 and (our_units / 2 > enemy_total) and base_foes >= rushed_foes and base_foes >= center_foes:
                    ans = 1

                if rushed_foes > 2:
                    ans = 2

                if self.a != ans:
                    dif = True
                self.a = ans

                if self.a == 0:
                    self.strategy = self.min_atk
                elif self.a == 1:
                    self.strategy = self.target_atk
                else:
                    self.strategy = self.defense
                self.last_update = self.time

        elif self.switch_cnt == 2:
            self.strategy = ready_rush(self)

        if self.switch_cnt == 1 and self.a == 1:
            self.strategy.reset(target)
        elif self.switch_cnt == 1 and self.a == 0:
            self.strategy.reset(end_by_min_atk)
            if self.strategy.line > 0:
                self.center_occupied = True
        else:
            try:
                self.strategy.reset()
            except:
                try:
                    self.strategy.reset(target)
                except:
                    self.strategy.reset(end_by_min_atk)

        if dif is True:
            sieged = self.units.owned.of_type(UnitTypeId.SIEGETANKSIEGED)
            unsiege = list()
            for u in sieged:
                unsiege.append(u(AbilityId.UNSIEGE_UNSIEGE))
            await self.do_actions(unsiege)
            dif = False
            self.target_atk.arrival = list()
            self.target_atk.atk_start = False

        actions = await self.strategy.step()
        if actions is not None:
            await self.do_actions(actions)

        self.checker.step()

        ############### DEBUG ###############
        text = [
                    f'Switch    {self.switch_cnt}',
                    f'target    {target}',
                    f'self.a    {self.a % 3}',
                    f'{end_by_min_atk}'
                ]
        self._client.debug_text_screen('\n'.join(text), pos = (0.02, 0.02), size = 13)

        await self._client.send_debug()

        dirname = os.path.dirname(__file__)
        replay_pth = os.path.join(dirname, 'latest_replay.SC2replay')
        if self.time % 5 == 0:
            await self._client.save_replay(replay_pth)
        ############### DEBUG ###############
from __future__ import annotations

import random
from typing import List, Tuple

from lane_system import LaneSystem
from entities import Enemy, EnemyType, Pickup, PickupType
from settings import (
    BASE_SCROLL_SPEED,
    SPAWN_INTERVAL_START,
    SPAWN_INTERVAL_MIN,
    SPAWN_INTERVAL_DECAY,
    ENEMY_NORMAL_PROB,
    ENEMY_LEVEL2_PROB,
    ENEMY_SPECIAL_PROB,
    PICKUP_SPAWN_CHANCE,
    PICKUP_AMMO_PROB,
    PICKUP_HP_PROB,
    PICKUP_COIN_PROB,
    MAX_ELITE_PER_LANE,
)


class Spawner:
    def __init__(self, lane_system: LaneSystem) -> None:
        self.lane_system = lane_system
        self.enemies: List[Enemy] = []
        self.pickups: List[Pickup] = []

        self.time_since_last_spawn: float = 0.0
        self.spawn_interval: float = SPAWN_INTERVAL_START
        self.speed_level: int = 1
        # enemy shooting interval scaling with difficulty (managed by Game)
        from settings import ENEMY_SHOOT_INTERVAL

        self.current_shoot_interval: float = ENEMY_SHOOT_INTERVAL

    @property
    def current_speed(self) -> float:
        return BASE_SCROLL_SPEED + (self.speed_level - 1) * 40

    def increase_difficulty(self) -> None:
        self.speed_level += 1
        self.spawn_interval = max(
            SPAWN_INTERVAL_MIN,
            SPAWN_INTERVAL_START - SPAWN_INTERVAL_DECAY * (self.speed_level - 1),
        )

    def spawn_pair(self) -> None:
        # spawn enemy with weighted type probabilities
        lane_idx = random.randrange(self.lane_system.lane_count)
        x = self.lane_system.lane_center_x(lane_idx)
        y = -80

        # limit number of level2 + special enemies in the same lane
        elite_in_lane = sum(
            1
            for e in self.enemies
            if e.lane_index == lane_idx and e.enemy_type in (EnemyType.LEVEL2, EnemyType.SPECIAL)
        )

        r = random.random()
        if elite_in_lane >= MAX_ELITE_PER_LANE:
            # force normal enemy if lane already has enough elites
            enemy_type = EnemyType.NORMAL
        else:
            if r < ENEMY_NORMAL_PROB:
                enemy_type = EnemyType.NORMAL
            elif r < ENEMY_NORMAL_PROB + ENEMY_LEVEL2_PROB:
                enemy_type = EnemyType.LEVEL2
            else:
                enemy_type = EnemyType.SPECIAL

        enemy = Enemy(lane_idx, x, y, self.current_speed, enemy_type, shoot_interval=self.current_shoot_interval)
        self.enemies.append(enemy)

        # chance to spawn a pickup in (possibly) different lane
        if random.random() < PICKUP_SPAWN_CHANCE:
            pick_lane = random.randrange(self.lane_system.lane_count)
            pick_x = self.lane_system.lane_center_x(pick_lane)
            pick_y = y - 120
            # decide pickup type based on configurable probabilities
            pr = random.random()
            if pr < PICKUP_AMMO_PROB:
                pickup_type = PickupType.AMMO
            elif pr < PICKUP_AMMO_PROB + PICKUP_HP_PROB:
                pickup_type = PickupType.HP
            else:
                pickup_type = PickupType.COIN
            pickup = Pickup(pick_lane, pick_x, pick_y, self.current_speed, pickup_type)
            self.pickups.append(pickup)

    def update(self, dt: float) -> None:
        self.time_since_last_spawn += dt
        if self.time_since_last_spawn >= self.spawn_interval:
            self.time_since_last_spawn = 0.0
            self.spawn_pair()

        for enemy in self.enemies:
            enemy.update(dt)
        for p in self.pickups:
            p.update(dt)

        # remove off-screen
        self.enemies = [e for e in self.enemies if e.y - e.height < self.lane_system.height + 80]
        self.pickups = [p for p in self.pickups if p.y - p.height < self.lane_system.height + 80]

    def clear_all(self) -> None:
        self.enemies.clear()
        self.pickups.clear()

    def all_entities(self) -> Tuple[list, list]:
        return self.enemies, self.pickups

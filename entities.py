from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import pygame
import os
_ASSET_CACHE: dict[str, pygame.Surface] = {}


from settings import (
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    ENEMY_NORMAL_COLOR,
    ENEMY_LEVEL2_COLOR,
    ENEMY_SPECIAL_COLOR,
    ENEMY_NORMAL_HP,
    ENEMY_LEVEL2_HP,
    ENEMY_SPECIAL_HP,
    ENEMY_SHOOT_INTERVAL,
    ENEMY_LEVEL2_FIRST_SHOT_DELAY,
    ENEMY_SPECIAL_FIRST_SHOT_DELAY,
    ENEMY_NORMAL_SPEED_MULT,
    ENEMY_LEVEL2_SPEED_MULT,
    ENEMY_SPECIAL_SPEED_MULT,
    PLAYER_BULLET_SPEED,
    ENEMY_BULLET_SPEED,
    LASER_DURATION,
    PICKUP_AMMO_COLOR,
    PICKUP_HP_COLOR,
    PICKUP_COIN_COLOR,
    PICKUP_RADIUS,
)

_ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")


def load_sprite(name: str, size: tuple[int, int]) -> pygame.Surface | None:
    key = f"{name}@{size[0]}x{size[1]}"
    if key in _ASSET_CACHE:
        return _ASSET_CACHE[key]

    path = os.path.join(_ASSET_DIR, name)
    if not os.path.exists(path):
        return None

    img = pygame.image.load(path).convert_alpha()
    img = pygame.transform.smoothscale(img, size)
    _ASSET_CACHE[key] = img
    return img


ENEMY_SPRITES = {
    "normal": "enemy_normal.png",
    "level2": "enemy_level2.png",
    "special": "enemy_special.png",
}

PICKUP_SPRITES = {
    "ammo": "pickup_ammo.png",
    "hp": "pickup_hp.png",
    "coin": "pickup_coin.png",
}



@dataclass
class BaseEntity:
    lane_index: int
    x: float
    y: float
    width: int
    height: int
    color: Tuple[int, int, int]
    speed: float  # positive = moving down, negative = moving up

    def update(self, dt: float) -> None:
        self.y += self.speed * dt

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.width / 2), int(self.y - self.height / 2), self.width, self.height)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.color, self.rect, border_radius=6)


class EnemyType:
    NORMAL = "normal"
    LEVEL2 = "level2"
    SPECIAL = "special"


class Enemy(BaseEntity):
    """Enemy with HP and optional shooting behaviour."""

    def __init__(self, lane_index: int, x: float, y: float, speed: float, enemy_type: str, shoot_interval: float | None = None) -> None:
        base_speed = speed
        if enemy_type == EnemyType.LEVEL2:
            color = ENEMY_LEVEL2_COLOR
            hp = ENEMY_LEVEL2_HP
            speed_mult = ENEMY_LEVEL2_SPEED_MULT
            first_shot_delay = ENEMY_LEVEL2_FIRST_SHOT_DELAY
        elif enemy_type == EnemyType.SPECIAL:
            color = ENEMY_SPECIAL_COLOR
            hp = ENEMY_SPECIAL_HP
            speed_mult = ENEMY_SPECIAL_SPEED_MULT
            first_shot_delay = ENEMY_SPECIAL_FIRST_SHOT_DELAY
        else:
            color = ENEMY_NORMAL_COLOR
            hp = ENEMY_NORMAL_HP
            enemy_type = EnemyType.NORMAL
            speed_mult = ENEMY_NORMAL_SPEED_MULT
            first_shot_delay = 0.0

        super().__init__(
            lane_index=lane_index,
            x=x,
            y=y,
            width=PLAYER_WIDTH,
            height=int(PLAYER_HEIGHT * 0.8),
            color=color,
            speed=base_speed * speed_mult,
        )
        self.enemy_type = enemy_type
        self.hp = hp
        base_interval = shoot_interval if shoot_interval is not None else ENEMY_SHOOT_INTERVAL
        self.shoot_interval = base_interval if enemy_type in (EnemyType.LEVEL2, EnemyType.SPECIAL) else None
        self.first_shot_delay = first_shot_delay
        self._time_since_shot = 0.0
        self._has_shot_once = False
        # for special enemies: channeling laser, stop movement during channel
        self.channel_timer: float = 0.0

    def update(self, dt: float) -> None:
        # if special is channeling a laser, it does not move
        if not (self.enemy_type == EnemyType.SPECIAL and self.channel_timer > 0.0):
            super().update(dt)
        else:
            self.channel_timer -= dt
        if self.shoot_interval is not None:
            self._time_since_shot += dt

    def can_shoot(self) -> bool:
        if self.shoot_interval is None:
            return False
        # first shot uses a separate delay, subsequent shots use interval
        if not self._has_shot_once:
            return self._time_since_shot >= self.first_shot_delay
        return self._time_since_shot >= self.shoot_interval

    def reset_shot_timer(self) -> None:
        self._time_since_shot = 0.0
        self._has_shot_once = True

    
    def draw(self, surface: pygame.Surface) -> None:
        name = ENEMY_SPRITES.get(self.enemy_type)
        if name:
            sprite = load_sprite(name, (self.width, self.height))
            if sprite is not None:
                surface.blit(sprite, sprite.get_rect(center=(int(self.x), int(self.y))))
                return
        super().draw(surface)



@dataclass
class Bullet(BaseEntity):
    """Generic bullet, from player or enemy."""

    damage: int
    from_player: bool
    is_circle: bool

    def __init__(self, lane_index: int, x: float, y: float, from_player: bool, is_circle: bool = False, color_override=None) -> None:
        width = 12
        height = 24
        if is_circle:
            height = width  # use square bounds for circular bullets
        color = color_override if color_override is not None else ((230, 230, 255) if from_player else (255, 180, 90))
        speed = PLAYER_BULLET_SPEED if from_player else ENEMY_BULLET_SPEED
        super().__init__(lane_index=lane_index, x=x, y=y, width=width, height=height, color=color, speed=speed)
        self.damage = 1
        self.from_player = from_player
        self.is_circle = is_circle

    def draw(self, surface: pygame.Surface) -> None:
        if self.is_circle:
            radius = self.width // 2
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), radius)
        else:
            super().draw(surface)


class LaserBeam:
    """Full-lane laser shot by special enemies."""

    def __init__(self, lane_index: int, x: float, start_y: float, width: int, color: Tuple[int, int, int]) -> None:
        self.lane_index = lane_index
        self.x = x
        self.start_y = start_y
        self.width = width
        self.color = color
        self.duration = LASER_DURATION
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        self.elapsed += dt

    @property
    def alive(self) -> bool:
        return self.elapsed < self.duration

    def get_rect(self, screen_height: int) -> pygame.Rect:
        # laser only goes downward from enemy towards the player
        return pygame.Rect(int(self.x - self.width / 2), int(self.start_y), self.width, max(0, screen_height - int(self.start_y)))

    def draw(self, surface: pygame.Surface) -> None:
        rect = self.get_rect(surface.get_height())
        pygame.draw.rect(surface, self.color, rect, border_radius=4)


class PickupType:
    AMMO = "ammo"
    HP = "hp"
    COIN = "coin"


@dataclass
class Pickup(BaseEntity):
    """Circular pickups (ammo / HP / coin)."""

    pickup_type: str = PickupType.AMMO

    def __init__(self, lane_index: int, x: float, y: float, speed: float, pickup_type: str) -> None:
        if pickup_type == PickupType.AMMO:
            color = PICKUP_AMMO_COLOR
        elif pickup_type == PickupType.HP:
            color = PICKUP_HP_COLOR
        else:
            color = PICKUP_COIN_COLOR
        diameter = PICKUP_RADIUS * 2
        super().__init__(
            lane_index=lane_index,
            x=x,
            y=y,
            width=diameter,
            height=diameter,
            color=color,
            speed=speed * 0.9,
        )
        self.pickup_type = pickup_type

    @property
    def rect(self) -> pygame.Rect:
        # collision bounds use the underlying square
        return super().rect

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), PICKUP_RADIUS)
    

    def draw(self, surface: pygame.Surface) -> None:
        diameter = PICKUP_RADIUS * 2

        name = PICKUP_SPRITES.get(self.pickup_type)
        if name:
            sprite = load_sprite(name, (diameter, diameter))
            if sprite is not None:
                surface.blit(sprite, sprite.get_rect(center=(int(self.x), int(self.y))))
                return

        # fallback nếu thiếu ảnh
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), PICKUP_RADIUS)


from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import pygame

from lane_system import LaneSystem
from entities import load_sprite
from settings import (
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_COLOR,
    PLAYER_START_HP,
    PLAYER_START_AMMO,
    PLAYER_SHOOT_COOLDOWN,
    PLAYER_INVULN_TIME,
    WINDOW_HEIGHT,
    LANE_CHANGE_COOLDOWN,
)


@dataclass
class PlayerCar:
    lane_system: LaneSystem
    lane_index: int = 1  # start in middle lane
    hp: int = PLAYER_START_HP
    score: int = 0
    coins: int = 0
    last_lane_change_time: float = -999.0
    lane_change_duration: float = 0.1  # seconds, visual smooth move
    ammo: int = PLAYER_START_AMMO

    def __post_init__(self) -> None:
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.color: Tuple[int, int, int] = PLAYER_COLOR
        self.y = WINDOW_HEIGHT - self.height
        # visual horizontal position (can be between lanes during animation)
        self.current_x: float = self.lane_system.lane_center_x(self.lane_index)
        self.target_x: float = self.current_x
        self._lane_change_elapsed: float = 0.0
        self._lane_change_start_x: float = self.current_x
        # shooting / damage
        self._shoot_cooldown_timer: float = PLAYER_SHOOT_COOLDOWN
        self.invuln_timer: float = 0.0

    @property
    def x(self) -> float:
        return self.current_x

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.width / 2), int(self.y - self.height / 2), self.width, self.height)

    @property
    def hitbox_rect(self) -> pygame.Rect:
        """Smaller hitbox than visual rectangle to feel fairer."""
        hit_w = int(self.width * 0.6)
        hit_h = int(self.height * 0.7)
        return pygame.Rect(
            int(self.x - hit_w / 2),
            int(self.y - hit_h / 2),
            hit_w,
            hit_h,
        )

    def can_change_lane(self, current_time: float) -> bool:
        return (current_time - self.last_lane_change_time) >= LANE_CHANGE_COOLDOWN

    def change_lane(self, direction: int, current_time: float) -> None:
        if not self.can_change_lane(current_time):
            return
        new_lane = self.lane_system.clamp_lane(self.lane_index + direction)
        if new_lane != self.lane_index:
            # logical lane index updates immediately
            self.lane_index = new_lane
            self.last_lane_change_time = current_time
            # start smooth interpolation from current_x to new lane center
            self._lane_change_start_x = self.current_x
            self.target_x = self.lane_system.lane_center_x(self.lane_index)
            self._lane_change_elapsed = 0.0

    def handle_event(self, event: pygame.event.Event, current_time: float) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_a, pygame.K_LEFT):
                self.change_lane(-1, current_time)
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self.change_lane(1, current_time)

    def update(self, dt: float) -> None:
        # smooth lane switching
        if self.current_x != self.target_x:
            self._lane_change_elapsed += dt
            t = min(1.0, self._lane_change_elapsed / max(0.0001, self.lane_change_duration))
            # linear interpolation
            self.current_x = self._lane_change_start_x + (self.target_x - self._lane_change_start_x) * t

        # cooldown for shooting
        if self._shoot_cooldown_timer < PLAYER_SHOOT_COOLDOWN:
            self._shoot_cooldown_timer += dt

        # invulnerability countdown
        if self.invuln_timer > 0.0:
            self.invuln_timer -= dt

    # shooting & damage helpers
    def can_shoot(self) -> bool:
        return self.ammo > 0 and self._shoot_cooldown_timer >= PLAYER_SHOOT_COOLDOWN

    def consume_shot(self) -> bool:
        """Return True if a bullet should be spawned."""
        if not self.can_shoot():
            return False
        self.ammo -= 1
        self._shoot_cooldown_timer = 0.0
        return True

    def apply_damage(self, amount: int) -> bool:
        """Apply damage; returns True if player died."""
        if self.invuln_timer > 0.0:
            return False
        self.hp -= amount
        self.invuln_timer = PLAYER_INVULN_TIME
        return self.hp <= 0

    def draw(self, surface: pygame.Surface) -> None:
        sprite = load_sprite("player.png", (self.width, self.height))
        if sprite is not None:
            surface.blit(sprite, sprite.get_rect(center=(int(self.x), int(self.y))))
            return

        # fallback nếu thiếu ảnh
        color = self.color
        if self.invuln_timer > 0.0:
            alpha_phase = int((self.invuln_timer * 20) % 2)
            if alpha_phase == 0:
                color = (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40))
        pygame.draw.rect(surface, color, self.rect, border_radius=8)


    def add_score(self, amount: int) -> None:
        self.score += amount

    def add_coin(self, amount: int = 1) -> None:
        self.coins += amount

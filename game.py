from __future__ import annotations

import sys
import os
import pygame

from lane_system import LaneSystem
from player import PlayerCar
from spawner import Spawner
from entities import EnemyType, Bullet, LaserBeam, PickupType
from hud import HUD
from settings import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    FPS,
    BACKGROUND_COLOR,
    SPEED_INCREASE_INTERVAL,
    SPAWN_INTERVAL_START,
    PLAYER_START_HP,
    PICKUP_AMMO_AMOUNT,
    PICKUP_HP_AMOUNT,
    PICKUP_COIN_SCORE,
    ENEMY_SHOOT_INTERVAL,
    ENEMY_SHOOT_INTERVAL_MIN,
    ENEMY_SHOOT_INTERVAL_DECAY_PER_LEVEL,
    LASER_DURATION,
    SCREEN_SCALE,
    START_FULLSCREEN,
    SMOOTH_SCALE,
)


class Game:
    def __init__(self) -> None:
        pygame.init()
        # ==== Music on start ====
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()
            bgm_path = os.path.join(os.path.dirname(__file__), "assets", "anh_do_skibidi.mp3")  # hoặc bgm.wav
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.set_volume(0.35)   # 0.0 -> 1.0
            pygame.mixer.music.play(-1)           # -1 = loop vô hạn
        except pygame.error as e:
            print(f"[WARN] Cannot play music: {e}")

        pygame.display.set_caption(WINDOW_TITLE)
        self.base_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        self.scale = SCREEN_SCALE
        self.fullscreen = START_FULLSCREEN

        # screen: cửa sổ thật (sẽ là base_size * scale hoặc fullscreen)
        self.apply_display_mode()

        # canvas: nơi vẽ game ở size gốc
        self.canvas = pygame.Surface(self.base_size).convert_alpha()

        self.clock = pygame.time.Clock()

        self.lane_system = LaneSystem()
        self.player = PlayerCar(self.lane_system)
        self.spawner = Spawner(self.lane_system)
        self.hud = HUD()

        self.running = True
        self.game_over = False
        self.time_accum_for_speed: float = 0.0
        # projectiles and lasers
        self.player_bullets: list[Bullet] = []
        self.enemy_bullets: list[Bullet] = []
        self.lasers: list[LaserBeam] = []


    def apply_display_mode(self) -> None:
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            w = int(WINDOW_WIDTH * self.scale)
            h = int(WINDOW_HEIGHT * self.scale)
            self.screen = pygame.display.set_mode((w, h))

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        self.apply_display_mode()


    def reset(self) -> None:
        self.player = PlayerCar(self.lane_system)
        self.spawner.clear_all()
        self.spawner.speed_level = 1
        self.spawner.spawn_interval = SPAWN_INTERVAL_START
        self.time_accum_for_speed = 0.0
        self.game_over = False
        self.player_bullets.clear()
        self.enemy_bullets.clear()
        self.lasers.clear()

    def handle_collisions(self) -> None:
        # use smaller hitbox for more forgiving collisions
        player_rect = self.player.hitbox_rect

        # Player vs enemies (body collision)
        remaining_enemies = []
        for e in self.spawner.enemies:
            if player_rect.colliderect(e.rect) and not self.game_over:
                if self.player.apply_damage(1):
                    self.game_over = True
                    self.hud.update_high_score(self.player.score)
                # enemy stays; it is a solid obstacle
            remaining_enemies.append(e)
        self.spawner.enemies = remaining_enemies

        # Player bullets vs enemies
        remaining_player_bullets: list[Bullet] = []
        for b in self.player_bullets:
            hit_any = False
            for e in self.spawner.enemies:
                if b.rect.colliderect(e.rect):
                    e.hp -= b.damage
                    hit_any = True
                    if e.hp <= 0:
                        # enemy destroyed, give score based on type
                        if e.enemy_type == EnemyType.NORMAL:
                            self.player.add_score(50)
                        elif e.enemy_type == EnemyType.LEVEL2:
                            self.player.add_score(100)
                        elif e.enemy_type == EnemyType.SPECIAL:
                            self.player.add_score(200)
                    break
            if not hit_any:
                remaining_player_bullets.append(b)

        # remove dead enemies after bullet processing
        self.spawner.enemies = [e for e in self.spawner.enemies if e.hp > 0]
        self.player_bullets = remaining_player_bullets

        # Player vs enemy bullets
        remaining_enemy_bullets: list[Bullet] = []
        for b in self.enemy_bullets:
            if b.rect.colliderect(player_rect) and not self.game_over:
                if self.player.apply_damage(1):
                    self.game_over = True
                    self.hud.update_high_score(self.player.score)
                # bullet consumed on hit
            else:
                remaining_enemy_bullets.append(b)
        self.enemy_bullets = remaining_enemy_bullets

        # Player vs lasers
        for laser in self.lasers:
            if not laser.alive:
                continue
            if laser.get_rect(WINDOW_HEIGHT).colliderect(player_rect) and not self.game_over:
                if self.player.apply_damage(1):
                    self.game_over = True
                    self.hud.update_high_score(self.player.score)

        # Player vs pickups
        remaining_pickups = []
        for p in self.spawner.pickups:
            if player_rect.colliderect(p.rect) and not self.game_over:
                if p.pickup_type == PickupType.AMMO:
                    self.player.ammo += PICKUP_AMMO_AMOUNT
                elif p.pickup_type == PickupType.HP:
                    # heal but cap at max hp
                    self.player.hp = min(self.player.hp + PICKUP_HP_AMOUNT, PLAYER_START_HP)
                elif p.pickup_type == PickupType.COIN:
                    self.player.add_score(PICKUP_COIN_SCORE)
                    self.player.add_coin(1)
                # pickup consumed
            else:
                remaining_pickups.append(p)
        self.spawner.pickups = remaining_pickups

    def update(self, dt: float) -> None:
        if self.game_over:
            return

        # update player smooth lane animation
        self.player.update(dt)

        self.spawner.update(dt)

        # enemy shooting (bullets / lasers)
        for e in self.spawner.enemies:
            if e.can_shoot():
                e.reset_shot_timer()
                if e.enemy_type == EnemyType.LEVEL2:
                    # spawn a single circular bullet in this lane (red circle)
                    b = Bullet(
                        e.lane_index,
                        e.x,
                        e.y + e.height / 2,
                        from_player=False,
                        is_circle=True,
                        color_override=(230, 60, 60),
                    )
                    self.enemy_bullets.append(b)
                elif e.enemy_type == EnemyType.SPECIAL:
                    # spawn a full-lane laser going downward from enemy
                    laser = LaserBeam(e.lane_index, e.x, e.y, e.width, e.color)
                    self.lasers.append(laser)
                    # special enemy stands still while channeling the laser
                    e.channel_timer = LASER_DURATION

        # update bullets & lasers
        for b in self.player_bullets:
            b.update(dt)
        for b in self.enemy_bullets:
            b.update(dt)
        for laser in self.lasers:
            laser.update(dt)

        # remove off-screen bullets / expired lasers
        self.player_bullets = [b for b in self.player_bullets if 0 - 50 < b.y < WINDOW_HEIGHT + 50]
        self.enemy_bullets = [b for b in self.enemy_bullets if 0 - 50 < b.y < WINDOW_HEIGHT + 50]
        self.lasers = [lz for lz in self.lasers if lz.alive]

        self.handle_collisions()

        # passive score over time, scaled by speed level
        self.player.add_score(int(60 * dt * self.spawner.speed_level))

        # difficulty scaling over time
        self.time_accum_for_speed += dt
        if self.time_accum_for_speed >= SPEED_INCREASE_INTERVAL:
            self.time_accum_for_speed = 0.0
            self.spawner.increase_difficulty()
            # also decrease enemy shoot cooldown as difficulty increases
            level = self.spawner.speed_level
            new_interval = max(
                ENEMY_SHOOT_INTERVAL_MIN,
                ENEMY_SHOOT_INTERVAL - ENEMY_SHOOT_INTERVAL_DECAY_PER_LEVEL * (level - 1),
            )
            self.spawner.current_shoot_interval = new_interval
            for e in self.spawner.enemies:
                if e.enemy_type in (EnemyType.LEVEL2, EnemyType.SPECIAL):
                    e.shoot_interval = new_interval

    def draw(self) -> None:
        surf = self.canvas
        surf.fill(BACKGROUND_COLOR)
        self.lane_system.draw(surf)

        for e in self.spawner.enemies:
            e.draw(surf)
        for p in self.spawner.pickups:
            p.draw(surf)

        for laser in self.lasers:
            if laser.alive:
                laser.draw(surf)

        for b in self.enemy_bullets:
            b.draw(surf)
        for b in self.player_bullets:
            b.draw(surf)

        self.player.draw(surf)
        self.hud.draw_top_panel(surf, self.player, self.spawner.speed_level)

        if self.game_over:
            self.hud.draw_game_over(surf, self.player.score)

        # ===== scale canvas -> screen (giữ tỉ lệ, có letterbox nếu fullscreen) =====
        sw, sh = self.screen.get_size()
        bw, bh = self.base_size
        scale = min(sw / bw, sh / bh)
        dw, dh = int(bw * scale), int(bh * scale)

        if SMOOTH_SCALE:
            scaled = pygame.transform.smoothscale(surf, (dw, dh))
        else:
            scaled = pygame.transform.scale(surf, (dw, dh))

        x = (sw - dw) // 2
        y = (sh - dh) // 2

        self.screen.fill((0, 0, 0))
        self.screen.blit(scaled, (x, y))
        pygame.display.flip()


    def run(self) -> None:
        dt = 0.0
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif self.game_over and event.key == pygame.K_RETURN:
                        self.reset()
                    
                    elif event.key == pygame.K_F11:
                        self.toggle_fullscreen()

                    elif event.key in (pygame.K_EQUALS, pygame.K_KP_PLUS):  # = hoặc numpad +
                        self.scale = min(6, self.scale + 1)
                        if not self.fullscreen:
                            self.apply_display_mode()

                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):  # - hoặc numpad -
                        self.scale = max(1, self.scale - 1)
                        if not self.fullscreen:
                            self.apply_display_mode()

                    else:
                        # lane change input with cooldown
                        current_time = pygame.time.get_ticks() / 1000.0
                        self.player.handle_event(event, current_time)
                        # shooting (space)
                        if event.key == pygame.K_SPACE and not self.game_over:
                            if self.player.consume_shot():
                                bullet = Bullet(
                                    lane_index=self.player.lane_index,
                                    x=self.player.x,
                                    y=self.player.y - self.player.height / 2,
                                    from_player=True,
                                )
                                self.player_bullets.append(bullet)

            if not self.running:
                break

            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit(0)

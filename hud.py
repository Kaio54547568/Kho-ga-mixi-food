from __future__ import annotations

import json
import os
from typing import Tuple

import pygame

from settings import (
    FONT_NAME,
    PLAYER_START_HP,
    HIGHSCORE_FILE,
    WINDOW_WIDTH,
)


def load_high_score() -> int:
    if not os.path.exists(HIGHSCORE_FILE):
        return 0
    try:
        with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return int(data.get("high_score", 0))
    except Exception:
        return 0


def save_high_score(score: int) -> None:
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            json.dump({"high_score": int(score)}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class HUD:
    def __init__(self, font_size: int = 22) -> None:
        self.font = pygame.font.SysFont(FONT_NAME, font_size)
        self.big_font = pygame.font.SysFont(FONT_NAME, 40)
        self.high_score: int = load_high_score()

    def update_high_score(self, score: int) -> None:
        if score > self.high_score:
            self.high_score = score
            save_high_score(score)

    def draw_text(self, surface: pygame.Surface, text: str, pos: Tuple[int, int], color=(240, 240, 240)) -> None:
        img = self.font.render(text, True, color)
        surface.blit(img, pos)

    def draw_top_panel(self, surface: pygame.Surface, player, speed_level: int) -> None:
        self.draw_text(surface, f"Score: {player.score}", (16, 10))
        self.draw_text(surface, f"Best: {self.high_score}", (16, 32))
        self.draw_text(surface, f"Speed Lv: {speed_level}", (16, 54))

        # HP hearts
        heart_w, heart_h = 18, 18
        for i in range(PLAYER_START_HP):
            color = (220, 80, 80) if i < player.hp else (80, 50, 50)
            x = WINDOW_WIDTH - 20 - (PLAYER_START_HP - i) * (heart_w + 4)
            y = 10
            pygame.draw.rect(surface, color, pygame.Rect(x, y, heart_w, heart_h), border_radius=4)

        # Ammo text
        ammo_text = f"Ammo: {player.ammo}"
        ammo_pos = (WINDOW_WIDTH - 20 - self.font.size(ammo_text)[0], 40)
        self.draw_text(surface, ammo_text, ammo_pos)

        # Coin text
        coin_text = f"Coins: {player.coins}"
        coin_pos = (WINDOW_WIDTH - 20 - self.font.size(coin_text)[0], 64)
        self.draw_text(surface, coin_text, coin_pos, color=(240, 220, 120))

    def draw_game_over(self, surface: pygame.Surface, score: int) -> None:
        msg = "CHƯA TÀY ĐÂU!"
        sub = "Press ENTER to restart / ESC to quit"
        best = f"Score: {score}  Best: {self.high_score}"

        msg_img = self.big_font.render(msg, True, (255, 220, 220))
        best_img = self.font.render(best, True, (240, 240, 240))
        sub_img = self.font.render(sub, True, (200, 200, 230))

        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2

        surface.blit(msg_img, msg_img.get_rect(center=(center_x, center_y - 60)))
        surface.blit(best_img, best_img.get_rect(center=(center_x, center_y)))
        surface.blit(sub_img, sub_img.get_rect(center=(center_x, center_y + 40)))

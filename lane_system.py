from dataclasses import dataclass

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, LANE_COUNT, LANE_LINE_COLOR
import pygame


@dataclass
class LaneSystem:
    lane_count: int = LANE_COUNT
    width: int = WINDOW_WIDTH
    height: int = WINDOW_HEIGHT

    def __post_init__(self) -> None:
        self.lane_width = self.width / self.lane_count

    def lane_center_x(self, lane_index: int) -> int:
        lane_index = max(0, min(self.lane_count - 1, lane_index))
        return int(self.lane_width * lane_index + self.lane_width / 2)

    def clamp_lane(self, lane_index: int) -> int:
        return max(0, min(self.lane_count - 1, lane_index))

    def draw(self, surface: pygame.Surface) -> None:
        # draw vertical lane separators
        for i in range(1, self.lane_count):
            x = int(self.lane_width * i)
            pygame.draw.line(surface, LANE_LINE_COLOR, (x, 0), (x, self.height), 2)

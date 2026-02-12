WINDOW_WIDTH = 480
WINDOW_HEIGHT = 720
WINDOW_TITLE = "3-Lane Runner - Pygame"

FPS = 60

LANE_COUNT = 3

PLAYER_WIDTH = 60
PLAYER_HEIGHT = 100
PLAYER_COLOR = (40, 210, 120)  # player car (green)
PLAYER_START_HP = 3
PLAYER_START_AMMO = 10
PLAYER_SHOOT_COOLDOWN = 0.0  # seconds
PLAYER_INVULN_TIME = 1.0  # seconds of invulnerability after being hit

OBSTACLE_COLOR = (220, 70, 70)  # legacy, not used for new enemies
GIFT_SCORE_COLOR = (80, 200, 120)  # legacy
GIFT_MANA_COLOR = (190, 140, 255)  # legacy

BACKGROUND_COLOR = (20, 20, 30)
LANE_LINE_COLOR = (70, 70, 90)

FONT_NAME = "consolas"

BASE_SCROLL_SPEED = 250  # pixels / second
SPEED_INCREASE_INTERVAL = 10.0  # seconds
SPEED_INCREASE_AMOUNT = 40

SPAWN_INTERVAL_START = 0.9
SPAWN_INTERVAL_MIN = 0.35
SPAWN_INTERVAL_DECAY = 0.02  # how fast spawn interval shrinks per speed level

LANE_CHANGE_COOLDOWN = 0.12  # seconds

# Enemy configuration
ENEMY_NORMAL_COLOR = (70, 140, 230)   # blue
ENEMY_LEVEL2_COLOR = (235, 210, 80)   # yellow
ENEMY_SPECIAL_COLOR = (230, 70, 70)   # red

ENEMY_NORMAL_HP = 1
ENEMY_LEVEL2_HP = 2
ENEMY_SPECIAL_HP = 3
ENEMY_SHOOT_INTERVAL = 2.0  # base seconds between shots for level2 and special
ENEMY_SHOOT_INTERVAL_MIN = 0.6
ENEMY_SHOOT_INTERVAL_DECAY_PER_LEVEL = 0.15

# First-shot delays (cooldown before the first shot after spawning)
ENEMY_LEVEL2_FIRST_SHOT_DELAY = 0.7
ENEMY_SPECIAL_FIRST_SHOT_DELAY = 1.5

# Enemy speed multipliers (relative to BASE_SCROLL_SPEED)
ENEMY_NORMAL_SPEED_MULT = 1.0
ENEMY_LEVEL2_SPEED_MULT = 0.75
ENEMY_SPECIAL_SPEED_MULT = 1.0

# Enemy spawn probabilities (should sum to 1.0)
ENEMY_NORMAL_PROB = 0.7
ENEMY_LEVEL2_PROB = 0.2
ENEMY_SPECIAL_PROB = 0.1

# Limit of level2+special enemies per lane at the same time
MAX_ELITE_PER_LANE = 1

# Projectiles
PLAYER_BULLET_SPEED = -600  # upwards
ENEMY_BULLET_SPEED = 380    # downwards
LASER_DURATION = 0.4        # seconds laser stays active

# Pickups
PICKUP_AMMO_COLOR = (80, 160, 255)  # blue circle
PICKUP_HP_COLOR = (80, 220, 140)    # green circle
PICKUP_COIN_COLOR = (240, 215, 80)  # yellow circle (money)
PICKUP_RADIUS = 14
PICKUP_AMMO_AMOUNT = 5
PICKUP_HP_AMOUNT = 1

# Pickup spawn configuration
PICKUP_SPAWN_CHANCE = 0.35  # overall chance to spawn any pickup per enemy
# Probabilities inside pickup spawn (should sum to 1.0)
PICKUP_AMMO_PROB = 0.4
PICKUP_HP_PROB = 0.2
PICKUP_COIN_PROB = 0.6

# Coin reward
PICKUP_COIN_SCORE = 15

HIGHSCORE_FILE = "highscore.json"


# ===== Display scaling (zoom whole game) =====
SCREEN_SCALE = 1          # 1 = bình thường, 2 = phóng to 2x, 3 = 3x...
START_FULLSCREEN = False  # True để vào fullscreen luôn
SMOOTH_SCALE = False      # True = mượt nhưng hơi blur, False = nét (hợp pixel art)

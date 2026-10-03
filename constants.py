from __future__ import annotations

import numpy as np

# ==============================================================
# MAP / EPISODE CONSTANTS
# ==============================================================

MAP_HALF_SIZE = 80.0
MAX_ALTITUDE = 50.0

NUM_ATTACKERS = 3
NUM_DEFENDERS = 3
NUM_AGENTS = NUM_ATTACKERS + NUM_DEFENDERS

MAX_HORIZONTAL_SPEED = 8.0
MAX_VERTICAL_SPEED = 3.0
MAX_YAW_RATE = 1.2

BASE_DETECTION_RANGE = 65.0

TARGET_RADIUS = 4.0
INTERCEPT_RADIUS = 3.0

CONTROL_REPEAT = 6
MAX_STEPS = 700

POI_NAMES = [
    "hospital",
    "defence_base",
    "power_plant",
    "communication_centre",
    "tourist_site",
]

WEATHER_NAMES = [
    "clear",
    "windy",
    "gusty",
    "rain",
    "fog",
]

WEATHER_CONFIG = {
    "clear": {
        "base_wind": 0.0,
        "gust": 0.0,
        "sensor_multiplier": 1.00,
    },
    "windy": {
        "base_wind": 4.0,
        "gust": 0.6,
        "sensor_multiplier": 1.00,
    },
    "gusty": {
        "base_wind": 5.0,
        "gust": 2.5,
        "sensor_multiplier": 0.90,
    },
    "rain": {
        "base_wind": 3.0,
        "gust": 1.0,
        "sensor_multiplier": 0.75,
    },
    "fog": {
        "base_wind": 1.0,
        "gust": 0.25,
        "sensor_multiplier": 0.50,
    },
}

# Spawn positions
ATTACKER_SPAWNS = np.array(
    [
        [-18.0, -68.0, 6.0],
        [0.0, -68.0, 6.0],
        [18.0, -68.0, 6.0],
    ],
    dtype=np.float32,
)

DEFENDER_SPAWNS = np.array(
    [
        [-26.0, -5.0, 7.0],
        [0.0, 0.0, 7.0],
        [26.0, -5.0, 7.0],
    ],
    dtype=np.float32,
)

# Observation dimension
OBS_DIM = 74

# Environment metadata
ENV_METADATA = {
    "name": "guardian_swarm_v1",
    "render_modes": ["human", None],
    "is_parallelizable": True,
}
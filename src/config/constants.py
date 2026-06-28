"""
src/config/constants.py
Tanggung jawab: Seluruh konfigurasi global (weight, threshold, utility, reward, penalty, cooldown, dll).
               Dilengkapi parser berkas .env bawaan untuk mengambil API_KEY tanpa dependensi eksternal.
"""

import os

# ==============================================================================
# PURE-PYTHON .ENV LOADER (Mencegah Dependency Error)
# ==============================================================================
# constants.py ada di src/config/constants.py, .env ada di root folder (3 tingkat ke atas)
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(root_dir, ".env")

if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip("'").strip('"')

# ==============================================================================
# API & CONNECTION CONFIG
# ==============================================================================
BASE_URL = os.getenv("CLAWROYALE_API_URL", "https://cdn.clawroyale.ai/api")
WS_BASE_URL = os.getenv("CLAWROYALE_WS_URL", "wss://cdn.clawroyale.ai/ws")
API_KEY = os.getenv("CLAWROYALE_API_KEY", "")

# Keepalive configurations
PING_INTERVAL_SECONDS = 15
WS_TIMEOUT_SECONDS = 10
MAX_CONNECTION_RETRIES = 5
RECONNECT_DELAY_SECONDS = 5

# Rate Limits
MAX_WS_MESSAGES_PER_MINUTE = 120
WS_THROTTLE_DELAY = 0.5

# ==============================================================================
# ACTIONS COOLDOWNS & COST CONFIG (Sesuai Aturan Resmi ClawRoyale)
# ==============================================================================
COOLDOWN_ACTION_SECONDS = 30.0

# EP Costs
EP_COST_MOVE = 1
EP_COST_MOVE_STORM_WATER = 2
EP_COST_EXPLORE = 1
EP_COST_ATTACK = 1
EP_COST_USE_ITEM = 0
EP_COST_INTERACT = 0
EP_COST_REST = 0
EP_COST_PICKUP = 0
EP_COST_EQUIP = 0

# Biaya EP Khusus Senjata Berat (Sesuai Aturan Resmi ClawRoyale)
WEAPON_EP_COSTS = {
    "katana": 2,
    "sniper": 2,
    "sniper rifle": 2,
    "sniper_rifle": 2
}

# Inventory Config
MAX_INVENTORY_SLOTS = 10

# ==============================================================================
# RETREAT & COMBAT THRESHOLDS (Sesuai COMBAT_RULES_v1.1 & RETREAT_RULES_v1.1)
# ==============================================================================
HP_RETREAT_THRESHOLD = 0.25
HP_EMERGENCY_THRESHOLD = 0.20
HP_FINISH_KILL_THRESHOLD = 0.15

# Ambang Batas EP
EP_MIN_RESERVE = 1

# Ambang Batas Win Probability (Peluang Menang)
WIN_PROBABILITY_RETREAT_THRESHOLD = 0.30
WIN_PROBABILITY_FINISH_KILL = 0.90

# Memori & Batasan Pergerakan
CHASE_LIMIT_REGIONS = 2
CHASE_LIMIT_TURNS = 2
RETREAT_DANGER_MEMORY_TURNS = 5
RETREAT_NO_LOOP_TURNS = 3

# Danger Score Weighting
WEIGHT_DANGER_HP = 0.4
WEIGHT_DANGER_ENEMY = 0.3
WEIGHT_DANGER_STORM = 0.2
WEIGHT_DANGER_EP = 0.1

# ==============================================================================
# GOAL & UTILITY WEIGHTS (Untuk Decision Making)
# ==============================================================================
WEIGHT_GOAL_STORM = 500.0
WEIGHT_GOAL_EMERGENCY = 400.0
WEIGHT_GOAL_HEAL = 300.0
WEIGHT_GOAL_ATTACK = 200.0
WEIGHT_GOAL_LOOT = 100.0
WEIGHT_GOAL_EXPLORE = 50.0

# Bonus Weights untuk Inventory Management
BONUS_WEIGHT_EQUIP = 150.0
BONUS_WEIGHT_CONSUMABLE = 120.0

# ==============================================================================
# WEB DASHBOARD CONFIG (Pancaran Telemetri Visual ke Browser)
# ==============================================================================
WEB_DASHBOARD_MODE = True
TELEMETRY_PORT = 8000
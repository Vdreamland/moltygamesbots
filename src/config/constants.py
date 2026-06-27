"""
src/config/constants.py
Tanggung jawab: Seluruh konfigurasi global (weight, threshold, utility, reward, penalty, cooldown, dll).
"""

import os

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
WS_THROTTLE_DELAY = 0.5  # Penjaga jarak kirim pesan agar tidak terkena rate limit

# ==============================================================================
# ACTIONS COOLDOWNS & COST CONFIG (Sesuai Aturan Resmi ClawRoyale)
# ==============================================================================
# Waktu cooldown aksi dalam detik
COOLDOWN_ACTION_SECONDS = 30.0

# EP Costs
EP_COST_MOVE = 1
EP_COST_MOVE_STORM_WATER = 2
EP_COST_EXPLORE = 1
EP_COST_ATTACK = 1
EP_COST_USE_ITEM = 0
EP_COST_INTERACT = 0
EP_COST_REST = 0  # Rest memulihkan EP tapi memicu cooldown
EP_COST_PICKUP = 0  # Tanpa cooldown, tanpa cost
EP_COST_EQUIP = 0  # Tanpa cooldown, tanpa cost

# Inventory Config
MAX_INVENTORY_SLOTS = 10

# ==============================================================================
# RETREAT & COMBAT THRESHOLDS (Sesuai COMBAT_RULES_v1.1 & RETREAT_RULES_v1.1)
# ==============================================================================
# Ambang Batas HP (Persentase 0.0 - 1.0)
HP_RETREAT_THRESHOLD = 0.25      # HP <= 25% langsung retreat
HP_EMERGENCY_THRESHOLD = 0.20    # HP < 20% aktifkan Emergency Mode (Combat Nonaktif)
HP_FINISH_KILL_THRESHOLD = 0.15   # Enemy HP < 15% batalkan retreat untuk finish-kill jika aman

# Ambang Batas EP
EP_MIN_RESERVE = 1                # EP <= 1 wajib retreat (tidak boleh habis total)

# Ambang Batas Win Probability (Peluang Menang)
WIN_PROBABILITY_RETREAT_THRESHOLD = 0.30  # Win Probability < 30% langsung retreat
WIN_PROBABILITY_FINISH_KILL = 0.90         # Win Probability > 90% paksa finish kill

# Memori & Batasan Pergerakan
CHASE_LIMIT_REGIONS = 2           # Pengejaran maksimal sejauh 2 region
CHASE_LIMIT_TURNS = 2             # Pengejaran maksimal selama 2 turn
RETREAT_DANGER_MEMORY_TURNS = 5   # Region berbahaya diingat selama 5 turn
RETREAT_NO_LOOP_TURNS = 3         # Dilarang berputar kembali ke region asal selama 3 turn

# Danger Score Weighting
WEIGHT_DANGER_HP = 0.4
WEIGHT_DANGER_ENEMY = 0.3
WEIGHT_DANGER_STORM = 0.2
WEIGHT_DANGER_EP = 0.1

# ==============================================================================
# GOAL & UTILITY WEIGHTS (Untuk Decision Making)
# ==============================================================================
WEIGHT_GOAL_STORM = 500.0         # Keluar dari badai memiliki prioritas tertinggi
WEIGHT_GOAL_EMERGENCY = 400.0     # Penyelamatan darurat
WEIGHT_GOAL_HEAL = 300.0          # Pemulihan HP jika aman
WEIGHT_GOAL_ATTACK = 200.0        # Menyerang musuh
WEIGHT_GOAL_LOOT = 100.0          # Mengumpulkan equipment
WEIGHT_GOAL_EXPLORE = 50.0        # Eksplorasi daerah baru
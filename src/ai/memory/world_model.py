"""
src/ai/memory/world_model.py
Tanggung jawab: Mengingat region yang dilewati, ground loot, jejak musuh,
               serta mengendalikan batasan aturan:
               - RETREAT MEMORY (Region bahaya selama 5 turn - Rule 13I)
               - NO LOOP RETREAT (Dilarang kembali ke region asal selama 3 turn - Rule 13D)
"""

import logging
from typing import Dict, Any, List, Set, Optional
from src.models.entities import Agent, Weapon
from src.models.game_state import GameState

logger = logging.getLogger("ClawRoyale.WorldModel")

class EnemyTrack:
    """Representasi memori analisis musuh (Combat Rule: ENEMY ANALYSIS)"""
    def __init__(self, enemy_id: str):
        self.enemy_id = enemy_id
        self.name: str = "Unknown"
        self.last_seen_region_id: str = ""
        self.last_hp: int = 100
        self.equipped_weapon: Optional[Weapon] = None
        self.last_seen_turn: int = -1
        self.predicted_regions: List[str] = []  # Jalur pergerakan musuh yang mungkin

    def update(self, agent: Agent, region_id: str, turn: int):
        self.name = agent.name
        self.last_seen_region_id = region_id
        self.last_hp = agent.hp
        self.equipped_weapon = agent.equipped_weapon
        self.last_seen_turn = turn
        
        # Masukkan region saat ini sebagai prioritas tebakan posisi
        if region_id not in self.predicted_regions:
            self.predicted_regions = [region_id]


class WorldModel:
    def __init__(self):
        # Struktur memori
        self.visited_regions_history: List[tuple[int, str]] = []  # List of tuple (turn, region_id)
        self.enemy_registry: Dict[str, EnemyTrack] = {}          # Map enemy_id -> EnemyTrack
        
        # Perekam kejadian taktis untuk memori pelarian
        self.retreat_danger_regions: Dict[str, int] = {}          # Map region_id -> turn_last_seen_danger
        self.retreat_exit_history: List[tuple[int, str]] = []     # Perekam perpindahan darurat untuk No Loop Rule

    def update(self, state: GameState):
        """Memperbarui world model berdasarkan game state baru per turn"""
        current_turn = state.turn
        current_region_id = state.current_region.id
        
        # 1. Catat sejarah kunjungan
        self.visited_regions_history.append((current_turn, current_region_id))

        # 2. Update tracking musuh yang terlihat
        for enemy in state.visible_enemies:
            if enemy.id not in self.enemy_registry:
                self.enemy_registry[enemy.id] = EnemyTrack(enemy.id)
                
            track = self.enemy_registry[enemy.id]
            track.update(enemy, current_region_id, current_turn)
            
            # [Retreat Rule 13I] Simpan region tempat musuh terlihat sebagai berbahaya selama 5 turn
            self.retreat_danger_regions[current_region_id] = current_turn
            logger.debug(f"[MEMORY] Region {current_region_id} ditandai BERBAHAYA di turn {current_turn} karena ada musuh.")

    def record_retreat_movement(self, from_region_id: str, turn: int):
        """
        [Retreat Rule 13D] Mencatat region asal pelarian untuk penegakan No Loop Rule.
        """
        self.retreat_exit_history.append((turn, from_region_id))
        logger.info(f"[RETREAT MEMORY] Mencatat meninggalkan region {from_region_id} di turn {turn} untuk No-Loop Rule.")

    def is_region_dangerous_by_enemy_memory(self, region_id: str, current_turn: int) -> bool:
        """
        [Retreat Rule 13I] Memeriksa apakah region aman dimasuki atau tergolong berbahaya
        karena ada musuh terlihat disana dalam 5 turn terakhir.
        """
        if region_id in self.retreat_danger_regions:
            turn_danger_occurred = self.retreat_danger_regions[region_id]
            # Berbahaya selama 5 turn
            if current_turn - turn_danger_occurred <= 5:
                return True
        return False

    def is_loop_forbidden(self, region_id: str, current_turn: int) -> bool:
        """
        [Retreat Rule 13D] Memeriksa apakah dilarang kembali ke region yang baru saja ditinggalkan
        saat melakukan retreat (minimal 3 turn sebelum boleh kembali).
        """
        # Cek sejarah perpindahan escape dalam 3 turn terakhir
        for turn_exit, abandoned_region in reversed(self.retreat_exit_history):
            if current_turn - turn_exit < 3:
                if abandoned_region == region_id:
                    logger.debug(f"[NO-LOOP CHECK] Region {region_id} DIBLOK karena ditinggalkan {current_turn - turn_exit} turn lalu.")
                    return True
            else:
                break
        return False

    def get_last_known_enemy_position(self, enemy_id: str) -> Optional[str]:
        if enemy_id in self.enemy_registry:
            return self.enemy_registry[enemy_id].last_seen_region_id
        return None

    def clean_expired_memories(self, current_turn: int):
        """Pembersihan memori usang untuk menghemat performa"""
        # Hapus memori bahaya musuh jika sudah lewat dari 5 turn
        expired_danger_keys = [
            region for region, turn in self.retreat_danger_regions.items()
            if current_turn - turn > 5
        ]
        for r_id in expired_danger_keys:
            del self.retreat_danger_regions[r_id]
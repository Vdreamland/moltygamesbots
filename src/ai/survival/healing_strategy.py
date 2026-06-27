"""
src/ai/survival/healing_strategy.py
Tanggung jawab: Merancang rute penyelamatan taktis khusus untuk melakukan pemulihan (Heal Move).
               Mengarahkan agen bergerak ke region sepi jika terluka tetapi ada musuh di dekatnya.
"""

import logging
from typing import Optional
from src.models.game_state import GameState
from src.models.entities import Potion
from src.models.action import MoveAction
from src.ai.memory.world_model import WorldModel
from src.ai.movement.path_scoring import PathScoring

logger = logging.getLogger("ClawRoyale.HealingStrategy")

class HealingStrategy:
    @staticmethod
    def evaluate_heal_retreat(state: GameState, memory: WorldModel) -> Optional[MoveAction]:
        """
        Jika HP terluka (< 75%) dan kita memiliki ramuan HP di tas, tetapi kondisi tidak aman (ada musuh),
        cari region tetangga terdekat yang tidak ada musuh dan bukan badai untuk mengungsi khusus untuk healing.
        """
        player = state.player
        visible_enemies = state.visible_enemies

        # Pastikan kita benar-benar terluka dan ada musuh yang mengancam healing instan
        hp_ratio = player.hp / player.max_hp
        if hp_ratio > 0.75 or len(visible_enemies) == 0:
            return None

        # Periksa apakah kita memiliki ramuan HP di dalam tas
        has_hp_potion = any(isinstance(i, Potion) and i.recovery_type == "hp" for i in player.inventory)
        if not has_hp_potion:
            return None

        # Cari region tetangga yang aman dari musuh saat ini dan badai
        connections = state.current_region.connections
        if not connections:
            return None

        best_safe_region_id: Optional[str] = None
        best_score = -9999.0

        for r_id in connections:
            # Nilai skor jalur region
            score = PathScoring.score_region(r_id, state, memory)
            
            # Berikan penalti keras jika region tetangga masuk pending death zone (tidak kondusif untuk healing)
            if r_id in state.pending_deathzones:
                score -= 100.0

            if score > best_score:
                best_score = score
                best_safe_region_id = r_id

        if best_safe_region_id and best_score > -500.0:
            logger.info(f"[HEAL STRATEGY] Mengungsi ke {best_safe_region_id} agar bisa menggunakan Potion HP dengan aman.")
            return MoveAction(
                region_id=best_safe_region_id,
                thought=f"Pindah ke {best_safe_region_id} agar terlepas dari vision musuh dan bisa meminum Potion HP."
            )

        return None
"""
src/ai/survival/storm_strategy.py
Tanggung jawab: Menangani evakuasi badai maut (Storm Rules).
 Menjamin keselamatan absolut agen dari penutupan zona badai.
"""

import logging
from typing import Optional
from src.models.game_state import GameState
from src.models.action import MoveAction
from src.ai.memory.world_model import WorldModel
from src.ai.movement.path_scoring import PathScoring

logger = logging.getLogger("ClawRoyale.StormStrategy")

class StormStrategy:
    @staticmethod
    def evaluate_storm_evacuation(state: GameState, memory: WorldModel) -> Optional[MoveAction]:
        current_region = state.current_region
        
        # [REVISI]: Pastikan evakuasi aktif jika wilayah saat ini adalah death zone murni ATAU diingat sebagai death zone
        if not current_region.is_death_zone and not memory.is_known_death_zone(current_region.id):
            return None

        connections = current_region.connections
        if not connections:
            return None

        # [REVISI]: Cari region tetangga yang benar-benar bersih murni dari memori badai maut kita
        safe_connections = [
            r_id for r_id in connections 
            if not memory.is_known_death_zone(r_id) and r_id not in state.pending_deathzones
        ]
        
        # Fallback jika semua tetangga terlanjur tertutup badai, gunakan koneksi yang tersedia
        target_connections = safe_connections if safe_connections else connections
        if not target_connections:
            return None

        best_region_id = max(target_connections, key=lambda r_id: PathScoring.score_region(r_id, state, memory))
        
        logger.info(f"[STORM STRATEGY] Menemukan wilayah evakuasi aman murni: {best_region_id}")
        return MoveAction(
            region_id=best_region_id,
            thought=f"Evakuasi badai menuju region aman bersih {best_region_id}."
        )
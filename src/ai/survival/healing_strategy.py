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
        Jika HP terluka parah (< 40%) dan kita memiliki ramuan HP di tas, tetapi kondisi tidak aman (ada musuh),
        cari region tetangga terdekat yang tidak ada musuh dan bukan badai untuk mengungsi khusus untuk healing.
        """
        player = state.player
        visible_enemies = state.visible_enemies

        # [REVISI JANGKAUAN]: Hanya deteksi ancaman instan jika ada musuh hidup di region murni yang sama (Layer 0)
        enemies_in_same_region = [e for e in visible_enemies if e.region_id == state.current_region.id and e.is_alive]

        hp_ratio = player.hp / player.max_hp
        
        # [AUDIT PREDATOR]: Hanya mengungsi untuk healing jika HP benar-benar kritis (<= 40%).
        # Mencegah bot menjadi pengecut (coward) melarikan diri saat HP masih 50%-75% padahal bisa menang duel.
        if hp_ratio > 0.40 or len(enemies_in_same_region) == 0:
            return None

        has_hp_potion = any(isinstance(i, Potion) and i.recovery_type == "hp" for i in player.inventory)
        if not has_hp_potion:
            return None

        connections = state.current_region.connections
        if not connections:
            return None

        best_safe_region_id: Optional[str] = None
        best_score = -9999.0

        for r_id in connections:
            score = PathScoring.score_region(r_id, state, memory)
            
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
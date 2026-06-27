"""
src/ai/movement/path_scoring.py
Tanggung jawab: Menilai kelayakan jalur wilayah tetangga secara matematis.
               Mempertimbangkan EP Cost, Ground Loot, risiko musuh,
               dan mengarahkan rute menuju Ruins jika berada dalam LOOT MODE.
"""

import logging
from src.models.game_state import GameState
from src.ai.memory.world_model import WorldModel
from src.ai.movement.exploration_strategy import ExplorationStrategy

logger = logging.getLogger("ClawRoyale.PathScoring")

class PathScoring:
    @staticmethod
    def score_region(region_id: str, state: GameState, memory: WorldModel) -> float:
        """
        Menghitung skor kelayakan komprehensif untuk melangkah ke sebuah region tetangga.
        """
        score = 0.0
        current_turn = state.turn

        # 1. Penilaian Berdasarkan Badai/Storm
        if region_id in state.pending_deathzones:
            score -= 150.0  # Penalti berat untuk area badai mendekat

        # Penalti Musuh Aktif Terlihat
        active_enemies_in_target = sum(1 for e in state.visible_enemies if e.region_id == region_id)
        if active_enemies_in_target > 0:
            score -= (active_enemies_in_target * 150.0)

        # 3. Penilaian Berdasarkan Memori Bahaya Musuh (Retreat Memory Rule 13I)
        if memory.is_region_dangerous_by_enemy_memory(region_id, current_turn):
            score -= 100.0  # Penalti jika pernah ada musuh dalam 5 turn terakhir
            
        # 4. Aturan Larangan No-Loop (Retreat Rule 13D)
        if memory.is_loop_forbidden(region_id, current_turn):
            score -= 500.0

        # 5. Potensi Loot (Ground Items)
        if region_id == state.current_region.id:
            for item in state.current_region.items:
                if item.type == "weapon":
                    score += 25.0
                elif "recovery" in item.type:
                    score += 20.0
                else:
                    score += 10.0

        # ==========================================================================
        # NAVIGASI TERARAH (LOOT MODE ROUTING):
        # Jika tidak bersenjata, beri bonus besar (+150) ke region berisi ruins aktif
        # ==========================================================================
        from src.ai.strategy.goal_selector import GoalSelector
        current_mode = GoalSelector.get_current_mode(state)
        
        ruin_bonus = 0.0
        if current_mode == "LOOT":
            # Cari apakah region target memiliki reruntuhan (ruin) aktif
            is_target_ruin = any(ruin.ruin_id == region_id and not ruin.is_empty for ruin in state.visible_ruins)
            if is_target_ruin:
                ruin_bonus = 150.0
                logger.info(f"[PATH SCORING] Region {region_id} diberi bonus Reruntuhan (+150) karena dalam LOOT MODE.")

        # 6. Nilai Penjelajahan (Eksplorasi & Anti-Oscillation)
        explore_score = ExplorationStrategy.calculate_exploration_score(region_id, memory, current_turn)
        score += explore_score + ruin_bonus

        # 7. Biaya Perjalanan (Travel EP Cost)
        is_water_or_storm = region_id in state.pending_deathzones or region_id.lower().startswith("water")
        if is_water_or_storm:
            score -= 40.0

        return score
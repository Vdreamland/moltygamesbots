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
        player = state.player

        # 1. DETEKSI BADAI & AIR (FAIL-SAFE)
        is_water_or_storm = region_id in state.pending_deathzones or memory.is_known_death_zone(region_id) or region_id.lower().startswith("water")
        if is_water_or_storm:
            score -= 2000.0

        # 2. PENALTI MUSUH HIDUP
        active_enemies_in_target = sum(1 for e in state.visible_enemies if e.region_id == region_id and e.is_alive)
        if active_enemies_in_target > 0:
            score -= (active_enemies_in_target * 150.0)

        # 3. PENALTI MEMORI (BAHAYA & LOOP)
        if memory.is_region_dangerous_by_enemy_memory(region_id, current_turn):
            score -= 100.0
        if memory.is_loop_forbidden(region_id, current_turn):
            score -= 500.0

        # 4. BONUS KONEKSI MID-GAME (TURN 30+)
        if current_turn >= 30:
            known_conn_count = memory.known_connections.get(region_id, 4)
            if known_conn_count >= 5:
                score += 30.0  
            elif known_conn_count <= 3:
                score -= 100.0 

        # 5. [PERBAIKAN ANTI-STUCK]: Baseline Score
        # Jika EP sehat (>= 8), berikan dorongan dasar agar skor total wilayah aman
        # tidak berakhir di angka 0 atau negatif, sehingga bot tidak terjebak REST loop.
        if player.ep >= 8:
            score += 15.0

        # 6. EVALUASI LOOT DI TANAH
        target_items = []
        if region_id == state.current_region.id:
            target_items = state.current_region.items
        else:
            target_items = memory.get_known_loot(region_id)

        item_ids_in_bag = {item.id for item in player.inventory}
        for item in target_items:
            if item.id in item_ids_in_bag:
                continue
            if item.type == "weapon":
                score += 25.0
            elif "recovery" in item.type:
                score += 20.0
            else:
                score += 10.0

        # 7. PENENTUAN MODE & BONUS KHUSUS
        from src.ai.strategy.goal_selector import GoalSelector
        current_mode = GoalSelector.get_current_mode(state)  
        
        ruin_bonus = 0.0
        loot_weapon_bonus = 0.0
        if current_mode == "LOOT":
            is_target_ruin = any(ruin.ruin_id == region_id and not ruin.is_empty for ruin in state.visible_ruins)
            if is_target_ruin:
                ruin_bonus = 150.0
            has_weapon_in_target = any(item.type == "weapon" for item in target_items)
            if has_weapon_in_target:
                loot_weapon_bonus = 350.0

        # 8. EVALUASI EKSPLORASI (ANTI-OSCILLATION)
        explore_score = ExplorationStrategy.calculate_exploration_score(region_id, memory, current_turn)
        score += explore_score + ruin_bonus + loot_weapon_bonus

        # 9. PENALTI EP COST (AIR/BADAI)
        if is_water_or_storm:
            score -= 40.0

        return score
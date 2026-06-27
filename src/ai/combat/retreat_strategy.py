"""
src/ai/combat/retreat_strategy.py
Tanggung jawab: Memicu pelarian instan (Retreat Triggers) berdasarkan musuh satu region,
 mengidentifikasi jalur pelarian aman, dan menegaskan No-Loop & Retreat Memory.
"""

import logging
from typing import Optional, List
from src.models.game_state import GameState
from src.models.entities import Agent, Region
from src.models.action import Action, MoveAction
from src.ai.memory.world_model import WorldModel
from src.ai.combat.win_probability import WinProbabilityCalculator
from src.ai.movement.path_scoring import PathScoring
from src.config.constants import HP_RETREAT_THRESHOLD, EP_MIN_RESERVE

logger = logging.getLogger("ClawRoyale.RetreatStrategy")

class RetreatStrategy:
    @staticmethod
    def evaluate_retreat(state: GameState, memory: WorldModel) -> Optional[MoveAction]:
        player = state.player
        visible_enemies = state.visible_enemies
        
        enemies_in_same_region = [e for e in visible_enemies if e.region_id == state.current_region.id]
        same_region_count = len(enemies_in_same_region)
        
        primary_enemy = enemies_in_same_region[0] if enemies_in_same_region else (visible_enemies[0] if visible_enemies else None)
        win_prob = WinProbabilityCalculator.calculate(player, primary_enemy) if primary_enemy else 1.0

        if primary_enemy and same_region_count == 1:
            e_hp_ratio = primary_enemy.hp / primary_enemy.max_hp
            if e_hp_ratio < 0.15 and win_prob > 0.90 and not state.current_region.is_death_zone:
                logger.info(f"[RETREAT] Diabaikan demi Finish-Kill pada {primary_enemy.name} (HP: {primary_enemy.hp}).")
                return None

        retreat_reason: Optional[str] = None
        hp_ratio = player.hp / player.max_hp

        # [REVISI]: Hanya retreat karena Low HP jika ada musuh di region yang sama
        if hp_ratio <= HP_RETREAT_THRESHOLD and same_region_count > 0:
            retreat_reason = "Low HP with enemy in same region"
        elif same_region_count >= 2:
            retreat_reason = "Outnumbered in current region (Enemy >= 2)"
        elif not player.equipped_weapon and same_region_count > 0:
            retreat_reason = "Unarmed with enemy in same region"
        elif player.ep <= EP_MIN_RESERVE and same_region_count > 0:
            retreat_reason = "Out of Energy with enemy in same region"
        elif state.current_region.is_death_zone:
            retreat_reason = "Inside Death Zone"

        if not retreat_reason:
            return None

        best_escape_region_id = RetreatStrategy._find_safest_escape_region(state, memory)
        if not best_escape_region_id:
            return None

        logger.warning(
            f"\n[RETREAT]\n"
            f"Enemy Visible : {len(visible_enemies)} (Same Region: {same_region_count})\n"
            f"Reason : {retreat_reason}\n"
            f"Current HP : {player.hp}\n"
            f"Win Probability : {win_prob:.0%}\n"
            f"Escape Region : {best_escape_region_id}\n"
            f"Decision : RETREAT\n"
        )

        return MoveAction(
            region_id=best_escape_region_id,
            thought=f"Retreat darurat ke {best_escape_region_id} karena kondisi: {retreat_reason}."
        )

    @staticmethod
    def _find_safest_escape_region(state: GameState, memory: WorldModel) -> Optional[str]:
        connections = state.current_region.connections
        if not connections:
            return None

        best_region_id: Optional[str] = None
        best_score = -99999.0

        for r_id in connections:
            score = PathScoring.score_region(r_id, state, memory)
            if score > best_score:
                best_score = score
                best_region_id = r_id

        if best_score < -1000.0:
            logger.warning("[RETREAT FALLBACK] Semua jalur pelarian dinilai sangat berbahaya. Mengaktifkan logika kelangsungan hidup darurat.")
            fallback_region_id = None
            fallback_score = -99999.0
            
            for r_id in connections:
                enemies_in_r = [e for e in state.visible_enemies if e.region_id == r_id]
                enemy_hp_sum = sum(e.hp for e in enemies_in_r)
                
                r_score = 0.0
                is_storm = False
                if hasattr(state, "regions") and r_id in state.regions:
                    is_storm = state.regions[r_id].is_death_zone
                
                if is_storm:
                    r_score -= 5000.0
                
                r_score -= enemy_hp_sum * 10.0
                
                if r_score > fallback_score:
                    fallback_score = r_score
                    fallback_region_id = r_id
                    
            if fallback_region_id:
                logger.info(f"[RETREAT FALLBACK] Memilih rute darurat: {fallback_region_id} (HP musuh di rute: {fallback_score / -10.0:.0f})")
                return fallback_region_id

        return best_region_id
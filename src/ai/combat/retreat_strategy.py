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
        
        # ==========================================================================
        # FILTER RETREAT: Hanya mundur jika musuh nyata berada di region yang sama dengan kita
        # ==========================================================================
        enemies_in_same_region = [e for e in visible_enemies if e.region_id == state.current_region.id]
        same_region_count = len(enemies_in_same_region)
        
        primary_enemy = enemies_in_same_region[0] if enemies_in_same_region else (visible_enemies[0] if visible_enemies else None)
        win_prob = WinProbabilityCalculator.calculate(player, primary_enemy) if primary_enemy else 1.0

        # Aturan Pengecualian Finish Kill
        if primary_enemy and same_region_count == 1:
            e_hp_ratio = primary_enemy.hp / primary_enemy.max_hp
            if e_hp_ratio < 0.15 and win_prob > 0.90 and not state.current_region.is_death_zone:
                logger.info(f"[RETREAT] Diabaikan demi Finish-Kill pada {primary_enemy.name} (HP: {primary_enemy.hp}).")
                return None

        # Evaluasi Trigger Retreat Instan (Hanya dipicu oleh ancaman satu region)
        retreat_reason: Optional[str] = None
        hp_ratio = player.hp / player.max_hp

        if hp_ratio <= HP_RETREAT_THRESHOLD:
            retreat_reason = "Low HP"
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

        # Cari Rute Pelarian Teraman
        best_escape_region_id = RetreatStrategy._find_safest_escape_region(state, memory)
        if not best_escape_region_id:
            return None

        logger.warning(
            f"\n[RETREAT]\n"
            f"Enemy Visible : {len(visible_enemies)} (Same Region: {same_region_count})\n"
            f"Reason        : {retreat_reason}\n"
            f"Current HP    : {player.hp}\n"
            f"Win Probability : {win_prob:.0%}\n"
            f"Escape Region : {best_escape_region_id}\n"
            f"Distance      : 1\n"
            f"Decision      : RETREAT\n"
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
        best_score = -9999.0

        for r_id in connections:
            score = PathScoring.score_region(r_id, state, memory)
            if score > best_score:
                best_score = score
                best_region_id = r_id

        return best_region_id
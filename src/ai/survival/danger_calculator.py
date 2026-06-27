"""
src/ai/survival/danger_calculator.py
Tanggung jawab: Menghitung Indeks Bahaya (Danger Score) terstandarisasi (0.0 - 100.0)
 berdasarkan HP, sisa EP, Badai, dan intensitas ancaman musuh sekitar.
"""

import logging
from src.models.game_state import GameState
from src.config.constants import (
    WEIGHT_DANGER_HP, WEIGHT_DANGER_ENEMY, 
    WEIGHT_DANGER_STORM, WEIGHT_DANGER_EP
)

logger = logging.getLogger("ClawRoyale.DangerCalculator")

class DangerCalculator:
    @staticmethod
    def calculate_danger_score(state: GameState) -> float:
        """
        Menghitung Danger Score kumulatif saat ini (0.0 - 100.0).
        Skor tinggi (>= 60.0) menandakan kondisi berbahaya yang memicu Emergency/Retreat.
        """
        player = state.player
        visible_enemies = state.visible_enemies
        current_region = state.current_region

        hp_ratio = player.hp / player.max_hp
        hp_risk = (1.0 - hp_ratio) * 100.0 * WEIGHT_DANGER_HP

        ep_ratio = player.ep / player.max_ep
        ep_risk = (1.0 - ep_ratio) * 100.0 * WEIGHT_DANGER_EP

        is_pending = False
        if state.pending_deathzones:
            for zone in state.pending_deathzones:
                if isinstance(zone, str):
                    if zone == current_region.id:
                        is_pending = True
                        break
                elif hasattr(zone, "id"):
                    if zone.id == current_region.id:
                        is_pending = True
                        break
                elif isinstance(zone, dict):
                    if zone.get("id") == current_region.id:
                        is_pending = True
                        break

        storm_risk = 0.0
        if current_region.is_death_zone:
            storm_risk = 100.0 * WEIGHT_DANGER_STORM
        elif is_pending:
            storm_risk = 50.0 * WEIGHT_DANGER_STORM

        enemy_risk = 0.0
        enemy_count = len(visible_enemies)
        if enemy_count > 0:
            enemy_ratio = min(1.0, enemy_count / 3.0)
            enemy_risk = enemy_ratio * 100.0 * WEIGHT_DANGER_ENEMY

        danger_score = hp_risk + ep_risk + storm_risk + enemy_risk
        danger_score = max(0.0, min(100.0, danger_score))

        logger.debug(
            f"[DANGER CALC] Danger Score: {danger_score:.1f} | "
            f"RiskBreakdown -> HP:{hp_risk:.1f}, EP:{ep_risk:.1f}, "
            f"Storm:{storm_risk:.1f}, Enemy:{enemy_risk:.1f}"
        )
        return danger_score
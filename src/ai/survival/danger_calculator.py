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

        # 1. Faktor Risiko HP (Semakin tipis HP, risiko semakin tinggi)
        hp_ratio = player.hp / player.max_hp
        hp_risk = (1.0 - hp_ratio) * 100.0 * WEIGHT_DANGER_HP

        # 2. Faktor Risiko EP (EP kritis membatasi kemampuan menyerang/kabur)
        ep_ratio = player.ep / player.max_ep
        ep_risk = (1.0 - ep_ratio) * 100.0 * WEIGHT_DANGER_EP

        # 3. Faktor Risiko Badai / Storm (Combat Rule: Storm paling berbahaya)
        storm_risk = 0.0
        if current_region.is_death_zone:
            storm_risk = 100.0 * WEIGHT_DANGER_STORM
        elif current_region.id in state.pending_deathzones:
            storm_risk = 50.0 * WEIGHT_DANGER_STORM

        # 4. Faktor Risiko Musuh (Jumlah musuh terlihat di sekitar)
        enemy_risk = 0.0
        enemy_count = len(visible_enemies)
        if enemy_count > 0:
            # Risiko dikalibrasi naik tajam jika musuh lebih dari 1 (risiko dikepung)
            enemy_ratio = min(1.0, enemy_count / 3.0)
            enemy_risk = enemy_ratio * 100.0 * WEIGHT_DANGER_ENEMY

        # Total Skor Bahaya Kumulatif
        danger_score = hp_risk + ep_risk + storm_risk + enemy_risk
        danger_score = max(0.0, min(100.0, danger_score))

        logger.debug(
            f"[DANGER CALC] Danger Score: {danger_score:.1f} | "
            f"RiskBreakdown -> HP:{hp_risk:.1f}, EP:{ep_risk:.1f}, "
            f"Storm:{storm_risk:.1f}, Enemy:{enemy_risk:.1f}"
        )
        return danger_score
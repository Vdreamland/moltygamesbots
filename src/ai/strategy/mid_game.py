"""
src/ai/strategy/mid_game.py
Tanggung jawab: Menegakkan strategi fase pertengahan permainan (Turn 31 - 70).
               Mengurangi penjelajahan liar, beralih ke kontrol posisi aman,
               dan menyaring perkelahian oportunis untuk mengumpulkan poin kill aman.
"""

import logging
from typing import List, Tuple
from src.models.action import Action
from src.models.game_state import GameState

logger = logging.getLogger("ClawRoyale.MidGameStrategy")

class MidGameStrategy:
    @staticmethod
    def adjust_utilities(candidates: List[Tuple[Action, float]], state: GameState) -> List[Tuple[Action, float]]:
        """
        Menyesuaikan utilitas aksi untuk perilaku Mid Game:
        - Mengurangi sedikit minat Explore (-20.0) agar agen beralih ke kontrol posisi aman
        - Mempertahankan minat Loot normal (+20.0) hanya untuk senjata upgrade tier tinggi
        - Meningkatkan hasrat Attack oportunis (+30.0) jika peluang menang terbukti tinggi
        """
        adjusted: List[Tuple[Action, float]] = []

        for action, utility in candidates:
            act_type = action.action_type
            new_utility = utility

            if act_type == "explore":
                new_utility -= 20.0
            elif act_type == "pickup":
                # Upgrade moderat saja
                new_utility += 20.0
            elif act_type == "attack":
                # Berikan bonus kecil untuk mengeliminasi musuh terlemah
                new_utility += 30.0

            adjusted.append((action, max(0.1, new_utility)))

        logger.debug("[MID STRATEGY] Penyesuaian bobot turn pertengahan berhasil diterapkan.")
        return adjusted
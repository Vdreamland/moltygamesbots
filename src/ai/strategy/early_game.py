"""
src/ai/strategy/early_game.py
Tanggung jawab: Menegakkan strategi fase awal permainan (Turn <= 30).
               Mendorong fokus penjarahan senjata (Loot) dan penjelajahan wilayah (Explore),
               serta meredam hasrat bertarung (Attack) untuk menghindari kematian dini.
"""

import logging
from typing import List, Tuple
from src.models.action import Action
from src.models.game_state import GameState

logger = logging.getLogger("ClawRoyale.EarlyGameStrategy")

class EarlyGameStrategy:
    @staticmethod
    def adjust_utilities(candidates: List[Tuple[Action, float]], state: GameState) -> List[Tuple[Action, float]]:
        """
        Menyesuaikan utilitas aksi untuk perilaku Early Game:
        - Meningkatkan hasrat Loot/Pickup (+60.0)
        - Meningkatkan hasrat Explore (+30.0)
        - Mengurangi hasrat Attack (-150.0) untuk menghindari perkelahian berisiko di awal
        """
        adjusted: List[Tuple[Action, float]] = []
        player = state.player

        for action, utility in candidates:
            act_type = action.action_type
            new_utility = utility

            if act_type == "pickup":
                # Cari tahu apakah kita sudah punya senjata
                if not player.equipped_weapon:
                    # Dorong mutlak hasrat mengambil senjata pertama
                    new_utility += 100.0
                else:
                    new_utility += 60.0
                    
            elif act_type == "explore":
                new_utility += 30.0
                
            elif act_type == "attack":
                # Kurangi agresivitas di awal turn kecuali musuh sangat sekarat
                new_utility -= 150.0

            adjusted.append((action, max(0.1, new_utility)))

        logger.debug("[EARLY STRATEGY] Penyesuaian bobot turn awal berhasil diterapkan.")
        return adjusted
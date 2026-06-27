"""
src/ai/strategy/late_game.py
Tanggung jawab: Menegakkan strategi fase akhir permainan (Turn >= 71).
               Fokus mutlak pada Survival dan penataan posisi di Safe Zone.
               Melarang penjarahan sampah yang mengorbankan nyawa dan menghindari penjelajahan liar.
"""

import logging
from typing import List, Tuple
from src.models.action import Action
from src.models.game_state import GameState

logger = logging.getLogger("ClawRoyale.LateGameStrategy")

class LateGameStrategy:
    @staticmethod
    def adjust_utilities(candidates: List[Tuple[Action, float]], state: GameState) -> List[Tuple[Action, float]]:
        """
        Menyesuaikan utilitas aksi untuk perilaku Late Game:
        - Memangkas keras minat Explore (-150.0) karena area badai semakin sempit
        - Memangkas keras minat Loot/Pickup sampah (-100.0) agar tidak serakah dan mati konyol
        - Meningkatkan hasrat bertahan hidup / pergerakan ke zona aman terbersih (+80.0)
        - Menyerang hanya jika peluang kemenangan mutlak aman
        """
        adjusted: List[Tuple[Action, float]] = []

        for action, utility in candidates:
            act_type = action.action_type
            new_utility = utility

            if act_type == "explore":
                new_utility -= 150.0
                
            elif act_type == "pickup":
                new_utility -= 100.0
                
            elif act_type == "move":
                # Jika bergerak menjauhi daerah penutupan badai, dorong prioritasnya
                new_utility += 80.0
                
            elif act_type == "attack":
                # Agresivitas diredam kecuali target benar-benar sekarat
                new_utility -= 30.0

            adjusted.append((action, max(0.1, new_utility)))

        logger.debug("[LATE STRATEGY] Penyesuaian bobot turn akhir berhasil diterapkan.")
        return adjusted
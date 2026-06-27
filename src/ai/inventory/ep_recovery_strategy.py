"""
src/ai/inventory/ep_recovery_strategy.py
Tanggung jawab: Mengevaluasi kapan harus memulihkan stamina (EP) agen.
               Menangani penggunaan item pemulih EP (Snack, Soda, Energy Drink)
               serta aksi istirahat taktis (RestAction / Smart REST).
"""

import logging
from typing import Optional, Tuple
from src.models.game_state import GameState
from src.models.action import Action, UseItemAction, RestAction

logger = logging.getLogger("ClawRoyale.EPRecoveryStrategy")

class EPRecoveryStrategy:
    @staticmethod
    def evaluate_ep_recovery(state: GameState) -> Optional[Tuple[Action, float]]:
        player = state.player
        inventory = player.inventory

        # Jangan mengisi EP jika ada musuh aktif/hidup di region murni yang sama
        enemies_in_same_region = [e for e in state.visible_enemies if e.region_id == state.current_region.id and e.is_alive]
        if len(enemies_in_same_region) > 0:
            logger.debug("[EP RECOVERY] Ditunda: Ada musuh aktif di ruangan yang sama.")
            return None

        # 1. PENGGUNAAN POTION EP (Stamina Potion) jika EP <= 3
        if player.ep <= 3:
            ep_potion = None
            for item in inventory:
                iname = item.name.lower()
                itype = item.type.lower()
                
                is_ep = "recovery_ep" in itype or any(k in iname for k in ["snack", "energy", "candy", "soda", "potion_ep", "drink"])
                if is_ep:
                    ep_potion = item
                    break

            if ep_potion:
                score = 120.0  # Prioritas tinggi untuk ramuan EP dibanding istirahat manual
                logger.info(f"[EP RECOVERY] Stamina rendah ({player.ep}). Menggunakan {ep_potion.name} (Skor: {score:.1f}).")
                return UseItemAction(
                    item_id=ep_potion.id,
                    thought=f"Menggunakan {ep_potion.name} untuk memulihkan cadangan stamina EP."
                ), score

            # 2. REST TAKTIS (Smart REST)
            # Hanya istirahat secara manual jika tidak memegang ramuan EP dan kondisi benar-benar aman
            score = 25.0  # Skor dasar istirahat agar tidak mengalahkan pergerakan taktis lainnya
            logger.info(f"[EP RECOVERY] Stamina rendah ({player.ep}) dan tidak ada ramuan EP. Beristirahat (Smart REST).")
            return RestAction(
                thought="Mengisi ulang energi (recharge) di lokasi sepi sebelum melanjutkan pergerakan."
            ), score

        return None
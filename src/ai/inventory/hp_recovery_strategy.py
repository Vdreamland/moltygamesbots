"""
src/ai/inventory/hp_recovery_strategy.py
Tanggung jawab: Mengevaluasi kapan harus mengonsumsi item pemulih HP (Food, Bandage, Medkit).
               Menegakkan Heal Rule: "Jangan heal di depan musuh".
"""

import logging
from typing import Optional, Tuple
from src.models.game_state import GameState
from src.models.action import UseItemAction

logger = logging.getLogger("ClawRoyale.HPRecoveryStrategy")

class HPRecoveryStrategy:
    @staticmethod
    def evaluate_hp_recovery(state: GameState) -> Optional[Tuple[UseItemAction, float]]:
        player = state.player
        inventory = player.inventory

        # Jangan makan/minum jika ada musuh aktif/hidup di region murni yang sama
        enemies_in_same_region = [e for e in state.visible_enemies if e.region_id == state.current_region.id and e.is_alive]
        if len(enemies_in_same_region) > 0:
            logger.debug("[HP RECOVERY] Ditunda: Ada musuh aktif di ruangan yang sama.")
            return None

        hp_ratio = player.hp / player.max_hp
        if hp_ratio > 0.75:
            return None

        hp_potion = None
        for item in inventory:
            iname = item.name.lower()
            itype = item.type.lower()
            
            is_hp = "recovery_hp" in itype or any(k in iname for k in ["food", "ration", "bandage", "medkit", "medical", "potion_hp"])
            if is_hp:
                hp_potion = item
                break  # Ambil item pemulih HP pertama yang dideteksi

        if hp_potion:
            # Semakin kritis HP, semakin tinggi prioritas pemulihan darah
            hp_pct = (1.0 - hp_ratio) * 100.0  # Jangkauan: 25.0 - 100.0
            score = 150.0 + hp_pct  # Skor dinamis tinggi saat sekarat
            
            logger.info(f"[HP RECOVERY] Darah rendah ({player.hp}/{player.max_hp}). Menggunakan {hp_potion.name} (Skor: {score:.1f}).")
            return UseItemAction(
                item_id=hp_potion.id,
                thought=f"Menggunakan {hp_potion.name} di posisi aman untuk memulihkan kesehatan HP."
            ), score

        return None
"""
src/ai/inventory/consumable_strategy.py
Tanggung jawab: Mengevaluasi kapan harus meminum ramuan pemulih (Potion HP / Potion EP).
               Menegakkan Heal Rule: "Jangan heal di depan musuh".
               Aksi use_item memakan 0 EP tetapi memicu 30s Cooldown.
"""

import logging
from typing import Optional
from src.models.game_state import GameState
from src.models.entities import Potion
from src.models.action import UseItemAction

logger = logging.getLogger("ClawRoyale.ConsumableStrategy")

class ConsumableStrategy:
    @staticmethod
    def evaluate_healing(state: GameState) -> Optional[UseItemAction]:
        player = state.player
        inventory = player.inventory
        visible_enemies = state.visible_enemies

        # [PERBAIKAN]: Hanya memblokir heal jika ada musuh AKTIF / HIDUP di region murni yang sama (is_alive)
        enemies_in_same_region = [e for e in visible_enemies if e.region_id == state.current_region.id and e.is_alive]
        if len(enemies_in_same_region) > 0:
            logger.debug("[CONSUMABLE] Ditunda: Ada musuh aktif di ruangan yang sama. Menunda penyembuhan.")
            return None

        hp_potion = None
        ep_potion = None

        # [PERBAIKAN - FAIL SAFE]: Deteksi hibrida tipe item secara aman tanpa bergantung murni pada isinstance Potion
        for item in inventory:
            iname = item.name.lower()
            itype = item.type.lower()
            
            is_hp = "recovery_hp" in itype or any(k in iname for k in ["food", "ration", "bandage", "medkit", "medical", "potion_hp"])
            is_ep = "recovery_ep" in itype or any(k in iname for k in ["snack", "energy", "candy", "soda", "potion_ep", "drink"])
            
            if is_hp:
                hp_potion = item
            elif is_ep:
                ep_potion = item

        # 1. Prioritas Utama: Pemulihan HP jika HP <= 75%
        hp_ratio = player.hp / player.max_hp
        if hp_ratio <= 0.75 and hp_potion:
            logger.info(f"[CONSUMABLE] Memutuskan meminum {hp_potion.name} (HP saat ini: {player.hp}/{player.max_hp}).")
            return UseItemAction(
                item_id=hp_potion.id,
                thought=f"Menggunakan {hp_potion.name} di posisi aman untuk memulihkan kesehatan HP."
            )

        # 2. Prioritas Kedua: Pemulihan EP jika EP <= 3
        if player.ep <= 3 and ep_potion:
            logger.info(f"[CONSUMABLE] Memutuskan meminum {ep_potion.name} (EP saat ini: {player.ep}).")
            return UseItemAction(
                item_id=ep_potion.id,
                thought=f"Menggunakan {ep_potion.name} untuk memulihkan cadangan energi EP."
            )

        return None
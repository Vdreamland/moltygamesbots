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

        # [REVISI]: Hanya memblokir heal jika ada musuh aktif di region yang sama
        enemies_in_same_region = [e for e in visible_enemies if e.region_id == state.current_region.id]
        if len(enemies_in_same_region) > 0:
            logger.debug("[CONSUMABLE] Ditunda: Ada musuh di ruangan yang sama. Menunda penyembuhan.")
            return None

        hp_potion: Optional[Potion] = None
        ep_potion: Optional[Potion] = None

        for item in inventory:
            if isinstance(item, Potion):
                if item.recovery_type == "hp":
                    hp_potion = item
                elif item.recovery_type == "ep":
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
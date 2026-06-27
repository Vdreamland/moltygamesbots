"""
src/ai/inventory/inventory_evaluator.py
Tanggung jawab: Agregator utilitas inventaris & logistik.
               Menghimpun dan menerapkan penimbang utilitas dinamis untuk Pickup, Equip, dan Use Item.
"""

import logging
from typing import List, Tuple
from src.models.game_state import GameState
from src.ai.memory.world_model import WorldModel
from src.models.action import Action
from src.ai.inventory.loot_strategy import LootStrategy
from src.ai.inventory.equip_strategy import EquipStrategy
from src.ai.inventory.consumable_strategy import ConsumableStrategy
from src.config.constants import WEIGHT_GOAL_LOOT, WEIGHT_GOAL_HEAL

logger = logging.getLogger("ClawRoyale.InventoryEvaluator")

class InventoryEvaluator:
    def __init__(self):
        pass

    def evaluate(self, state: GameState, memory: WorldModel) -> List[Tuple[Action, float]]:
        """
        Menilai peluang logistik dan mengembalikan daftar kandidat aksi inventaris.
        """
        candidates: List[Tuple[Action, float]] = []

        # 1. Evaluasi Auto-Equip Senjata Terkuat di Tas (0 EP, 0 Cooldown)
        equip_action = EquipStrategy.evaluate_auto_equip(state)
        if equip_action:
            candidates.append((equip_action, WEIGHT_GOAL_LOOT + 150.0))
            logger.info("[INV EVAL] Menyisipkan aksi instan EQUIP senjata terkuat.")
            return candidates

        # 2. Evaluasi Penggunaan Consumables / Potion (Heal)
        use_item_action = ConsumableStrategy.evaluate_healing(state)
        if use_item_action:
            candidates.append((use_item_action, WEIGHT_GOAL_HEAL))
            logger.info("[INV EVAL] Menyisipkan aksi USE ITEM ramuan pemulih.")

        # 3. Evaluasi Penjarahan Barang di Tanah (Pickup - Menggunakan Skor Dinamis)
        loot_result = LootStrategy.evaluate_ground_loot(state)
        if loot_result:
            pickup_action, loot_score = loot_result
            # Skor pickup disesuaikan secara dinamis agar lebih besar dibanding utilitas bergerak eksplorasi standar
            final_pickup_utility = WEIGHT_GOAL_LOOT + loot_score
            candidates.append((pickup_action, final_pickup_utility))
            logger.info(f"[INV EVAL] Menyisipkan aksi PICKUP dinamis (Utilitas: {final_pickup_utility:.2f}).")

        return candidates
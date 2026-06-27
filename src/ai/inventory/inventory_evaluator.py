"""
src/ai/inventory/inventory_evaluator.py
Tanggung jawab: Menggabungkan seluruh utilitas inventaris (looting, auto-equip, consumables)
               menjadi kandidat aksi inventaris taktis tunggal.
"""

import logging
from typing import List, Tuple, Any
from src.models.game_state import GameState
from src.models.action import Action
from src.config.constants import WEIGHT_GOAL_LOOT, BONUS_WEIGHT_EQUIP, BONUS_WEIGHT_CONSUMABLE
from src.ai.inventory.loot_strategy import LootStrategy
from src.ai.inventory.equip_strategy import EquipStrategy
from src.ai.inventory.consumable_strategy import ConsumableStrategy

logger = logging.getLogger("ClawRoyale.InventoryEvaluator")

class InventoryEvaluator:
    def __init__(self):
        self.loot_strategy = LootStrategy()
        self.equip_strategy = EquipStrategy()
        self.consumable_strategy = ConsumableStrategy()

    def evaluate(self, state: GameState, memory: Any = None) -> List[Tuple[Action, float]]:
        """
        Menilai kelayakan seluruh aksi inventaris (looting, auto-equip, consumables)
        dan mengembalikannya sebagai daftar kandidat aksi berbobot skor utilitas.
        """
        options: List[Tuple[Action, float]] = []

        # 1. Evaluasi Pemungutan Barang di Tanah (Looting)
        loot_result = self.loot_strategy.evaluate_ground_loot(state)
        if loot_result:
            loot_action, score = loot_result
            options.append((loot_action, WEIGHT_GOAL_LOOT + score))

        # 2. Evaluasi Penggunaan Consumables (Pemulih HP / EP)
        consumable_action = self.consumable_strategy.evaluate_healing(state)
        if consumable_action:
            # Berikan bonus berat khusus untuk penyembuhan darurat saat darah sekarat
            hp_ratio = state.player.hp / state.player.max_hp
            heal_boost = 180.0 if hp_ratio <= 0.40 else 0.0
            
            options.append((
                consumable_action, 
                BONUS_WEIGHT_CONSUMABLE + heal_boost
            ))

        # 3. Evaluasi Pemasangan Equipment Terkuat (Auto-Equip)
        equip_action = self.equip_strategy.evaluate_auto_equip(state)
        if equip_action:
            options.append((equip_action, BONUS_WEIGHT_EQUIP))

        return options
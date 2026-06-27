"""
src/ai/inventory/inventory_evaluator.py
Tanggung jawab: Menghasilkan utility score untuk inventory, looting, dan manajemen item.
"""

import logging
from typing import List, Tuple
from src.models.game_state import GameState
from src.ai.memory.world_model import WorldModel
from src.models.action import Action
from src.ai.inventory.loot_strategy import LootStrategy
from src.ai.inventory.equip_strategy import EquipStrategy
from src.ai.inventory.consumable_strategy import ConsumableStrategy
from src.config.constants import WEIGHT_GOAL_LOOT, BONUS_WEIGHT_EQUIP, BONUS_WEIGHT_CONSUMABLE

logger = logging.getLogger("ClawRoyale.InventoryEvaluator")

class InventoryEvaluator:
    def __init__(self):
        self.loot_strategy = LootStrategy()
        self.equip_strategy = EquipStrategy()
        self.consumable_strategy = ConsumableStrategy()

    def evaluate(self, state: GameState, memory: WorldModel) -> List[Tuple[Action, float]]:
        options: List[Tuple[Action, float]] = []

        # 1. Evaluasi Looting (Memanggil metode yang benar: evaluate_ground_loot)
        loot_result = self.loot_strategy.evaluate_ground_loot(state)
        if loot_result:
            loot_action, score = loot_result
            options.append((loot_action, WEIGHT_GOAL_LOOT + score))

        # 2. Evaluasi Equip (Weapon/Armor)
        equip_action = self.equip_strategy.evaluate_auto_equip(state)
        if equip_action:
            options.append((equip_action, WEIGHT_GOAL_LOOT + BONUS_WEIGHT_EQUIP))

        # 3. Evaluasi Consumable (Memanggil metode yang benar: evaluate)
        consumable_action = self.consumable_strategy.evaluate(state)
        if consumable_action:
            options.append((consumable_action, WEIGHT_GOAL_LOOT + BONUS_WEIGHT_CONSUMABLE))

        return options
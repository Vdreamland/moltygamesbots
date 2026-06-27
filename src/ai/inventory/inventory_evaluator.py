"""
src/ai/inventory/inventory_evaluator.py
Tanggung jawab: Menggabungkan seluruh utilitas inventaris (looting, auto-equip, pemulihan HP & EP)
               menjadi kandidat aksi inventaris taktis.
"""

import logging
from typing import List, Tuple, Any
from src.models.game_state import GameState
from src.models.action import Action
from src.config.constants import WEIGHT_GOAL_LOOT, BONUS_WEIGHT_EQUIP
from src.ai.inventory.loot_strategy import LootStrategy
from src.ai.inventory.equip_strategy import EquipStrategy
from src.ai.inventory.hp_recovery_strategy import HPRecoveryStrategy
from src.ai.inventory.ep_recovery_strategy import EPRecoveryStrategy

logger = logging.getLogger("ClawRoyale.InventoryEvaluator")

class InventoryEvaluator:
    def __init__(self):
        self.loot_strategy = LootStrategy()
        self.equip_strategy = EquipStrategy()

    def evaluate(self, state: GameState, memory: Any = None) -> List[Tuple[Action, float]]:
        """
        Menilai kelayakan seluruh aksi inventaris (looting, auto-equip, pemulihan HP/EP)
        dan mengembalikannya sebagai daftar kandidat aksi berbobot skor utilitas.
        """
        options: List[Tuple[Action, float]] = []

        # 1. Evaluasi Pemungutan Barang di Tanah (Looting)
        loot_result = self.loot_strategy.evaluate_ground_loot(state)
        if loot_result:
            loot_action, score = loot_result
            options.append((loot_action, WEIGHT_GOAL_LOOT + score))

        # 2. Evaluasi Pemulihan Darah (HP Recovery Strategy)
        hp_result = HPRecoveryStrategy.evaluate_hp_recovery(state)
        if hp_result:
            hp_action, score = hp_result
            options.append((hp_action, score))

        # 3. Evaluasi Pemulihan Stamina (EP Recovery Strategy + Smart REST)
        ep_result = EPRecoveryStrategy.evaluate_ep_recovery(state)
        if ep_result:
            ep_action, score = ep_result
            options.append((ep_action, score))

        # 4. Evaluasi Pemasangan Equipment Terkuat (Auto-Equip)
        equip_action = self.equip_strategy.evaluate_auto_equip(state)
        if equip_action:
            options.append((equip_action, BONUS_WEIGHT_EQUIP))

        return options
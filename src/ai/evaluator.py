"""
src/ai/evaluator.py
Tanggung jawab: Menggabungkan seluruh utilitas taktis, melakukan normalisasi skor, 
dan meranking opsi aksi berdasarkan skor utilitas terbesar.
"""

import logging
from typing import List, Tuple
from src.models.game_state import GameState
from src.ai.memory.world_model import WorldModel
from src.models.action import Action, RestAction

logger = logging.getLogger("ClawRoyale.Evaluator")

class Evaluator:
    def __init__(self):
        self.combat_evaluator = None
        self.movement_evaluator = None
        self.inventory_evaluator = None
        self.survival_evaluator = None

    def inject_sub_evaluators(self, combat, movement, inventory, survival):
        self.combat_evaluator = combat
        self.movement_evaluator = movement
        self.inventory_evaluator = inventory
        self.survival_evaluator = survival

    def evaluate_all_options(self, state: GameState, memory: WorldModel) -> List[Tuple[Action, float]]:
        options: List[Tuple[Action, float]] = []
        
        # [REVISI JANGKAUAN]: Deteksi canAct secara mendalam dari nested JSON
        data_payload = getattr(state, "data_payload", {})
        can_act = data_payload.get("canAct")
        if can_act is None:
            can_act = data_payload.get("view", {}).get("canAct")
        if can_act is None:
            can_act = data_payload.get("data", {}).get("canAct")
        if can_act is None:
            can_act = True

        if self.survival_evaluator:
            options.extend(self.survival_evaluator.evaluate(state, memory))

        if can_act:
            if self.combat_evaluator:
                options.extend(self.combat_evaluator.evaluate(state, memory))
            
            if self.movement_evaluator:
                options.extend(self.movement_evaluator.evaluate(state, memory))
            
            if self.inventory_evaluator:
                options.extend(self.inventory_evaluator.evaluate(state, memory))
        else:
            logger.debug("[EVALUATOR] Bot dalam cooldown, menahan aksi taktis berat.")

        if not options:
            options.append((RestAction(thought="Tidak ada aksi tersedia, beristirahat."), 0.1))

        options.sort(key=lambda x: x[1], reverse=True)
        return options
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
        
        # [REVISI]: Mengambil 'canAct' dari data mentah karena tidak ada di atribut GameState
        # Mengambil dari data_payload yang sudah dibersihkan di GameState.__init__
        can_act = state.data_payload.get("canAct", True)

        # 1. Evaluasi Aksi Bertahan Hidup (Heal, Run) - Selalu evaluasi
        if self.survival_evaluator:
            options.extend(self.survival_evaluator.evaluate(state, memory))

        # 2. Evaluasi Aksi Strategis (Attack, Move, Loot)
        # Hanya dievaluasi jika bot dalam status can_act = True
        if can_act:
            if self.combat_evaluator:
                options.extend(self.combat_evaluator.evaluate(state, memory))
            
            if self.movement_evaluator:
                options.extend(self.movement_evaluator.evaluate(state, memory))
            
            if self.inventory_evaluator:
                options.extend(self.inventory_evaluator.evaluate(state, memory))
        else:
            logger.debug("[EVALUATOR] Bot dalam cooldown, hanya memproses survival actions.")

        # 3. Default Fallback Action
        if not options:
            options.append((RestAction(thought="Tidak ada aksi tersedia, beristirahat."), 0.1))

        options.sort(key=lambda x: x[1], reverse=True)
        
        return options
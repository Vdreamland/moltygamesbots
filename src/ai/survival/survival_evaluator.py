"""
src/ai/survival/survival_evaluator.py
Tanggung jawab: Menggabungkan seluruh keputusan pertahanan hidup taktis (evakuasi storm, healing retreat).
"""

import logging
from typing import List, Tuple
from src.models.game_state import GameState
from src.models.action import Action
from src.ai.memory.world_model import WorldModel
from src.ai.survival.storm_strategy import StormStrategy
from src.ai.survival.healing_strategy import HealingStrategy

logger = logging.getLogger("ClawRoyale.SurvivalEvaluator")

class SurvivalEvaluator:
    def __init__(self):
        pass

    def evaluate(self, state: GameState, memory: WorldModel) -> List[Tuple[Action, float]]:
        candidates: List[Tuple[Action, float]] = []

        # 1. Evaluasi Evakuasi Storm (Dapatkan MoveAction dari StormStrategy)
        storm_action = StormStrategy.evaluate_storm_evacuation(state, memory)
        if storm_action:
            candidates.append((storm_action, 500.0))
            return candidates  # Mengabaikan aksi taktis lain jika badai adalah ancaman utama

        # 2. Evaluasi Heal Retreat (Dapatkan MoveAction dari HealingStrategy)
        heal_retreat_action = HealingStrategy.evaluate_heal_retreat(state, memory)
        if heal_retreat_action:
            candidates.append((heal_retreat_action, 400.0))
            return candidates

        return candidates
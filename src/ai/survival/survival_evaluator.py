"""
src/ai/survival/survival_evaluator.py
Tanggung jawab: Agregator utilitas kelangsungan hidup final.
 Mengevaluasi indeks bahaya dan menyisipkan aksi darurat seperti:
 - Storm Evacuation (Evakuasi Badai)
 - Heal Move (Mengungsi demi healing aman)
 - Smart REST (Istirahat preventif di posisi aman saat EP <= 4)
"""

import logging
from typing import List, Tuple
from src.models.game_state import GameState
from src.ai.memory.world_model import WorldModel
from src.models.action import Action, RestAction
from src.ai.survival.danger_calculator import DangerCalculator
from src.ai.survival.healing_strategy import HealingStrategy
from src.ai.survival.storm_strategy import StormStrategy
from src.config.constants import WEIGHT_GOAL_STORM, WEIGHT_GOAL_EMERGENCY, WEIGHT_GOAL_HEAL

logger = logging.getLogger("ClawRoyale.SurvivalEvaluator")

class SurvivalEvaluator:
    def __init__(self):
        pass

    def evaluate(self, state: GameState, memory: WorldModel) -> List[Tuple[Action, float]]:
        candidates: List[Tuple[Action, float]] = []
        player = state.player

        # 1. Hitung Indeks Bahaya Real-time (Danger Score)
        danger_score = DangerCalculator.calculate_danger_score(state)

        # 2. Evaluasi Evakuasi Badai Darurat (Storm Strategy)
        storm_evac_action = StormStrategy.evaluate_storm_evacuation(state, memory)
        if storm_evac_action:
            candidates.append((storm_evac_action, WEIGHT_GOAL_STORM))
            logger.warning("[SURVIVAL EVAL] Menyisipkan opsi EVAKUASI BADAI MUTLAK.")
            return candidates

        # 3. Evaluasi Kebutuhan "Heal Move" (Mengungsi demi healing aman)
        heal_move_action = HealingStrategy.evaluate_heal_retreat(state, memory)
        if heal_move_action:
            candidates.append((heal_move_action, WEIGHT_GOAL_EMERGENCY - 50.0))
            logger.info("[SURVIVAL EVAL] Menyisipkan opsi HEAL RETREAT (Jalur pelarian khusus healing).")

        # [REVISI]: Evaluasi musuh di region yang sama agar Smart REST dapat diaktifkan meski ada musuh di luar area
        enemies_in_same_region = [e for e in state.visible_enemies if e.region_id == state.current_region.id]

        # 4. SMART REST (Pengecasan Energi Preventif):
        if player.ep <= 4 and danger_score < 20.0 and len(enemies_in_same_region) == 0:
            candidates.append((
                RestAction(
                    thought="Mengisi ulang energi (recharge) di lokasi yang aman sebelum melanjutkan perjalanan."
                ),
                WEIGHT_GOAL_HEAL + 20.0
            ))
            logger.info(f"[SURVIVAL EVAL] Memicu aksi REST preventif (Sisa EP: {player.ep}/10).")

        return candidates
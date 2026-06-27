"""
src/ai/survival/survival_evaluator.py
Tanggung jawab: Agregator utilitas kelangsungan hidup final.
 Mengevaluasi indeks bahaya dan menyisipkan aksi darurat seperti:
 - Storm Evacuation (Evakuasi Badai)
 - Heal Move (Mengungsi demi healing aman)
 - Smart REST (Istirahat preventif di posisi aman saat EP <= 3)
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

        danger_score = DangerCalculator.calculate_danger_score(state)

        storm_evac_action = StormStrategy.evaluate_storm_evacuation(state, memory)
        if storm_evac_action:
            candidates.append((storm_evac_action, WEIGHT_GOAL_STORM))
            logger.warning("[SURVIVAL EVAL] Menyisipkan opsi EVAKUASI BADAI MUTLAK.")
            return candidates

        heal_move_action = HealingStrategy.evaluate_heal_retreat(state, memory)
        if heal_move_action:
            candidates.append((heal_move_action, WEIGHT_GOAL_EMERGENCY - 50.0))
            logger.info("[SURVIVAL EVAL] Menyisipkan opsi HEAL RETREAT (Jalur pelarian khusus healing).")

        # Deteksi musuh di region saat ini
        enemies_in_same_region = [e for e in state.visible_enemies if e.region_id == state.current_region.id]

        # [REVISI EP REST]: Lebih longgar. Jika EP <= 3 dan area lokal sepi, wajib REST untuk keamanan masa depan.
        if player.ep <= 3 and len(enemies_in_same_region) == 0:
            candidates.append((
                RestAction(
                    thought="Mengisi ulang energi (recharge) di lokasi sepi sebelum melanjutkan pergerakan."
                ),
                WEIGHT_GOAL_HEAL + 20.0
            ))
            logger.info(f"[SURVIVAL EVAL] Memicu aksi REST preventif (Sisa EP: {player.ep}/10).")

        return candidates
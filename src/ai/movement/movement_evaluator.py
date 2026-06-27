"""
src/ai/movement/movement_evaluator.py
Tanggung jawab: Menghitung utilitas pergerakan final untuk MoveAction dan ExploreAction.
 Mengamankan evakuasi badai dan memicu pengejaran musuh taktis (Chase Strategy).
"""

import logging
from typing import List, Tuple
from src.models.game_state import GameState
from src.ai.memory.world_model import WorldModel
from src.models.action import Action, MoveAction, ExploreAction
from src.ai.movement.path_scoring import PathScoring
from src.ai.movement.zone_strategy import ZoneStrategy
from src.config.constants import WEIGHT_GOAL_STORM, WEIGHT_GOAL_EXPLORE

logger = logging.getLogger("ClawRoyale.MovementEvaluator")

class MovementEvaluator:
    def __init__(self):
        pass

    def evaluate(self, state: GameState, memory: WorldModel) -> List[Tuple[Action, float]]:
        candidates: List[Tuple[Action, float]] = []
        connections = state.current_region.connections
        player = state.player

        if ZoneStrategy.is_in_danger_zone(state):
            escape_regions = ZoneStrategy.get_storm_escape_regions(state)
            if escape_regions:
                best_escape_id = max(escape_regions, key=lambda r: PathScoring.score_region(r, state, memory))
                candidates.append((
                    MoveAction(
                        region_id=best_escape_id,
                        thought="EVAKUASI BADAI MUTLAK! Keluar dari Death Zone menuju wilayah aman."
                    ),
                    WEIGHT_GOAL_STORM
                ))
                return candidates

        # [REVISI]: Pengejaran Cerdas (Chase Hunt) di wilayah tetangga
        if player.equipped_weapon and player.hp > 40 and player.ep >= 2:
            for enemy in state.visible_enemies:
                if enemy.region_id in connections:
                    # Hitung peluang menang nyata melawan musuh di wilayah tetangga
                    from src.ai.combat.win_probability import WinProbabilityCalculator
                    win_prob = WinProbabilityCalculator.calculate(player, enemy)
                    
                    # Jika peluang menang tinggi (>= 70%) ATAU musuh sangat sekarat (HP < 20), lakukan penyerbuan!
                    if (win_prob >= 0.70 or enemy.hp < 20) and enemy.region_id not in state.pending_deathzones:
                        chase_utility = 250.0
                        candidates.append((
                            MoveAction(
                                region_id=enemy.region_id,
                                thought=f"Menyerbu musuh di wilayah sebelah {enemy.name} (Peluang Menang: {win_prob*100:.1f}%) demi mengamankan eliminasi."
                            ),
                            chase_utility
                        ))
                        logger.info(f"[CHASE/HUNT] Memicu pengejaran musuh ke {enemy.region_id} (Win Prob: {win_prob*100:.1f}%)")

        for region_id in connections:
            path_score = PathScoring.score_region(region_id, state, memory)
            move_utility = WEIGHT_GOAL_EXPLORE + path_score
            candidates.append((
                MoveAction(
                    region_id=region_id,
                    thought=f"Eksplorasi wilayah ke {region_id} untuk mengumpulkan sumber daya."
                ),
                max(1.0, move_utility)
            ))

        ruin_gauge = state.current_region.ruin_gauge
        if ruin_gauge > 0 and ruin_gauge < 100:
            explore_utility = WEIGHT_GOAL_EXPLORE + 30.0
            candidates.append((
                ExploreAction(
                    thought=f"Mengisi ruin gauge di region {state.current_region.name}."
                ),
                explore_utility
            ))

        return candidates
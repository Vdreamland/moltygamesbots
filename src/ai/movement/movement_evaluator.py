"""
src/ai/movement/movement_evaluator.py
Tanggung jawab: Menghitung utilitas pergerakan final untuk MoveAction dan ExploreAction.
               Mengamankan evakuasi badai dan memicu pengejaran musuh sekarat (Chase Strategy).
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
        """
        Menilai seluruh opsi gerakan dan eksplorasi yang tersedia untuk turn ini.
        """
        candidates: List[Tuple[Action, float]] = []
        connections = state.current_region.connections
        player = state.player

        # ======================================================================
        # SKENARIO 1: ATURAN DARURAT BADAI (Storm Rules)
        # ======================================================================
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

        # ======================================================================
        # SKENARIO 2: CHASE STRATEGY (Pengejaran Musuh Sekarat di Luar Wilayah)
        # Jika bersenjata, HP sehat (>40), sisa EP aman (>=2), dan ada musuh terdeteksi
        # sekarat (HP < 20) di salah satu region tetangga, kejar mereka!
        # ======================================================================
        if player.equipped_weapon and player.hp > 40 and player.ep >= 2:
            for enemy in state.visible_enemies:
                if enemy.region_id in connections and enemy.hp < 20:
                    # Pastikan region tujuan pengejaran bukan daerah badai
                    if enemy.region_id not in state.pending_deathzones:
                        chase_utility = 250.0  # Utilitas tinggi untuk mengejar target empuk
                        candidates.append((
                            MoveAction(
                                region_id=enemy.region_id,
                                thought=f"Mengejar musuh sekarat {enemy.name} (HP: {enemy.hp}) ke {enemy.region_id} demi poin kill aman."
                            ),
                            chase_utility
                        ))
                        logger.info(f"[CHASE] Memicu aksi pengejaran taktis ke {enemy.region_id} untuk mengeksekusi {enemy.name}.")

        # ======================================================================
        # SKENARIO 3: PERGERAKAN NORMAL / PENJELAJAHAN (Explore & Move)
        # ======================================================================
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

        # Explore Reruntuhan (Ruin Gauge Charging)
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
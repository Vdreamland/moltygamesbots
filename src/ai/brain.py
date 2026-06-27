"""
src/ai/brain.py
Tanggung jawab: Entry point berpikir AI, mengintegrasikan memori, seluruh sub-evaluator,
               dan menyelaraskan status Darurat secara presisi dengan State Machine (GoalSelector).
"""

import logging
from typing import Optional
from src.models.game_state import GameState
from src.models.action import Action
from src.ai.memory.world_model import WorldModel
from src.ai.planner import Planner
from src.ai.evaluator import Evaluator
from src.ai.action_selector import ActionSelector
from src.ai.strategy.goal_selector import GoalSelector

from src.ai.combat.combat_evaluator import CombatEvaluator
from src.ai.movement.movement_evaluator import MovementEvaluator
from src.ai.inventory.inventory_evaluator import InventoryEvaluator
from src.ai.survival.survival_evaluator import SurvivalEvaluator

logger = logging.getLogger("ClawRoyale.Brain")

class Brain:
    def __init__(self):
        self.memory = WorldModel()
        self.planner = Planner()
        self.evaluator = Evaluator()
        self.selector = ActionSelector()
        
        self.combat_eval = CombatEvaluator()
        self.movement_eval = MovementEvaluator()
        self.inventory_eval = InventoryEvaluator()
        self.survival_eval = SurvivalEvaluator()
        
        self.evaluator.inject_sub_evaluators(
            combat=self.combat_eval,
            movement=self.movement_eval,
            inventory=self.inventory_eval,
            survival=self.survival_eval
        )
        
        self.emergency_mode_active = False

    def think(self, state: GameState) -> Action:
        logger.info(f"=== [BRAIN] MEMULAI BERPIKIR TURN {state.turn} ===")
        
        self.memory.update(state)
        self.memory.clean_expired_memories(state.turn)

        current_mode = GoalSelector.get_current_mode(state)
        is_in_storm = state.current_region.is_death_zone
        
        if current_mode == "RETREAT" or is_in_storm:
            if not self.emergency_mode_active:
                logger.warning(f"[BRAIN] !!! DARURAT !!! EMERGENCY MODE DIAKTIFKAN. (Sebab: {current_mode})")
                self.emergency_mode_active = True
                self.planner.clear(reason=f"Emergency Mode Active ({current_mode})")
        else:
            if self.emergency_mode_active:
                logger.info("[BRAIN] Kondisi membaik. Emergency Mode dinonaktifkan.")
                self.emergency_mode_active = False

        enemies_in_same_region = [e for e in state.visible_enemies if e.region_id == state.current_region.id and e.is_alive]
        
        # [REVISI ANTI-SPAM]: Menghentikan eksekusi fall-through. Jika planner punya aksi tapi sedang menahan (cooldown), kembalikan None!
        if self.planner.has_actions() and not self.emergency_mode_active:
            if enemies_in_same_region:
                logger.warning("[BRAIN] Musuh terdeteksi di area yang sama selama eksekusi rencana berantai. Membersihkan Planner!")
                self.planner.clear(reason="Enemy entered current region")
            else:
                return self.planner.get_next_action(state)

        # Hanya lakukan evaluasi jika planner benar-benar kosong
        if not self.planner.has_actions():
            candidates = self.evaluator.evaluate_all_options(state, self.memory)
            candidates = GoalSelector.select_goal_and_adjust(candidates, state)
            final_action = self.selector.validate_and_select(candidates, state)
            
            if final_action:
                if final_action.action_type == "move" and self.emergency_mode_active:
                    self.memory.record_retreat_movement(state.current_region.id, state.turn)
                self.planner.add_actions([final_action])
                
            return self.planner.get_next_action(state)

        return None
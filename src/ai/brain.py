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

# Impor Sub-Evaluator Taktis
from src.ai.combat.combat_evaluator import CombatEvaluator
from src.ai.movement.movement_evaluator import MovementEvaluator
from src.ai.inventory.inventory_evaluator import InventoryEvaluator
from src.ai.survival.survival_evaluator import SurvivalEvaluator

logger = logging.getLogger("ClawRoyale.Brain")

class Brain:
    def __init__(self):
        # 1. Inisialisasi Memori, Planner, Evaluator Utama, dan Selector
        self.memory = WorldModel()
        self.planner = Planner()
        self.evaluator = Evaluator()
        self.selector = ActionSelector()
        
        # 2. Inisialisasi Seluruh Sub-Evaluator Taktis
        self.combat_eval = CombatEvaluator()
        self.movement_eval = MovementEvaluator()
        self.inventory_eval = InventoryEvaluator()
        self.survival_eval = SurvivalEvaluator()
        
        # Suntikkan sub-evaluators ke dalam Evaluator utama
        self.evaluator.inject_sub_evaluators(
            combat=self.combat_eval,
            movement=self.movement_eval,
            inventory=self.inventory_eval,
            survival=self.survival_eval
        )
        
        # State internal darurat
        self.emergency_mode_active = False

    def think(self, state: GameState) -> Action:
        """
        Fungsi eksekusi berpikir per turn.
        Mengimplementasikan hirarki pengambilan keputusan (Decision Order).
        """
        logger.info(f"=== [BRAIN] MEMULAI BERPIKIR TURN {state.turn} ===")
        
        # 1. Sinkronisasi memori dunia dengan data state terbaru
        self.memory.update(state)
        self.memory.clean_expired_memories(state.turn)

        # 2. Ambil Mode Taktis Aktif dari State Machine (GoalSelector)
        current_mode = GoalSelector.get_current_mode(state)

        # ==========================================================================
        # SINKRONISASI EMERGENCY MODE (Sangat Hati-Hati):
        # Status Darurat diselaraskan 100% dengan State Machine taktis (RETREAT)
        # atau jika agen sedang berada di wilayah badai aktif (is_death_zone).
        # ==========================================================================
        is_in_storm = state.current_region.is_death_zone
        
        if current_mode == "RETREAT" or is_in_storm:
            if not self.emergency_mode_active:
                logger.warning(f"[BRAIN] !!! DARURAT !!! EMERGENCY MODE DIAKTIFKAN. (Sebab: {current_mode})")
                self.emergency_mode_active = True
                # Kosongkan rencana lama demi penyelamatan diri instan
                self.planner.clear(reason=f"Emergency Mode Aktif ({current_mode})")
        else:
            if self.emergency_mode_active:
                logger.info("[BRAIN] Kondisi membaik. Emergency Mode dinonaktifkan.")
                self.emergency_mode_active = False

        # 3. KEPUTUSAN UTAMA: Hirarki Decision Order
        
        # Skenario A: Eksekusi rencana taktis berantai di Planner yang tertunda (jika aman)
        if self.planner.has_actions() and not self.emergency_mode_active:
            next_action = self.planner.get_next_action(state)
            if next_action:
                return next_action

        # Skenario B: Kalkulasi Evaluasi Utilitas Komprehensif
        # Ambil seluruh kandidat aksi dari Survival, Combat, Movement, dan Inventory Evaluators
        candidates = self.evaluator.evaluate_all_options(state, self.memory)
        
        # Sunting bobot utilitas kandidat aksi secara dinamis berdasarkan Fase State Machine
        candidates = GoalSelector.select_goal_and_adjust(candidates, state)
        
        # Filter kelayakan teknis (cooldown & sisa EP) dan pilih aksi final terbaik
        final_action = self.selector.validate_and_select(candidates, state)
        
        # Jika melakukan retreat darurat, catat wilayah awal pelarian demi penegakan No-Loop Rule
        if final_action.action_type == "move" and self.emergency_mode_active:
            self.memory.record_retreat_movement(state.current_region.id, state.turn)

        logger.info(f"=== [BRAIN] AKSI PILIHAN AKHIR: {final_action.action_type} ===")
        return final_action
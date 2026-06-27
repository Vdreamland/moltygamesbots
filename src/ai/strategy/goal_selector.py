"""
src/ai/strategy/goal_selector.py
Tanggung jawab: Menentukan State Machine / AIMode aktif (LOOT, COMBAT, RETREAT, SURVIVAL)
               dan memodifikasi utilitas aksi secara konsisten untuk mencapai tujuan taktis.
               Mendukung bypass kenaikan utilitas serang khusus untuk finisher tangan kosong.
"""

import logging
from typing import List, Tuple
from src.models.game_state import GameState
from src.models.action import Action
from src.config.constants import HP_EMERGENCY_THRESHOLD

logger = logging.getLogger("ClawRoyale.GoalSelector")

class GoalSelector:
    @staticmethod
    def get_current_mode(state: GameState) -> str:
        """
        Menentukan mode taktis aktif (State Machine) berdasarkan GameState.
        """
        player = state.player
        visible_enemies = state.visible_enemies
        current_region = state.current_region
        
        # Hitung musuh di region yang sama dengan kita
        enemies_same_region = sum(1 for e in visible_enemies if e.region_id == current_region.id)
        hp_ratio = player.hp / player.max_hp

        # 1. State RETREAT (HP Kritis <= 35%)
        if hp_ratio <= 0.35 or enemies_same_region >= 2:
            return "RETREAT"

        # 2. State LOOT (Prioritas Perlengkapan)
        if player.equipped_weapon is None:
            return "LOOT"

        # 3. State SURVIVAL (Late Game / Storm Evac)
        if state.turn >= 71 or current_region.is_death_zone:
            return "SURVIVAL"

        # 4. State COMBAT (Default Armed & Safe)
        return "COMBAT"

    @staticmethod
    def select_goal_and_adjust(candidates: List[Tuple[Action, float]], state: GameState) -> List[Tuple[Action, float]]:
        """
        Mengambil keputusan State Machine aktif, menerapkan pengali utilitas khusus,
        dan mengembalikan list kandidat aksi yang telah disesuaikan.
        """
        mode = GoalSelector.get_current_mode(state)
        logger.info(f"[AIMODE] State Machine Aktif: {mode} (Turn: {state.turn})")

        adjusted: List[Tuple[Action, float]] = []

        for action, utility in candidates:
            act_type = action.action_type
            new_utility = utility

            # Penerapan Modifikasi Skor Berdasarkan State Machine
            if mode == "RETREAT":
                if act_type == "move":
                    new_utility += 100.0
                else:
                    new_utility -= 200.0

            elif mode == "LOOT":
                if act_type == "pickup":
                    new_utility += 150.0
                elif act_type == "explore":
                    new_utility += 50.0
                elif act_type == "attack":
                    # ==================================================================
                    # BYPASS LOOT ATTACK (UNARMED FINISHER):
                    # Jika ada peluang membunuh target sekarat (HP <= 5) satu area,
                    # bypass penalti menyerang dan dorong skor ke utilitas tertinggi (+250)!
                    # ==================================================================
                    target_id = action.data.get("targetId")
                    target_enemy = next((e for e in state.visible_enemies if e.id == target_id), None)
                    
                    is_unarmed_finisher = (
                        target_enemy is not None and 
                        target_enemy.hp <= 5 and 
                        target_enemy.region_id == state.current_region.id
                    )
                    
                    if is_unarmed_finisher:
                        new_utility += 250.0  # Dongkrak mutlak agar segera dipukul mati!
                        logger.info(f"[AIMODE] Memicu peluang eksekusi FINISHER tangan kosong pada {target_enemy.name}!")
                    else:
                        new_utility -= 300.0  # Tetap haram menyerang musuh sehat tanpa senjata

            elif mode == "SURVIVAL":
                if act_type == "move":
                    new_utility += 50.0
                elif act_type == "pickup":
                    new_utility -= 80.0

            elif mode == "COMBAT":
                if act_type == "attack":
                    new_utility += 80.0

            adjusted.append((action, max(0.1, new_utility)))

        # Urutkan kembali kandidat berdasarkan utilitas tertinggi
        adjusted.sort(key=lambda x: x[1], reverse=True)
        return adjusted
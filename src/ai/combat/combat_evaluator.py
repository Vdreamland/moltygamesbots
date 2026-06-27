"""
src/ai/combat/combat_evaluator.py
Tanggung jawab: Agregator utilitas taktis pertempuran.
               Menghasilkan kandidat aksi serang atau melarikan diri dengan bobot prioritas dinamis.
               Mengamankan optimasi CPU dengan melewati modul jika tidak bersenjata,
               kecuali ada peluang finisher tangan kosong (HP <= 5) di region kita.
"""

import logging
from typing import List, Tuple
from src.models.game_state import GameState
from src.ai.memory.world_model import WorldModel
from src.models.action import Action, AttackAction
from src.ai.combat.target_selector import TargetSelector
from src.ai.combat.attack_strategy import AttackStrategy
from src.ai.combat.retreat_strategy import RetreatStrategy
from src.config.constants import WEIGHT_GOAL_ATTACK, WEIGHT_GOAL_EMERGENCY

logger = logging.getLogger("ClawRoyale.CombatEvaluator")

class CombatEvaluator:
    def __init__(self):
        pass

    def evaluate(self, state: GameState, memory: WorldModel) -> List[Tuple[Action, float]]:
        """
        Mengevaluasi opsi pertempuran dan mengembalikan daftar aksi potensial dengan skor utilitasnya.
        """
        # ==========================================================================
        # CPU OPTIMIZATION & UNARMED FINISHER CHECK:
        # Jika tidak bersenjata, lewati seluruh modul, KECUALI ada musuh/monster
        # yang sangat sekarat (HP <= 5) berdiri satu ruangan dengan kita untuk dieksekusi!
        # ==========================================================================
        if not state.player.equipped_weapon:
            has_unarmed_finisher = any(
                e.hp <= 5 and e.region_id == state.current_region.id 
                for e in state.visible_enemies
            )
            if not has_unarmed_finisher:
                return []

        candidates: List[Tuple[Action, float]] = []
        
        # Ambil target musuh terbaik yang terlihat
        target = TargetSelector.select_best_target(state)
        if not target:
            return candidates

        # Cek apakah kondisi taktis mengharuskan kita RETREAT instan (Rule 13B)
        retreat_action = RetreatStrategy.evaluate_retreat(state, memory)
        if retreat_action:
            candidates.append((retreat_action, WEIGHT_GOAL_EMERGENCY))
            logger.info(f"[COMBAT EVAL] Retreat terpicu. Menyisipkan rute pelarian ke daftar aksi.")
            return candidates

        # Evaluasi apakah aman melakukan serangan
        if AttackStrategy.should_attack(state, target):
            hp_factor = (target.max_hp - target.hp) / target.max_hp
            attack_utility = WEIGHT_GOAL_ATTACK + (hp_factor * 50.0)
            
            candidates.append((
                AttackAction(
                    target_id=target.id,
                    thought=f"Menyerang {target.name} karena peluang menang tinggi dan posisi aman."
                ),
                attack_utility
            ))
            logger.info(f"[COMBAT EVAL] Menyisipkan opsi SERANG {target.name} (Utilitas: {attack_utility:.2f})")

        return candidates
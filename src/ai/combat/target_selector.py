"""
src/ai/combat/target_selector.py
Tanggung jawab: Memilih target terbaik berdasarkan 7 aturan prioritas taktis (Target Priority).
"""

import logging
from typing import List, Optional
from src.models.game_state import GameState
from src.models.entities import Agent
from src.ai.combat.win_probability import WinProbabilityCalculator

logger = logging.getLogger("ClawRoyale.TargetSelector")

class TargetSelector:
    @staticmethod
    def select_best_target(state: GameState) -> Optional[Agent]:
        player = state.player
        visible_enemies = state.visible_enemies
        if not visible_enemies:
            return None

        def get_target_score(enemy: Agent) -> float:
            score = 0.0
            
            # Hitung jarak murni ke region target
            distance = 0
            if enemy.region_id != state.current_region.id:
                if enemy.region_id in state.current_region.connections:
                    distance = 1
                else:
                    distance = 2
            
            weapon_range = player.equipped_weapon.range if player.equipped_weapon else 0
            
            # [REVISI JANGKAUAN]: Beri penalti raksasa jika musuh di luar jangkauan senjata (paling diabaikan)
            if distance > weapon_range:
                score += 1000.0
                
            # Beri bonus prioritas jika musuh berada di region yang sama
            if distance == 0:
                score -= 150.0
                
            score += enemy.hp * 1.0
            
            if not enemy.equipped_weapon:
                score -= 100.0
            
            score += enemy.ep * 0.5
            
            win_prob = WinProbabilityCalculator.calculate(state.player, enemy)
            score -= (win_prob * 150.0)
            
            return score

        sorted_enemies = sorted(visible_enemies, key=get_target_score)
        best_target = sorted_enemies[0]
        
        # Hitung jarak ke target terbaik
        distance = 0
        if best_target.region_id != state.current_region.id:
            if best_target.region_id in state.current_region.connections:
                distance = 1
            else:
                distance = 2
                
        weapon_range = player.equipped_weapon.range if player.equipped_weapon else 0
        
        # [REVISI JANGKAUAN]: Jika target terbaik pun di luar jangkauan senjata murni kita, return None
        if distance > weapon_range:
            logger.debug(f"[TARGET] Mengabaikan target {best_target.name} karena berada di luar jangkauan (Jarak: {distance}, Range Senjata: {weapon_range}).")
            return None
            
        logger.info(f"[TARGET] Target terpilih: {best_target.name} (HP: {best_target.hp}, Weapon: {best_target.equipped_weapon.name if best_target.equipped_weapon else 'None'})")
        return best_target
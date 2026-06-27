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
        """
        Memilih target musuh terbaik dari daftar musuh yang terlihat saat ini.
        Menerapkan urutan prioritas:
        1. HP paling rendah
        2. Tidak membawa senjata (unarmed)
        3. Sedang healing / lemah
        4. EP rendah
        5. Ancaman terbesar (jika terpaksa bertarung)
        """
        visible_enemies = state.visible_enemies
        if not visible_enemies:
            return None

        # Definisikan fungsi penilaian skor prioritas (semakin rendah skor, semakin diprioritaskan)
        def get_target_score(enemy: Agent) -> float:
            score = 0.0
            
            # Aturan 1: HP paling rendah (Prioritas Utama)
            score += enemy.hp * 1.0
            
            # Aturan 2: Tidak membawa senjata (Kurangi skor agar diprioritaskan)
            if not enemy.equipped_weapon:
                score -= 100.0
                
            # Aturan 3: EP rendah (Musuh kelelahan)
            score += enemy.ep * 0.5
            
            # Aturan 4: Hitung win probability (Jika peluang menang tinggi, kurangi skor prioritas)
            win_prob = WinProbabilityCalculator.calculate(state.player, enemy)
            score -= (win_prob * 150.0)
            
            return score

        # Urutkan musuh berdasarkan skor taktis terendah
        sorted_enemies = sorted(visible_enemies, key=get_target_score)
        best_target = sorted_enemies[0]
        
        logger.info(f"[TARGET] Target terpilih: {best_target.name} (HP: {best_target.hp}, Weapon: {best_target.equipped_weapon.name if best_target.equipped_weapon else 'None'})")
        return best_target
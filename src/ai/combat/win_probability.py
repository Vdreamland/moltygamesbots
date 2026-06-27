"""
src/ai/combat/win_probability.py
Tanggung jawab: Menghitung peluang menang duel secara deterministik.
               Membandingkan HP, damage, EP cost, range, tier senjata,
               serta memperhitungkan mitigasi ketahanan DEF (Armor).
"""

import logging
from typing import Optional
from src.models.entities import Agent, Weapon

logger = logging.getLogger("ClawRoyale.WinProbability")

class WinProbabilityCalculator:
    @staticmethod
    def calculate(player: Agent, enemy: Agent) -> float:
        """
        Menghitung persentase peluang menang (0.0 - 1.0) melawan musuh spesifik.
        Formula memperhitungkan pengurangan damage berdasarkan DEF (Armor) absolut.
        """
        # 1. Tentukan kekuatan senjata player
        p_weapon = player.equipped_weapon
        p_dmg = p_weapon.damage if p_weapon else 5
        p_ep_cost = p_weapon.ep_cost if p_weapon else 1
        p_tier = p_weapon.tier if p_weapon else 0
        
        p_efficiency = p_dmg / max(1, p_ep_cost)
        p_power = p_efficiency * (1.0 + (p_tier * 0.15))

        # 2. Tentukan kekuatan senjata musuh
        e_weapon = enemy.equipped_weapon
        e_dmg = e_weapon.damage if e_weapon else 5
        e_ep_cost = e_weapon.ep_cost if e_weapon else 1
        e_tier = e_weapon.tier if e_weapon else 0
        
        e_efficiency = e_dmg / max(1, e_ep_cost)
        e_power = e_efficiency * (1.0 + (e_tier * 0.15))

        # ==========================================================================
        # MITIGASI PERTAHANAN (DEF/ARMOR):
        # Damage teoretis dikurangi oleh status DEF (Armor) aslinya
        # ==========================================================================
        p_mitigated_power = max(1.0, p_power - enemy.defense)
        e_mitigated_power = max(1.0, e_power - player.defense)

        # 3. Hitung Time-to-Kill (TTK) dengan reduksi damage DEF
        p_survival_turns = player.hp / e_mitigated_power
        e_survival_turns = enemy.hp / p_mitigated_power

        # 4. Normalisasi rasio kelangsungan hidup
        total_survival = p_survival_turns + e_survival_turns
        if total_survival <= 0:
            return 0.5
            
        win_prob = p_survival_turns / total_survival

        # 5. Penalti/Bonus Taktis Tambahan
        if player.ep <= 1:
            win_prob *= 0.5
            
        if not enemy.equipped_weapon:
            win_prob = max(win_prob, 0.85)

        win_prob = max(0.01, min(0.99, win_prob))
        return win_prob
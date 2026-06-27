"""
src/ai/combat/win_probability.py
Tanggung jawab: Menghitung persentase peluang menang (Win Probability) melawan musuh spesifik.
"""

from typing import TYPE_CHECKING

# Menggunakan TYPE_CHECKING untuk menghindari circular import pada model Entities
if TYPE_CHECKING:
    from src.models.entities import Agent

class WinProbabilityCalculator:
    @staticmethod
    def calculate(player: 'Agent', enemy: 'Agent') -> float:
        """
        Menghitung persentase peluang menang (0.0 - 1.0) melawan musuh spesifik.
        Formula memperhitungkan pengurangan damage berdasarkan DEF (Armor) absolut,
        serta memberikan penalti jika musuh memiliki jangkauan (range) lebih jauh.
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

        # [REVISI AUDIT]: Kalkulasi Jarak (Range Penalty)
        # Jika musuh memiliki jangkauan lebih jauh, asumsikan musuh mendapat "free hits" 
        # sejumlah selisih range sebelum bot bisa menyerang.
        p_range = p_weapon.range if p_weapon else 1
        e_range = e_weapon.range if e_weapon else 1
        
        range_diff = max(0, e_range - p_range)
        effective_p_hp = player.hp - (range_diff * e_mitigated_power)

        # 3. Hitung Time-to-Kill (TTK) dengan reduksi damage DEF & penalti jarak
        if effective_p_hp <= 0:
            p_survival_turns = 0.1 # Bot diprediksi mati sebelum bisa menyentuh musuh
        else:
            p_survival_turns = effective_p_hp / e_mitigated_power
            
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
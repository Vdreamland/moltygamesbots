"""
src/ai/inventory/weapon_strategy.py
Tanggung jawab: Membandingkan kekuatan senjata secara deterministik (Weapon Rules).
               Memastikan upgrade senjata dilakukan hanya jika benar-benar lebih kuat.
"""

import logging
from typing import Optional
from src.models.entities import Weapon

logger = logging.getLogger("ClawRoyale.WeaponStrategy")

class WeaponStrategy:
    @staticmethod
    def calculate_weapon_score(weapon: Optional[Weapon]) -> float:
        """
        Menghitung nilai skor absolut kekuatan senjata.
        Formula: (Damage / EP Cost) * (1.0 + Tier * 0.20) + (Range * 3.0)
        Senjata kosong (unarmed/tinju) memiliki skor dasar paling rendah (5.0).
        """
        if not weapon:
            return 5.0  # Default unarmed/fist score
            
        damage = max(1, weapon.damage)
        ep_cost = max(1, weapon.ep_cost)
        range_val = max(1, weapon.range)
        tier = max(0, weapon.tier)

        # Efisiensi serangan (damage per EP)
        efficiency = damage / ep_cost
        # Bonus tier (Tier 1 +20%, Tier 2 +40%, dst)
        tier_multiplier = 1.0 + (tier * 0.20)
        # Bonus range (semakin jauh range senjata, semakin aman & fleksibel)
        range_bonus = range_val * 3.0

        score = (efficiency * tier_multiplier) + range_bonus
        return score

    @classmethod
    def should_upgrade(cls, current_weapon: Optional[Weapon], target_weapon: Weapon) -> bool:
        """
        Membandingkan senjata aktif dengan target senjata baru.
        Mengembalikan True jika target senjata baru secara deterministik lebih kuat.
        """
        current_score = cls.calculate_weapon_score(current_weapon)
        target_score = cls.calculate_weapon_score(target_weapon)

        is_better = target_score > current_score
        if is_better:
            curr_name = current_weapon.name if current_weapon else "Unarmed"
            logger.info(f"[WEAPON EVAL] Potensi Upgrade Terdeteksi: {curr_name} (Skor: {current_score:.1f}) -> {target_weapon.name} (Skor: {target_score:.1f})")
            
        return is_better
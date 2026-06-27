"""
src/ai/inventory/equip_strategy.py
Tanggung jawab: Mengotomatiskan pemasangan (equip) senjata DAN baju zirah terbaik dari tas.
               Dilengkapi fitur Fail-Safe Dynamic Upcaster untuk menjamin senjata & zirah
               capital-mismatch dari server tetap terpasang instan ke slotnya masing-masing.
"""

import logging
from typing import Optional
from src.models.game_state import GameState
from src.models.entities import Weapon, Armor
from src.models.action import EquipAction
from src.ai.inventory.weapon_strategy import WeaponStrategy

logger = logging.getLogger("ClawRoyale.EquipStrategy")

class EquipStrategy:
    @staticmethod
    def calculate_armor_score(armor: Optional[Armor]) -> float:
        """Menghitung skor kelayakan absolut zirah pertahanan"""
        if not armor:
            return 0.0
        # Formula: Pertahanan absolut dikali bonus tier
        return float(armor.defense) * (1.0 + armor.tier * 0.20)

    @staticmethod
    def evaluate_auto_equip(state: GameState) -> Optional[EquipAction]:
        inventory = state.player.inventory
        
        # 1. EVALUASI AUTO-EQUIP SENJATA
        current_weapon = state.player.equipped_weapon
        best_weapon_in_bag: Optional[Weapon] = None
        best_weapon_score = WeaponStrategy.calculate_weapon_score(current_weapon)
        
        # 2. EVALUASI AUTO-EQUIP ZIRAH (ARMOR)
        current_armor = state.player.equipped_armor
        best_armor_in_bag: Optional[Armor] = None
        best_armor_score = EquipStrategy.calculate_armor_score(current_armor)

        # Cari barang penunjang terkuat di dalam tas
        for item in inventory:
            # A. Deteksi Kategori Senjata (Weapon)
            is_weapon = isinstance(item, Weapon) or str(getattr(item, "type", "")).lower() == "weapon"
            if is_weapon:
                weapon_item = item
                if not isinstance(item, Weapon):
                    stats = item.raw_data.get("stats", {}) or {}
                    weapon_item = Weapon(
                        id=item.id,
                        name=item.name,
                        type="weapon",
                        tier=item.tier,
                        damage=int(stats.get("damage", item.raw_data.get("damage", 15))),
                        range=int(stats.get("range", item.raw_data.get("range", 1))),
                        ep_cost=int(stats.get("epCost", item.raw_data.get("ep_cost", 1))),
                        raw_data=item.raw_data
                    )
                
                score = WeaponStrategy.calculate_weapon_score(weapon_item)
                if score > best_weapon_score:
                    best_weapon_score = score
                    best_weapon_in_bag = weapon_item

            # B. Deteksi Kategori Baju Zirah (Armor)
            is_armor = isinstance(item, Armor) or str(getattr(item, "type", "")).lower() == "armor"
            if is_armor:
                armor_item = item
                if not isinstance(item, Armor):
                    stats = item.raw_data.get("stats", {}) or {}
                    armor_item = Armor(
                        id=item.id,
                        name=item.name,
                        type="armor",
                        tier=item.tier,
                        defense=int(stats.get("defense", item.raw_data.get("defense", 5))),
                        raw_data=item.raw_data
                    )
                
                score = EquipStrategy.calculate_armor_score(armor_item)
                if score > best_armor_score:
                    best_armor_score = score
                    best_armor_in_bag = armor_item

        # Prioritas Utama: Pasang senjata terkuat terlebih dahulu untuk meningkatkan daya serang
        if best_weapon_in_bag:
            curr_name = current_weapon.name if current_weapon else "None"
            logger.info(f"[EQUIP] Otomatis memasang senjata: {best_weapon_in_bag.name} menggantikan {curr_name}.")
            return EquipAction(
                item_id=best_weapon_in_bag.id,
                thought=f"Otomatis memakai senjata terkuat di dalam tas ({best_weapon_in_bag.name}) untuk meningkatkan DPS."
            )
            
        # Prioritas Kedua: Pasang zirah tertangguh untuk meningkatkan daya tahan DEF
        if best_armor_in_bag:
            curr_name = current_armor.name if current_armor else "None"
            logger.info(f"[EQUIP] Otomatis memasang zirah: {best_armor_in_bag.name} menggantikan {curr_name}.")
            return EquipAction(
                item_id=best_armor_in_bag.id,
                thought=f"Otomatis memakai zirah terkuat di dalam tas ({best_armor_in_bag.name}) untuk mereduksi damage musuh."
            )

        return None
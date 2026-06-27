"""
src/ai/inventory/equip_strategy.py
Tanggung jawab: Menentukan kelayakan auto-equip senjata dan baju zirah terkuat (Equip Rules).
               Mengevaluasi gain peningkatan status demi efisiensi slot aksi.
"""

import logging
from typing import Optional, Any
from src.models.game_state import GameState
from src.models.action import Action, EquipAction
from src.models.entities import Weapon, Armor
from src.ai.inventory.weapon_strategy import WeaponStrategy

logger = logging.getLogger("ClawRoyale.EquipStrategy")

def _safe_int(val: Any, default: int = 0) -> int:
    try:
        if val is None:
            return default
        return int(val)
    except (ValueError, TypeError):
        return default

class EquipStrategy:
    @staticmethod
    def calculate_armor_score(armor: Optional[Armor]) -> float:
        if not armor:
            return 0.0
        # Formula evaluasi zirah: defense * (1.0 + tier * 0.15)
        return float(armor.defense) * (1.0 + armor.tier * 0.15)

    @staticmethod
    def evaluate_auto_equip(state: GameState) -> Optional[EquipAction]:
        inventory = state.player.inventory
        player = state.player
        
        # 1. PERSIAPAN SKOR TERPASANG SAAT INI
        current_weapon = player.equipped_weapon
        current_weapon_score = WeaponStrategy.calculate_weapon_score(current_weapon)
        best_weapon_score = current_weapon_score
        best_weapon_in_bag: Optional[Weapon] = None
        
        current_armor = player.equipped_armor
        current_armor_score = EquipStrategy.calculate_armor_score(current_armor)
        best_armor_score = current_armor_score
        best_armor_in_bag: Optional[Armor] = None

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
                        damage=_safe_int(stats.get("damage", item.raw_data.get("damage", 15)), 15),
                        range=_safe_int(stats.get("range", item.raw_data.get("range", 1)), 1),
                        ep_cost=_safe_int(stats.get("epCost", item.raw_data.get("ep_cost", 1)), 1),
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
                        defense=_safe_int(stats.get("defense", item.raw_data.get("defense", 5)), 5),
                        raw_data=item.raw_data
                    )
                
                score = EquipStrategy.calculate_armor_score(armor_item)
                if score > best_armor_score:
                    best_armor_score = score
                    best_armor_in_bag = armor_item

        # Bandingkan mana upgrade (Gain) yang dampaknya lebih besar.
        weapon_gain = best_weapon_score - current_weapon_score if best_weapon_in_bag else 0.0
        armor_gain = best_armor_score - current_armor_score if best_armor_in_bag else 0.0

        # [REVISI BARU - PRIORITAS SEHAT]: Jika HP dan EP aman (sehat), utamakan memasang senjata terkuat dahulu dibanding zirah
        is_hp_safe = (player.hp / player.max_hp) > 0.40
        is_ep_safe = player.ep > 3
        if is_hp_safe and is_ep_safe and best_weapon_in_bag:
            weapon_gain += 1000.0 # Dongkrak prioritas di atas zirah

        if best_weapon_in_bag and best_armor_in_bag:
            # Jika ada dua upgrade sekaligus di satu turn, pilih yang efek utilitasnya paling tinggi (atau senjata jika sehat)
            if weapon_gain >= armor_gain:
                curr_name = current_weapon.name if current_weapon else "None"
                logger.info(f"[EQUIP] Otomatis memasang senjata: {best_weapon_in_bag.name} menggantikan {curr_name} (Gain: +{weapon_gain:.1f}).")
                return EquipAction(item_id=best_weapon_in_bag.id, thought=f"Otomatis memakai senjata terkuat di dalam tas ({best_weapon_in_bag.name}).")
            else:
                curr_name = current_armor.name if current_armor else "None"
                logger.info(f"[EQUIP] Otomatis memasang zirah: {best_armor_in_bag.name} menggantikan {curr_name} (Gain: +{armor_gain:.1f}).")
                return EquipAction(item_id=best_armor_in_bag.id, thought=f"Otomatis memakai zirah terkuat di dalam tas ({best_armor_in_bag.name}).")
        
        elif best_weapon_in_bag:
            curr_name = current_weapon.name if current_weapon else "None"
            logger.info(f"[EQUIP] Otomatis memasang senjata: {best_weapon_in_bag.name} menggantikan {curr_name}.")
            return EquipAction(item_id=best_weapon_in_bag.id, thought=f"Otomatis memakai senjata terkuat di dalam tas ({best_weapon_in_bag.name}).")
        
        elif best_armor_in_bag:
            curr_name = current_armor.name if current_armor else "None"
            logger.info(f"[EQUIP] Otomatis memasang zirah: {best_armor_in_bag.name} menggantikan {curr_name}.")
            return EquipAction(item_id=best_armor_in_bag.id, thought=f"Otomatis memakai zirah terkuat di dalam tas ({best_armor_in_bag.name}).")

        return None
"""
src/ai/inventory/equip_strategy.py
Tanggung jawab: Mengotomatiskan pemasangan (equip) senjata DAN baju zirah terbaik dari tas.
Dilengkapi fitur Fail-Safe Dynamic Upcaster dan pemilihan prioritas rasional berdasarkan Gain terbesar.
"""

import logging
from typing import Optional, Any
from src.models.game_state import GameState
from src.models.entities import Weapon, Armor
from src.models.action import EquipAction
from src.ai.inventory.weapon_strategy import WeaponStrategy

logger = logging.getLogger("ClawRoyale.EquipStrategy")

def _safe_int(val: Any, default: int) -> int:
    """Helper fail-safe untuk menangani JSON value yang kotor / bukan angka."""
    try:
        if val is None: return default
        return int(float(val))
    except (ValueError, TypeError):
        return default

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
        
        # 1. PERSIAPAN SKOR TERPASANG SAAT INI
        current_weapon = state.player.equipped_weapon
        current_weapon_score = WeaponStrategy.calculate_weapon_score(current_weapon)
        best_weapon_score = current_weapon_score
        best_weapon_in_bag: Optional[Weapon] = None
        
        current_armor = state.player.equipped_armor
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

        # [REVISI AUDIT]: Jangan paksakan return weapon di awal! 
        # Bandingkan mana upgrade (Gain) yang dampaknya lebih besar.
        weapon_gain = best_weapon_score - current_weapon_score if best_weapon_in_bag else 0.0
        armor_gain = best_armor_score - current_armor_score if best_armor_in_bag else 0.0

        if best_weapon_in_bag and best_armor_in_bag:
            # Jika ada dua upgrade sekaligus di satu turn, pilih yang efek utilitasnya paling tinggi
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
"""
src/ai/inventory/loot_strategy.py
Tanggung jawab: Menganalisis ketersediaan item di wilayah tanah saat ini,
 menentukan kelayakan pungut (Pickup Rules) berdasarkan slot tas tersedia,
 dan memprioritaskan item berharga taktis tinggi.
"""

import logging
from typing import Optional, Tuple
from src.models.game_state import GameState
from src.models.action import PickupAction
from src.models.entities import Weapon, Armor, Potion
from src.config.constants import MAX_INVENTORY_SLOTS

logger = logging.getLogger("ClawRoyale.LootStrategy")

class LootStrategy:
    @staticmethod
    def evaluate_ground_loot(state: GameState) -> Optional[Tuple[PickupAction, float]]:
        player = state.player
        current_region = state.current_region

        if len(player.inventory) >= MAX_INVENTORY_SLOTS:
            logger.warning("[LOOT] Tas penuh! Mematikan evaluasi looting.")
            return None

        enemies_in_same_region = [e for e in state.visible_enemies if e.region_id == current_region.id and e.is_alive]
        if len(enemies_in_same_region) >= 1:
            logger.warning("[LOOT] Ada musuh aktif di satu region. Menunda looting untuk keamanan.")
            return None

        item_ids_in_bag = {item.id for item in player.inventory}

        best_item = None
        best_score = -1.0

        for item in current_region.items:
            if item.id in item_ids_in_bag:
                continue

            score = 0.0
            
            if isinstance(item, Weapon):
                current_weapon = player.equipped_weapon
                weapons_in_bag = [i for i in player.inventory if isinstance(i, Weapon)]
                
                max_owned_weapon_tier = -1
                if current_weapon:
                    max_owned_weapon_tier = max(max_owned_weapon_tier, current_weapon.tier)
                for w in weapons_in_bag:
                    max_owned_weapon_tier = max(max_owned_weapon_tier, w.tier)
                
                if item.tier <= max_owned_weapon_tier:
                    continue

                if player.equipped_weapon is None:
                    score = 100.0 + (item.tier * 20.0)
                else:
                    score = 20.0 + (item.tier * 10.0)
                    
            elif isinstance(item, Armor):
                current_armor = player.equipped_armor
                armors_in_bag = [i for i in player.inventory if isinstance(i, Armor)]
                
                max_owned_armor_tier = -1
                if current_armor:
                    max_owned_armor_tier = max(max_owned_armor_tier, current_armor.tier)
                for a in armors_in_bag:
                    max_owned_armor_tier = max(max_owned_armor_tier, a.tier)
                
                if item.tier <= max_owned_armor_tier:
                    continue

                if player.equipped_armor is None:
                    score = 90.0 + (item.tier * 20.0)
                else:
                    score = 15.0 + (item.tier * 10.0)
                    
            elif isinstance(item, Potion):
                score = 50.0 + (item.tier * 10.0)
                
            elif "smoltz" in item.name.lower():
                # [REVISI AUDIT]: sMoltz adalah koin mata uang progres berharga tinggi. Beri prioritas 60.0
                score = 60.0

            else:
                score = 5.0

            if score > best_score:
                best_score = score
                best_item = item

        if best_item and best_score > 0:
            return PickupAction(
                item_id=best_item.id,
                thought=f"Memungut {best_item.name} dari tanah karena bernilai taktis tinggi (Skor: {best_score:.1f})."
            ), best_score

        return None
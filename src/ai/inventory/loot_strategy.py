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
                # [REVISI AMAN]: Anti-Duplikat Cerdas. Hanya abaikan jika kita sudah punya senjata dengan NAMA yang sama dan TIER setara/lebih tinggi
                current_weapon = player.equipped_weapon
                weapons_in_bag = [i for i in player.inventory if isinstance(i, Weapon)]
                
                has_better_or_equal_same_weapon = False
                
                if current_weapon and current_weapon.name.lower() == item.name.lower() and current_weapon.tier >= item.tier:
                    has_better_or_equal_same_weapon = True
                    
                for w in weapons_in_bag:
                    if w.name.lower() == item.name.lower() and w.tier >= item.tier:
                        has_better_or_equal_same_weapon = True
                        break
                
                if has_better_or_equal_same_weapon:
                    continue

                if player.equipped_weapon is None:
                    # Senjata saat unarmed (Prioritas Teratas: Rank 1)
                    score = 100.0 + (item.tier * 20.0)
                else:
                    # Senjata baru / tipe lain untuk opsi taktis (Prioritas Tinggi: Rank 2)
                    score = 85.0 + (item.tier * 10.0)
                    
            elif isinstance(item, Armor):
                # [REVISI AMAN]: Anti-Duplikat Cerdas untuk baju zirah
                current_armor = player.equipped_armor
                armors_in_bag = [i for i in player.inventory if isinstance(i, Armor)]
                
                has_better_or_equal_same_armor = False
                
                if current_armor and current_armor.name.lower() == item.name.lower() and current_armor.tier >= item.tier:
                    has_better_or_equal_same_armor = True
                    
                for a in armors_in_bag:
                    if a.name.lower() == item.name.lower() and a.tier >= item.tier:
                        has_better_or_equal_same_armor = True
                        break
                        
                if has_better_or_equal_same_armor:
                    continue

                if player.equipped_armor is None:
                    # Zirah saat telanjang dada (Prioritas Menengah-Tinggi: Rank 3)
                    score = 70.0 + (item.tier * 20.0)
                else:
                    # Zirah upgrade
                    score = 15.0 + (item.tier * 10.0)
                    
            elif isinstance(item, Potion):
                # Ramuan HP/EP (Prioritas Bawah: Rank 5)
                score = 50.0 + (item.tier * 10.0)
                
            elif "smoltz" in item.name.lower():
                # Koin mata uang taktis (Prioritas Menengah: Rank 4)
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
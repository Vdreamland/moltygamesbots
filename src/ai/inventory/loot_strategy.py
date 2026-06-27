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

        enemies_in_same_region = [e for e in state.visible_enemies if e.region_id == current_region.id]
        if len(enemies_in_same_region) >= 1:
            logger.warning("[LOOT] Ada musuh di satu region. Menunda looting untuk keamanan.")
            return None

        # [REVISI AUDIT]: Ambil daftar ID item yang sudah aman ada di dalam tas
        item_ids_in_bag = {item.id for item in player.inventory}

        best_item = None
        best_score = -1.0

        for item in current_region.items:
            # [REVISI AUDIT]: Cegah pengambilan ganda (Ignore item yang sudah masuk tas)
            if item.id in item_ids_in_bag:
                continue

            score = 0.0
            
            if isinstance(item, Weapon):
                if player.equipped_weapon is None:
                    score = 100.0 + (item.tier * 20.0)
                else:
                    score = 20.0 + (item.tier * 10.0)
                    
            elif isinstance(item, Armor):
                if player.equipped_armor is None:
                    score = 90.0 + (item.tier * 20.0)
                else:
                    score = 15.0 + (item.tier * 10.0)
                    
            elif isinstance(item, Potion):
                score = 50.0 + (item.tier * 10.0)
                
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
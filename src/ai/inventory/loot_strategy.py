"""
src/ai/inventory/loot_strategy.py
Tanggung jawab: Menentukan kelayakan memungut barang di tanah (Loot Rules).
               Mencegah kepungan musuh dan menghindari pemungutan barang duplikat tak berguna.
"""

import logging
from typing import List, Tuple
from src.models.game_state import GameState
from src.models.entities import Item, Weapon, Armor, Potion
from src.models.action import Action, PickupAction
from src.config.constants import MAX_INVENTORY_SLOTS

logger = logging.getLogger("ClawRoyale.LootStrategy")

class LootStrategy:
    @staticmethod
    def _is_useless_duplicate(item: Item, inventory: List[Item], player) -> bool:
        """Cegah pengambilan item tipe sama dengan tier yang lebih rendah/setara."""
        if isinstance(item, Potion) or getattr(item, "type", "").lower() == "utility":
            return False

        if isinstance(item, Armor) and player.equipped_armor:
            if player.equipped_armor.name == item.name and player.equipped_armor.tier >= item.tier:
                return True

        if isinstance(item, Weapon) and player.equipped_weapon:
            if player.equipped_weapon.name == item.name and player.equipped_weapon.tier >= item.tier:
                return True

        for inv_item in inventory:
            if inv_item.name == item.name and inv_item.tier >= item.tier:
                return True

        return False

    @staticmethod
    def evaluate_looting(state: GameState) -> List[Tuple[Action, float]]:
        candidates: List[Tuple[Action, float]] = []
        player = state.player
        ground_items = state.current_region.items
        inventory = player.inventory

        # 1. Batas Kapasitas Tas Maksimal
        if len(inventory) >= MAX_INVENTORY_SLOTS:
            return candidates

        # 2. Pengamanan Kepungan Musuh Aktif
        enemies_in_same_region = [e for e in state.visible_enemies if e.region_id == state.current_region.id and e.is_alive]
        if len(enemies_in_same_region) > 0:
            logger.warning("[LOOT] Ada musuh aktif di satu region. Menunda looting untuk keamanan.")
            return candidates

        for item in ground_items:
            # [REVISI BARU - ANTI HOARDING]: Batasi penyimpanan senjata maksimal 2 unit (termasuk yang di-equip)
            total_weapons = (1 if player.equipped_weapon else 0) + len([i for i in inventory if isinstance(i, Weapon)])
            if isinstance(item, Weapon) and total_weapons >= 2:
                logger.debug(f"[LOOT] Melewati senjata {item.name} karena sudah membawa maksimal 2 senjata taktis.")
                continue

            # Cegah duplikasi item tipe sama dengan tier lebih rendah/setara
            if LootStrategy._is_useless_duplicate(item, inventory, player):
                continue

            score = 10.0

            # C. Deteksi & Skor Prioritas Pemungutan
            if isinstance(item, Weapon):
                if player.equipped_weapon is None:
                    score = 100.0 + (item.tier * 20.0) # Prioritas mutlak jika bertangan kosong
                else:
                    score = 85.0 + (item.tier * 15.0)  # Prioritas sedang untuk upgrade senjata
                    
            elif isinstance(item, Armor):
                potions_in_bag = [i for i in inventory if isinstance(i, Potion)]
                
                # [REVISI BARU - PRIORITAS ZIRAH]: Ambil armor jika tidak memakai armor dan masih memiliki ramuan pemulih
                if player.equipped_armor is None and len(potions_in_bag) > 0:
                    score = 110.0 + (item.tier * 20.0) # Melompat ke peringkat teratas
                elif player.equipped_armor is None:
                    score = 70.0 + (item.tier * 15.0)  # Prioritas sedang jika tidak memakai armor
                else:
                    score = 15.0 + (item.tier * 10.0)  # Prioritas rendah untuk upgrade armor
                    
            elif isinstance(item, Potion):
                score = 50.0 + (item.tier * 10.0)
                
            elif getattr(item, "type", "").lower() == "utility":
                score = 60.0
                
            candidates.append((
                PickupAction(
                    item_id=item.id,
                    thought=f"Memungut {item.name} dari tanah karena bernilai taktis tinggi (Skor: {score:.1f})."
                ),
                score
            ))

        return candidates
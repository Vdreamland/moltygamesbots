"""
src/ai/inventory/loot_strategy.py
Tanggung jawab: Menganalisis ground items di region saat ini dan menyaring prioritas loot.
               Mengamankan taktik penjarahan "pemberani tapi minim risiko" dengan hanya
               membatasi loot jika musuh berada di region yang sama.
"""

import logging
from typing import Optional, Tuple
from src.models.game_state import GameState
from src.models.entities import Item, Weapon, Potion
from src.models.action import PickupAction
from src.ai.inventory.weapon_strategy import WeaponStrategy
from src.config.constants import MAX_INVENTORY_SLOTS, HP_RETREAT_THRESHOLD

logger = logging.getLogger("ClawRoyale.LootStrategy")

class LootStrategy:
    @staticmethod
    def evaluate_ground_loot(state: GameState) -> Optional[Tuple[PickupAction, float]]:
        """
        Menyaring barang di tanah pada region aktif dan mengembalikan (PickupAction, skor_barang).
        """
        player = state.player
        ground_items = state.current_region.items

        if not ground_items:
            return None

        # 1. Pengaman Batas Kapasitas Tas (Max 10)
        if len(player.inventory) >= MAX_INVENTORY_SLOTS:
            logger.debug("[LOOT] Diabaikan: Kapasitas tas sudah penuh (10/10).")
            return None

        # ==========================================================================
        # PENGAMAN LOOT MINIM RISIKO (PEMBERANI):
        # Filter hanya musuh yang berada di region yang sama dengan kita.
        # Jika di region kita 0 musuh, kita sangat aman untuk memungut barang.
        # ==========================================================================
        enemies_in_same_region = [e for e in state.visible_enemies if e.region_id == state.current_region.id]
        hp_ratio = player.hp / player.max_hp
        
        # Bot hanya menunda loot jika HP kritis (<25%) ATAU jika ada musuh nyata berdiri satu region dengan kita
        if hp_ratio <= HP_RETREAT_THRESHOLD or len(enemies_in_same_region) >= 1:
            logger.debug("[LOOT] Ditangguhkan: Ada ancaman musuh satu ruangan atau HP kritis.")
            return None

        # Urutan Penilaian Kategori Loot (Loot Priority)
        best_item: Optional[Item] = None
        best_item_score = -1.0

        for item in ground_items:
            score = 0.0
            
            if isinstance(item, Weapon):
                if WeaponStrategy.should_upgrade(player.equipped_weapon, item):
                    score = 100.0 + (item.tier * 10.0)
                else:
                    score = 5.0
                    
            elif isinstance(item, Potion):
                if item.recovery_type == "hp":
                    score = 80.0
                elif item.recovery_type == "ep":
                    score = 70.0
                    
            elif "relic" in item.type or "relic" in item.name.lower():
                score = 50.0
            else:
                score = 20.0

            if score > best_item_score:
                best_item_score = score
                best_item = item

        # Ambil item jika bernilai baik
        if best_item and best_item_score > 10.0:
            logger.info(f"[LOOT] Mengunci penjarahan untuk item: {best_item.name} (Skor Dinamis: {best_item_score:.1f}).")
            action = PickupAction(
                item_id=best_item.id,
                thought=f"Memungut {best_item.name} dari tanah karena bernilai taktis tinggi (Skor: {best_item_score:.1f})."
            )
            return action, best_item_score

        return None
"""
src/ai/movement/zone_strategy.py
Tanggung jawab: Mengelola navigasi taktis terhadap Storm/Death Zone dan Pending Zone.
               Memastikan agen mendeteksi bahaya badai dan mengarahkan evakuasi ke Safe Zone.
"""

import logging
from typing import List, Optional
from src.models.game_state import GameState

logger = logging.getLogger("ClawRoyale.ZoneStrategy")

class ZoneStrategy:
    @staticmethod
    def get_storm_escape_regions(state: GameState) -> List[str]:
        """
        Mencari koneksi region tetangga yang bebas dari Badai Aktif dan Pending Death Zone.
        """
        connections = state.current_region.connections
        pending_dz = state.pending_deathzones
        
        safe_regions: List[str] = []
        pending_safe_regions: List[str] = []

        for r_id in connections:
            # Saring wilayah yang bukan badai aktif dan bukan badai penutupan berikutnya
            is_pending = r_id in pending_dz
            # Catatan: Kita tidak bisa tahu detail region tetangga isDeathZone kecuali dari memory
            # atau jika kita berasumsi region yang tidak ada di list pending/active adalah aman.
            
            if not is_pending:
                safe_regions.append(r_id)
            else:
                pending_safe_regions.append(r_id)

        # Jika ada wilayah yang benar-benar bersih, prioritaskan wilayah tersebut
        if safe_regions:
            return safe_regions
        
        # Jika terpaksa, pilih wilayah pending zone daripada tetap berada di badai aktif saat ini
        return pending_safe_regions

    @staticmethod
    def is_in_danger_zone(state: GameState) -> bool:
        """Memeriksa apakah posisi saat ini terancam oleh badai aktif atau badai penutupan berikutnya"""
        current_region = state.current_region
        if current_region.is_death_zone:
            return True
        if current_region.id in state.pending_deathzones:
            return True
        return False
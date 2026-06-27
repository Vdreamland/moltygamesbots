"""
src/ai/movement/zone_strategy.py
Tanggung jawab: Mengelola klasifikasi zona wilayah (Safe Zone, Pending Death Zone, Active Storm)
               dan mengidentifikasi wilayah pelarian darurat dari badai.
"""

from typing import List
from src.models.game_state import GameState

class ZoneStrategy:
    @staticmethod
    def is_in_danger_zone(state: GameState) -> bool:
        """
        Cek apakah wilayah tempat agen berdiri saat ini berada di dalam badai (Active Storm)
        atau merupakan wilayah pending badai yang akan meledak di turn ini.
        """
        region = state.current_region
        if region.is_death_zone:
            return True
        if region.id in state.pending_deathzones:
            return True
        return False

    @staticmethod
    def get_storm_escape_regions(state: GameState) -> List[str]:
        """
        Mengembalikan daftar ID wilayah tetangga yang aman (BUKAN badai aktif maupun pending).
        """
        connections = state.current_region.connections
        escape_routes = []
        for r_id in connections:
            # [PERBAIKAN]: Hindari pemanggilan state.regions yang tidak ada di GameState.
            # Kita andalkan state.pending_deathzones yang menampung seluruh daftar badai aktif maupun terjadwal.
            if r_id in state.pending_deathzones:
                continue
                
            escape_routes.append(r_id)
        return escape_routes
"""
src/ai/survival/storm_strategy.py
Tanggung jawab: Mengelola keputusan darurat taktis untuk keluar dari storm,
               menghindari pending zone, dan memprioritaskan pergerakan menuju safe zone.
"""

import logging
from typing import Optional, List
from src.models.game_state import GameState
from src.models.action import MoveAction
from src.ai.memory.world_model import WorldModel
from src.ai.movement.path_scoring import PathScoring

logger = logging.getLogger("ClawRoyale.StormStrategy")

class StormStrategy:
    @staticmethod
    def evaluate_storm_evacuation(state: GameState, memory: WorldModel) -> Optional[MoveAction]:
        """
        Mengevaluasi apakah agen terancam oleh badai (Death Zone) aktif saat ini
        atau badai yang akan menutup (Pending Death Zone).
        Mengembalikan MoveAction pelarian menuju wilayah aman dengan skor tertinggi jika terancam.
        """
        current_region = state.current_region
        pending_dz = state.pending_deathzones
        connections = current_region.connections

        # Deteksi status ancaman badai di region aktif saat ini
        is_inside_active_storm = current_region.is_death_zone
        is_inside_pending_storm = current_region.id in pending_dz

        # Jika kita berada di wilayah yang aman, tidak perlu memicu evakuasi badai darurat
        if not is_inside_active_storm and not is_inside_pending_storm:
            return None

        if not connections:
            logger.warning("[STORM STRATEGY] Terperangkap! Tidak ada koneksi wilayah tetangga untuk kabur.")
            return None

        # Identifikasi rute pelarian teraman
        best_safe_region_id: Optional[str] = None
        best_pending_region_id: Optional[str] = None
        
        highest_safe_score = -9999.0
        highest_pending_score = -9999.0

        for r_id in connections:
            # Dapatkan skor jalur komprehensif dari modul PathScoring
            score = PathScoring.score_region(r_id, state, memory)

            # Cek status badai region tetangga
            is_neighbor_pending = r_id in pending_dz

            if not is_neighbor_pending:
                # Prioritas Utama: Region yang benar-benar bersih dari badai aktif & pending
                if score > highest_safe_score:
                    highest_safe_score = score
                    best_safe_region_id = r_id
            else:
                # Prioritas Cadangan: Region pending (lebih baik daripada badai aktif saat ini)
                if score > highest_pending_score:
                    highest_pending_score = score
                    best_pending_region_id = r_id

        # 1. Pilih jalur evakuasi terbaik yang benar-benar aman
        if best_safe_region_id and highest_safe_score > -500.0:
            logger.info(f"[STORM STRATEGY] Menemukan wilayah aman bersih: {best_safe_region_id} (Skor: {highest_safe_score:.1f})")
            return MoveAction(
                region_id=best_safe_region_id,
                thought=f"Evakuasi badai menuju region aman bersih {best_safe_region_id}."
            )

        # 2. Jika tidak ada yang aman bersih, pilih pending zone terbaik sebagai fallback
        if best_pending_region_id and highest_pending_score > -500.0:
            logger.warning(f"[STORM STRATEGY] Hanya menemukan wilayah pending zone: {best_pending_region_id}. Menggunakannya sebagai rute cadangan.")
            return MoveAction(
                region_id=best_pending_region_id,
                thought=f"Mengungsi sementara ke pending zone {best_pending_region_id} daripada bertahan di badai aktif."
            )

        return None
"""
src/ai/movement/exploration_strategy.py
Tanggung jawab: Menjelajah peta secara cerdas, mengidentifikasi area jarang dikunjungi,
               dan menegakkan anti-oscillation (mencegah jalan bolak-balik tak berguna).
"""

import logging
from typing import List, Dict
from src.models.game_state import GameState
from src.ai.memory.world_model import WorldModel

logger = logging.getLogger("ClawRoyale.ExplorationStrategy")

class ExplorationStrategy:
    @staticmethod
    def calculate_exploration_score(region_id: str, memory: WorldModel, current_turn: int) -> float:
        """
        Menghitung bonus eksplorasi untuk wilayah tetangga.
        Semakin jarang atau semakin lama wilayah tersebut ditinggalkan, semakin tinggi nilainya.
        """
        history = memory.visited_regions_history
        if not history:
            return 100.0  # Belum pernah dikunjungi sama sekali

        # Cari berapa kali kita mengunjungi region ini dan kapan terakhir kali
        visit_count = 0
        last_visit_turn = -999
        
        for turn, r_id in history:
            if r_id == region_id:
                visit_count += 1
                last_visit_turn = turn

        # 1. Aturan Anti-Oscillation Mutlak
        # Jika kita baru saja meninggalkan region ini di turn terakhir, berikan penalti besar
        # agar agen tidak bolak-balik monoton tanpa alasan
        turns_since_last_visit = current_turn - last_visit_turn
        
        if turns_since_last_visit == 1:
            return -200.0  # Penalti keras anti-oscillation
        elif turns_since_last_visit == 2:
            return -50.0   # Penalti sedang jika baru 2 turn berlalu

        # 2. Formula Nilai Eksplorasi
        # Semakin lama tidak dikunjungi, skor semakin tinggi
        time_bonus = min(150.0, turns_since_last_visit * 3.0) if visit_count > 0 else 100.0
        # Kurangi skor berdasarkan seberapa sering kita memutari region tersebut
        visit_penalty = visit_count * 15.0

        score = time_bonus - visit_penalty
        return max(-100.0, score)
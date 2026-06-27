"""
src/ai/evaluator.py
Tanggung jawab: Menggabungkan seluruh utilitas taktis, melakukan normalisasi skor,
               dan meranking opsi aksi berdasarkan Expected Value terbesar.
"""

import logging
from typing import Dict, List, Tuple
from src.models.game_state import GameState
from src.ai.memory.world_model import WorldModel
from src.models.action import Action, RestAction

logger = logging.getLogger("ClawRoyale.Evaluator")

class Evaluator:
    def __init__(self):
        # Placeholder instansiasi sub-evaluators yang akan kita buat di fase berikutnya
        self.combat_evaluator = None
        self.movement_evaluator = None
        self.inventory_evaluator = None
        self.survival_evaluator = None

    def inject_sub_evaluators(self, combat, movement, inventory, survival):
        """Menghubungkan instansi sub-evaluator taktis ke evaluator utama"""
        self.combat_evaluator = combat
        self.movement_evaluator = movement
        self.inventory_evaluator = inventory
        self.survival_evaluator = survival

    def evaluate_all_options(self, state: GameState, memory: WorldModel) -> List[Tuple[Action, float]]:
        """
        Mengevaluasi seluruh opsi aksi potensial dan memberikan skor utilitas.
        Menghasilkan list tuple berisi (Action, Skor Utilitas).
        """
        options: List[Tuple[Action, float]] = []

        # 1. Evaluasi Aksi Bertahan Hidup (Heal, Run)
        if self.survival_evaluator:
            options.extend(self.survival_evaluator.evaluate(state, memory))

        # 2. Evaluasi Opsi Serangan (Attack)
        if self.combat_evaluator:
            options.extend(self.combat_evaluator.evaluate(state, memory))

        # 3. Evaluasi Opsi Pergerakan (Move, Explore)
        if self.movement_evaluator:
            options.extend(self.movement_evaluator.evaluate(state, memory))

        # 4. Evaluasi Opsi Penjarahan (Loot, Pickup, Equip)
        if self.inventory_evaluator:
            options.extend(self.inventory_evaluator.evaluate(state, memory))

        # 5. Default Fallback Action: Rest jika tidak ada opsi lain yang bernilai positif
        # Membantu memulihkan EP saat aman
        options.append((RestAction(thought="Tidak ada aksi prioritas tinggi, beristirahat memulihkan EP."), 1.0))

        # Urutkan aksi berdasarkan skor utilitas tertinggi secara menurun
        options.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"[EVALUATOR] Evaluasi Selesai. Total kandidat aksi dievaluasi: {len(options)}")
        return options
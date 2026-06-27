"""
src/ai/planner.py
Tanggung jawab: Mengelola multi-step action, antrian tugas (queue), 
               serta validasi akhir sebelum aksi diteruskan ke network layer.
"""

import logging
import time
from typing import List, Optional, Deque
from collections import deque
from src.models.action import Action

logger = logging.getLogger("ClawRoyale.Planner")

class Planner:
    def __init__(self):
        self.action_queue: Deque[Action] = deque()
        self.last_pop_time: float = 0.0

    def add_actions(self, actions: List[Action]):
        for action in actions:
            self.action_queue.append(action)
        logger.info(f"[PLANNER] Menambahkan {len(actions)} aksi ke queue. Total: {len(self.action_queue)}")

    def get_next_action(self, can_act: bool) -> Optional[Action]:
        if not self.action_queue:
            return None

        current_time = time.time()
        next_action = self.action_queue[0]
        is_free = getattr(next_action, "is_free_action", False)

        # [PENYEMPURNAAN]: Aksi gratis (EP 0 seperti pickup & equip) dibebaskan dari pembatas interval 2.0 detik
        if not is_free and (current_time - self.last_pop_time < 2.0):
            return None

        # [PENYEMPURNAAN]: Aksi gratis diizinkan bypass cooldown can_act agar bisa langsung dipasang pada turn yang sama
        if not can_act and not is_free:
            logger.debug("[PLANNER] Bot dalam cooldown, menahan aksi non-gratis di antrean.")
            return None

        action = self.action_queue.popleft()
        self.last_pop_time = current_time
        logger.info(f"[PLANNER] Mengambil aksi: {type(action).__name__} | Thought: {getattr(action, 'thought', 'None')}")
        return action

    def clear(self, reason: str = ""):
        if reason:
            logger.warning(f"[PLANNER] Queue dibersihkan secara paksa oleh Brain. Alasan: {reason}")
        else:
            logger.warning("[PLANNER] Queue dibersihkan secara paksa oleh Brain.")
        self.action_queue.clear()

    def has_actions(self) -> bool:
        return len(self.action_queue) > 0
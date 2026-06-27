"""
src/ai/planner.py
Tanggung jawab: Mengelola aksi berlapis (multi-step action, queue task, action chaining).
               Contoh: Move -> Pickup -> Equip -> Attack.
"""

import logging
from typing import List, Optional
from src.models.action import Action

logger = logging.getLogger("ClawRoyale.Planner")

class Planner:
    def __init__(self):
        self.action_queue: List[Action] = []

    def queue_action(self, action: Action):
        """Menambahkan aksi ke dalam antrean rencana"""
        self.action_queue.append(action)
        logger.debug(f"[PLANNER] Aksi ditambahkan ke rencana: {action.action_type}")

    def queue_chain(self, actions: List[Action]):
        """Menambahkan rantai aksi sekaligus"""
        for act in actions:
            self.queue_action(act)

    def has_actions(self) -> bool:
        """Memeriksa apakah ada rencana aksi yang tertunda"""
        return len(self.action_queue) > 0

    def get_next_action(self) -> Optional[Action]:
        """Mengambil aksi berikutnya dari antrean"""
        if self.has_actions():
            next_act = self.action_queue.pop(0)
            logger.info(f"[PLANNER] Menjalankan aksi terencana berikutnya: {next_act.action_type}")
            return next_act
        return None

    def clear(self, reason: str = ""):
        """Mengosongkan seluruh antrean rencana (biasanya saat emergency / retreat)"""
        if self.action_queue:
            self.action_queue.clear()
            logger.warning(f"[PLANNER] Rencana aksi DIKOSONGKAN. Alasan: {reason}")
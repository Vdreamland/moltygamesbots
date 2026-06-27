"""
src/ai/planner.py
Tanggung jawab: Mengelola multi-step action, antrian tugas (queue), 
serta validasi akhir sebelum aksi diteruskan ke network layer.
"""

import logging
import time
from typing import List, Optional, Deque
from collections import deque
from src.models.game_state import GameState
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

    def get_next_action(self, state: GameState) -> Optional[Action]:
        if not self.action_queue:
            return None

        # [REVISI ANTI-SPAM]: Kunci mekanis waktu. Dilarang melepaskan aksi > 1 kali per 2.0 detik.
        current_time = time.time()
        if current_time - self.last_pop_time < 2.0:
            return None

        data_payload = getattr(state, "data_payload", {})
        can_act = data_payload.get("canAct")
        if can_act is None:
            can_act = data_payload.get("view", {}).get("canAct")
        if can_act is None:
            can_act = data_payload.get("data", {}).get("canAct")
        if can_act is None:
            can_act = True

        if not can_act:
            next_action = self.action_queue[0]
            if not getattr(next_action, "is_free_action", False):
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

    def has_pending_actions(self) -> bool:
        return len(self.action_queue) > 0
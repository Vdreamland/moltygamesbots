"""
src/ai/action_selector.py
Tanggung jawab: Menguji validitas teknis seluruh kandidat aksi,
               memastikan kepatuhan EP & cooldown region target (mencegah INSUFFICIENT_EP).
               Menggunakan tingkat logging DEBUG untuk mencegah spam pengulangan di konsol.
"""

import logging
import time
from typing import List, Tuple, Optional
from src.models.game_state import GameState
from src.models.action import Action, RestAction
from src.config.constants import (
    EP_COST_MOVE, 
    EP_COST_MOVE_STORM_WATER, 
    EP_COST_EXPLORE, 
    EP_COST_ATTACK,
    WEAPON_EP_COSTS
)

logger = logging.getLogger("ClawRoyale.ActionSelector")

class ActionSelector:
    def __init__(self):
        self.last_action_type: Optional[str] = None

    def validate_and_select(self, candidate_actions: List[Tuple[Action, float]], state: GameState) -> Action:
        current_ep = state.player.ep

        for action, score in candidate_actions:
            if not self._has_sufficient_ep(action, current_ep, state):
                logger.debug(f"[SELECTOR] Aksi {action.action_type} diabaikan karena kekurangan EP atau tidak valid (Sisa EP: {current_ep})")
                continue

            if action.action_type == "attack":
                target_id = action.data.get("targetId")
                enemy_exists = any(e.id == target_id and e.is_alive for e in state.visible_enemies)
                if not enemy_exists:
                    logger.debug(f"[SELECTOR] Serangan ke target {target_id} dibatalkan karena target tidak terdeteksi.")
                    continue

            logger.info(f"[SELECTOR] Memilih aksi final: {action.action_type} (Skor Utilitas: {score:.2f})")
            self.last_action_type = action.action_type
            return action

        logger.warning("[SELECTOR] Menjalankan rest pengaman karena kekurangan EP untuk aksi taktis lainnya.")
        if self.last_action_type == "rest":
            time.sleep(1.0)
        self.last_action_type = "rest"
        return RestAction(thought="Menjalankan rest pengaman karena kekurangan EP untuk aksi taktis lainnya.")

    def _has_sufficient_ep(self, action: Action, current_ep: int, state: GameState) -> bool:
        act_type = action.action_type
        
        # Aksi gratis (EP 0) selalu diizinkan lewat
        if getattr(action, "is_free_action", False):
            return True
        
        # [REVISI EP BUFFER]: Cegah pergerakan dan eksplorasi tidak darurat jika EP kritis (EP <= 2) saat aman.
        enemies_in_same_region = [e for e in state.visible_enemies if e.region_id == state.current_region.id]
        is_emergency = (len(enemies_in_same_region) > 0 or state.current_region.is_death_zone)
        
        if not is_emergency and act_type in ["move", "explore"] and current_ep <= 2:
            logger.debug(f"[SELECTOR] Memblokir aksi non-darurat {act_type} untuk mengamankan cadangan EP (EP: {current_ep}).")
            return False

        if act_type == "move":
            target_region_id = action.data.get("regionId")
            
            is_target_water_or_storm = False
            if state.pending_deathzones:
                for zone in state.pending_deathzones:
                    if isinstance(zone, str):
                        if zone == target_region_id:
                            is_target_water_or_storm = True
                            break
                    elif hasattr(zone, "id"):
                        if zone.id == target_region_id:
                            is_target_water_or_storm = True
                            break
                    elif isinstance(zone, dict):
                        if zone.get("id") == target_region_id:
                            is_target_water_or_storm = True
                            break

            if not is_target_water_or_storm:
                is_target_water_or_storm = (target_region_id and target_region_id.lower().startswith("water"))
            
            if is_target_water_or_storm or state.current_region.is_death_zone:
                return current_ep >= EP_COST_MOVE_STORM_WATER
            
            return current_ep >= EP_COST_MOVE
            
        elif act_type == "explore":
            return current_ep >= EP_COST_EXPLORE
            
        elif act_type == "attack":
            # [REVISI EP SERANGAN DINAMIS]: Tentukan biaya EP berdasarkan senjata aktif
            equipped_weapon = state.player.equipped_weapon
            attack_cost = EP_COST_ATTACK
            if equipped_weapon:
                weapon_name = equipped_weapon.name.lower()
                for key, cost in WEAPON_EP_COSTS.items():
                    if key in weapon_name:
                        attack_cost = cost
                        break
            return current_ep >= attack_cost
            
        elif act_type == "interact":
            # [REVISI INTERACT BADAI]: Blokir keras interact jika berada di dalam Death Zone
            if state.current_region.is_death_zone:
                logger.debug("[SELECTOR] Memblokir aksi interact karena berada di dalam Death Zone.")
                return False
            return True
            
        return True
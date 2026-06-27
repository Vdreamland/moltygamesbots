"""
src/ai/memory/world_model.py
Tanggung jawab: Mengingat region yang dilewati, ground loot, jejak musuh,
               serta mengendalikan batasan aturan:
               - RETREAT MEMORY (Region bahaya selama 5 turn - Rule 13I)
               - NO LOOP RETREAT (Dilarang kembali ke region asal selama 3 turn - Rule 13D)
"""

import logging
from typing import Dict, Any, List, Optional
from src.models.entities import Agent, Weapon
from src.models.game_state import GameState

logger = logging.getLogger("ClawRoyale.WorldModel")

class EnemyTrack:
    def __init__(self, enemy_id: str):
        self.enemy_id = enemy_id
        self.name: str = "Unknown"
        self.last_seen_region_id: str = ""
        self.last_hp: int = 100
        self.equipped_weapon: Optional[Weapon] = None
        self.last_seen_turn: int = -1
        self.predicted_regions: List[str] = []

    def update(self, agent: Agent, region_id: str, turn: int):
        self.name = agent.name
        self.last_seen_region_id = region_id
        self.last_hp = agent.hp
        self.equipped_weapon = agent.equipped_weapon
        self.last_seen_turn = turn
        
        if region_id not in self.predicted_regions:
            self.predicted_regions = [region_id]


class WorldModel:
    def __init__(self):
        self.visited_regions_history: List[tuple[int, str]] = []
        self.enemy_registry: Dict[str, EnemyTrack] = {}
        self.retreat_danger_regions: Dict[str, int] = {}
        self.retreat_exit_history: List[tuple[int, str]] = []
        # [REVISI]: Menyimpan memori barang di tanah per region
        self.known_loot: Dict[str, List[Any]] = {}

    def update(self, state: GameState):
        current_turn = state.turn
        current_region_id = state.current_region.id
        
        self.visited_regions_history.append((current_turn, current_region_id))
        
        # [REVISI]: Otomatis rekam sisa barang di tanah region saat ini ke memori
        self.update_known_loot(current_region_id, state.current_region.items)

        for enemy in state.visible_enemies:
            if enemy.id not in self.enemy_registry:
                self.enemy_registry[enemy.id] = EnemyTrack(enemy.id)
                
            track = self.enemy_registry[enemy.id]
            track.update(enemy, current_region_id, current_turn)
            
            self.retreat_danger_regions[current_region_id] = current_turn
            
        self.cleanup_dead_enemies(state)

    def cleanup_dead_enemies(self, state: GameState):
        alive_enemy_ids = {enemy.id for enemy in state.visible_enemies}
        dead_enemies = [eid for eid in self.enemy_registry if eid not in alive_enemy_ids]
        for eid in dead_enemies:
            del self.enemy_registry[eid]

    def record_retreat_movement(self, from_region_id: str, turn: int):
        self.retreat_exit_history.append((turn, from_region_id))

    def is_region_dangerous_by_enemy_memory(self, region_id: str, current_turn: int) -> bool:
        if region_id in self.retreat_danger_regions:
            turn_danger_occurred = self.retreat_danger_regions[region_id]
            if current_turn - turn_danger_occurred <= 5:
                return True
        return False

    def is_loop_forbidden(self, region_id: str, current_turn: int) -> bool:
        for turn_exit, abandoned_region in reversed(self.retreat_exit_history):
            if current_turn - turn_exit < 3:
                if abandoned_region == region_id:
                    return True
            else:
                break
        return False

    def get_last_known_enemy_position(self, enemy_id: str) -> Optional[str]:
        if enemy_id in self.enemy_registry:
            return self.enemy_registry[enemy_id].last_seen_region_id
        return None

    def update_known_loot(self, region_id: str, items: List[Any]):
        self.known_loot[region_id] = items

    def get_known_loot(self, region_id: str) -> List[Any]:
        return self.known_loot.get(region_id, [])

    def clean_expired_memories(self, current_turn: int):
        expired_danger_keys = [
            region for region, turn in self.retreat_danger_regions.items()
            if current_turn - turn > 5
        ]
        for r_id in expired_danger_keys:
            del self.retreat_danger_regions[r_id]

        if len(self.visited_regions_history) > 100:
            self.visited_regions_history = self.visited_regions_history[-100:]
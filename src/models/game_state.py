"""
src/models/game_state.py
Tanggung jawab: Merekonstruksi payload JSON snapshot mentah ("agent_view") menjadi
               objek GameState Python yang bersih dan siap diolah oleh evaluator AI.
               Mendukung standard "view", "data", serta parsing koordinat presisi "visibleMonsters".
"""

import logging
from typing import Dict, Any, List, Optional
from src.models.entities import Agent, Region, Ruin

logger = logging.getLogger("ClawRoyale.GameState")

class GameState:
    def __init__(self, raw_data: Dict[str, Any]):
        self.raw_data = raw_data
        
        # Parser Sensitif-Format (Mendukung standard "view", "data", maupun Flat)
        if "self" in raw_data:
            self.data_payload = raw_data
        elif "view" in raw_data and isinstance(raw_data["view"], dict) and "self" in raw_data["view"]:
            self.data_payload = raw_data["view"]
        elif "data" in raw_data and isinstance(raw_data["data"], dict) and "self" in raw_data["data"]:
            self.data_payload = raw_data["data"]
        else:
            self.data_payload = raw_data.get("view") or raw_data.get("data") or raw_data
            if not isinstance(self.data_payload, dict) or "self" not in self.data_payload:
                self.data_payload = raw_data

        # Metadata dasar turn dan game
        self.game_id: str = raw_data.get("gameId", self.data_payload.get("gameId", "unknown"))
        self.turn: int = int(raw_data.get("turn", self.data_payload.get("turn", 0)))
        
        # 1. Parsing Karakter Utama (Self)
        self.player: Agent = Agent.from_dict(self.data_payload.get("self", {}))
        
        # 2. Parsing Region Aktif Saat Ini
        self.current_region: Region = Region.from_dict(self.data_payload.get("currentRegion", {}))
        
        # Pastikan region_id agen sinkron dengan current_region
        if self.player and self.current_region:
            self.player.region_id = self.current_region.id

        # 3. Parsing Musuh yang Terlihat (Visible Agents)
        self.visible_enemies: List[Agent] = []
        raw_agents = self.data_payload.get("visibleAgents", []) or []
        for agent_data in raw_agents:
            if agent_data.get("id") == self.player.id:
                continue
            enemy_agent = Agent.from_dict(agent_data)
            enemy_agent.region_id = agent_data.get("regionId", self.current_region.id)
            self.visible_enemies.append(enemy_agent)

        # ==========================================================================
        # SINKRONISASI MONSTER AKTIF: Ambil regionId asli lokasi monster berdiri
        # Mencegah deteksi kepungan palsu dari monster yang berada di luar region kita
        # ==========================================================================
        raw_monsters = self.data_payload.get("visibleMonsters", []) or []
        for monster_data in raw_monsters:
            monster_id = monster_data.get("id", monster_data.get("monsterId", ""))
            monster_name = monster_data.get("name", monster_data.get("type", "Monster"))
            
            # Ambil koordinat asli lokasi monster berada dari pancaran data server
            m_region_id = monster_data.get("regionId", self.current_region.id)
            
            # Bentuk objek Agent representatif khusus untuk Monster
            monster_agent = Agent(
                id=monster_id,
                name=f"{monster_name} #{monster_id[:4]}" if len(monster_id) > 4 else monster_name,
                hp=int(monster_data.get("hp", 0)),
                max_hp=int(monster_data.get("maxHp", 100)),
                ep=0,
                max_ep=100,
                alert_gauge=0,
                alert_active=False,
                equipped_weapon=None,
                inventory=[],
                is_alive=True,
                region_id=m_region_id  # <--- SEKARANG KOORDINAT MONSTER 100% AKURAT
            )
            self.visible_enemies.append(monster_agent)

        # 4. Parsing Reruntuhan yang Terlihat (Visible Ruins)
        self.visible_ruins: List[Ruin] = []
        raw_ruins = self.data_payload.get("visibleRuins", []) or []
        for ruin_data in raw_ruins:
            self.visible_ruins.append(Ruin.from_dict(ruin_data))

        # 5. Parsing Pending Death Zones (Badai Storm yang akan menutup)
        self.pending_deathzones: List[str] = []
        raw_pending = self.data_payload.get("pendingDeathzones", []) or []
        for dz in raw_pending:
            if isinstance(dz, dict):
                dz_id = dz.get("id", dz.get("name", ""))
                if dz_id:
                    self.pending_deathzones.append(dz_id)
            elif isinstance(dz, str):
                self.pending_deathzones.append(dz)

        # 6. Pesan Obrolan Terbaru
        self.recent_messages: List[Dict[str, Any]] = self.data_payload.get("recentMessages", []) or []

    @property
    def is_player_alive(self) -> bool:
        return self.player.is_alive and self.player.hp > 0

    def __repr__(self) -> str:
        return (f"GameState(GameId={self.game_id}, Turn={self.turn}, "
                f"HP={self.player.hp}, EP={self.player.ep}, "
                f"EnemiesVisible={len(self.visible_enemies)}, "
                f"CurrentRegion={self.current_region.name})")
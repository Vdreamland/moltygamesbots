"""
src/network/gui_logger.py
Tanggung jawab: Memformat dan mengalirkan data taktis agen per turn (telemetri)
               ke Web Dashboard lokal, serta mencetak satu baris log informatif di konsol.
"""

import logging
import asyncio
from typing import Optional
from src.models.game_state import GameState
from src.models.action import Action
from src.config.constants import WEB_DASHBOARD_MODE
from src.network.telemetry_server import broadcast_telemetry

logger = logging.getLogger("ClawRoyale.GUILogger")

class GUILogger:
    # Memori peta lokal yang akan dipelajari secara mandiri oleh bot saat bermain
    REGION_MAP = {}

    @staticmethod
    def log_turn(state: GameState, action: Optional[Action], can_act: bool = True):
        player = state.player
        region = state.current_region
        
        # [DYNAMIC LEARNING]: Rekam secara otomatis nama region yang sedang dihuni ke memori belajar bot
        if region and hasattr(region, "id") and hasattr(region, "name"):
            GUILogger.REGION_MAP[region.id] = region.name
            
        # Deteksi status badai
        danger_status = "AMAN" if not region.is_death_zone else "DEATH_ZONE"
        if region.id in state.pending_deathzones:
            danger_status = "PENDING_BADAI"
            
        # Deteksi Kelayakan Taktis & Kematian Agen (GAME OVER VISUALIZATION)
        if not state.is_player_alive:
            act_type = "GAME OVER (DEAD)"
            act_desc = "Disconnecting..."
            thought = '"Agen telah gugur! Menghentikan sesi aktif ini untuk mengantre pada game baru."'
            cooldown_status = "MEMUTUSKAN SOKET (RE-QUEUE)..."
        else:
            if action:
                act_type = action.action_type.upper()
                
                # Terjemahkan UUID target move secara otomatis ke nama atau kode sektor taktis
                if action.action_type == "move":
                    dest_id = action.data.get("regionId", "")
                    dest_name = GUILogger.REGION_MAP.get(dest_id, f"Sektor-{dest_id[:4].upper()}")
                    act_desc = f"{dest_name}"
                else:
                    act_desc = f"{action.data}" if action.data else "None"
                    
                thought = f'"{action.thought}"' if action.thought else "None"
            else:
                act_type = "NONE (COOLDOWN)"
                act_desc = "None"
                thought = '"Sedang menunggu cooldown aksi selesai"'
            cooldown_status = "Menunggu Cooldown (30s)" if not can_act else "SIAP BERTINDAK!"
        
        # Format daftar isi tas
        bag_counts = {}
        eq_weapon_id = player.equipped_weapon.id if player.equipped_weapon else None
        eq_armor_id = player.equipped_armor.id if player.equipped_armor else None
        actual_bag_slots = 0
        
        for item in player.inventory:
            if item.id in [eq_weapon_id, eq_armor_id]:
                continue
            itype = getattr(item, 'item_type', getattr(item, 'type', 'item'))
            key = f"{item.name} ({itype})"
            bag_counts[key] = bag_counts.get(key, 0) + 1
            actual_bag_slots += 1
            
        bag_items_desc = ", ".join([f"{key} x{count}" for key, count in bag_counts.items()]) if bag_counts else "None"

        # Format loot di tanah
        ground_items = getattr(region, "items", [])
        ground_counts = {}
        for item in ground_items:
            itype = getattr(item, 'item_type', getattr(item, 'type', 'item'))
            key = f"{item.name} ({itype})"
            ground_counts[key] = ground_counts.get(key, 0) + 1
        ground_items_desc = ", ".join([f"{key} x{count}" for key, count in ground_counts.items()]) if ground_counts else "None"

        # Terjemahkan UUID koneksi tetangga menjadi Nama Asli jika pernah dikunjungi (Fog of War)
        conn_names = []
        for r_id in region.connections:
            r_name = GUILogger.REGION_MAP.get(r_id, f"Sektor-{r_id[:4].upper()}")
            conn_names.append(r_name)
        connections_desc = ", ".join(conn_names) if conn_names else "None"

        # Format status bahaya alert gauge
        alert_desc = f"{player.alert_gauge}/10"

        # Kalkulasi Detail Radar
        enemies_same_region = sum(1 for e in state.visible_enemies if e.region_id == region.id)
        enemies_outside_region = len(state.visible_enemies) - enemies_same_region

        # --------------------------------======================================
        # [KONSOL LOG SINGKAT - HEADLESS MODE - BARU]
        # --------------------------------======================================
        logger.info(f"[TELEMETRY] [TURN {state.turn:02d}] Lokasi: {region.name} | HP: {player.hp}/{player.max_hp} | EP: {player.ep}/{player.max_ep} | Keputusan: {act_type} -> {act_desc}")

        # ======================================================================
        # [TELEMETRY STREAMING - BARU]
        # ======================================================================
        if WEB_DASHBOARD_MODE:
            telemetry_payload = {
                "turn": state.turn,
                "game_id": state.game_id,
                "location_name": region.name,
                "location_id": region.id,
                "hp": player.hp,
                "max_hp": player.max_hp,
                "ep": player.ep,
                "max_ep": player.max_ep,
                "defense": player.defense,
                "kills": player.kills,
                "weapon": player.equipped_weapon.name if player.equipped_weapon else "None",
                "armor": player.equipped_armor.name if player.equipped_armor else "None",
                "alert_gauge": player.alert_gauge,
                "badai_status": danger_status,
                "bag_items": [
                    {"name": item.name, "type": getattr(item, "item_type", getattr(item, "type", "item")), "tier": item.tier}
                    for item in player.inventory if item.id not in [eq_weapon_id, eq_armor_id]
                ],
                "ground_items": [
                    {"name": item.name, "type": getattr(item, "item_type", getattr(item, "type", "item")), "tier": item.tier}
                    for item in ground_items
                ],
                "connections": [
                    {"id": r_id, "name": GUILogger.REGION_MAP.get(r_id, f"Sektor-{r_id[:4].upper()}")}
                    for r_id in region.connections
                ],
                "decision": act_type,
                "decision_detail": act_desc,
                "thought": thought,
                "cooldown_status": cooldown_status,
                "can_act": can_act
            }
            
            # Kirim secara asinkron ke server telemetri lokal tanpa memblokir perulangan utama
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(broadcast_telemetry(telemetry_payload))
            except Exception:
                pass
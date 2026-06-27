"""
src/network/gui_logger.py
Tanggung jawab: Memformat dan mencetak visualisasi data taktis agen per turn 
               dalam bentuk log bergulir (rolling logs) yang terstruktur, rapi, dan padat angka.
               Mendukung rincian tas, pertahanan DEF (Armor), jumlah Kills, Senjata, dan Zirah terpasang.
               Menerapkan lokalisasi nama region (bukan UUID) untuk keasrian visual.
"""

from typing import Optional
from src.models.game_state import GameState
from src.models.action import Action

class GUILogger:
    # Kamus Static Map ID resmi ClawRoyale untuk visualisasi ramah pengguna (User-Friendly)
    REGION_MAP = {
        "ef525413-e6fe-4943-b128-199c09603cff": "Marina",
        "83d7b447-64ce-428e-aa60-c527dcc162d3": "Checkpoint",
        "4df6862d-3b4d-4a4a-856a-75cd416a6295": "Chapel",
        "bbf7bfbf-8c49-49c1-b44b-639e266bd143": "Docks",
        "f973f976-57e2-4661-a0b3-89229bf47f60": "Downtown",
        "a11e6355-4922-45cd-9367-ba601595b2ba": "Garden",
        "deee8eac-e0cd-4041-8d70-2e55a2de6545": "Pond",
        "1dd589db-c337-4c57-bfd3-b39726b82ef8": "S:Relic",
        "27787ac4-8edf-479a-8771-afcdfa4d54e7": "Alley",
        "0f930c6a-cb8d-4ad8-9ce8-8f8e4fb718ab": "Gym",
        "c8d9a00d-3bd9-4f60-a9e4-12ca53061969": "Observatory",
        "e3082ea1-cbad-456d-a79a-147d4c9b2488": "Hotel",
        "596515c2-f2a6-47fa-b203-297379a5451f": "Dam",
        "72e8a706-96c9-4cb2-b3c1-88031cb8dfaa": "Mall",
        "6f1354e1-5a7f-4158-8517-4c87b79b2cef": "Fort",
        "49731c8a-8fb6-4d30-b863-c893926859b9": "Greenhouse",
        "801a1fbf-1dae-4969-8673-817cb2239bad": "Court"
    }

    @staticmethod
    def log_turn(state: GameState, action: Optional[Action], can_act: bool = True):
        player = state.player
        region = state.current_region
        
        # [DYNAMIC LEARNING]: Rekam secara dinamis nama region yang sedang dihuni agar peta visual semakin kaya
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
                
                # Jika aksinya adalah pergerakan (MOVE), terjemahkan UUID target menjadi Nama Region yang terbaca
                if action.action_type == "move":
                    dest_id = action.data.get("regionId", "")
                    dest_name = GUILogger.REGION_MAP.get(dest_id, f"Unknown ({dest_id[:8]}...)")
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
        bag_items_desc = ", ".join([f"{item.name} ({getattr(item, 'item_type', getattr(item, 'type', 'item'))})" for item in player.inventory]) if player.inventory else "None"

        # Format loot di tanah
        ground_items = getattr(region, "items", [])
        ground_items_desc = ", ".join([f"{item.name} ({getattr(item, 'item_type', getattr(item, 'type', 'item'))})" for item in ground_items]) if ground_items else "None"

        # Menerjemahkan seluruh UUID koneksi tetangga menjadi Nama Asli Region yang User-Friendly
        conn_names = []
        for r_id in region.connections:
            r_name = GUILogger.REGION_MAP.get(r_id, f"Unknown ({r_id[:8]}...)")
            conn_names.append(r_name)
        connections_desc = ", ".join(conn_names) if conn_names else "None"

        # Format status bahaya alert gauge
        alert_desc = f"{player.alert_gauge}/10"

        # Kalkulasi Detail Radar
        enemies_same_region = sum(1 for e in state.visible_enemies if e.region_id == region.id)
        enemies_outside_region = len(state.visible_enemies) - enemies_same_region

        # Cetak blok per turn yang bersih, ringkas, dan mudah di-scroll
        print("\n" + "-"*65)
        print(f"[TURN {state.turn:02d}] Lokasi: {region.name} ({region.id})")
        print("-"*65)
        # SINKRONISASI VISUAL: Menampilkan stats DEF (Armor) dan jumlah KILLS dinamis dari server
        print(f" Stat Fisik : HP: {player.hp}/{player.max_hp} | EP: {player.ep}/{player.max_ep} | Tas: {len(player.inventory)}/10 | DEF: {player.defense} | Kills: {player.kills}")
        print(f" Isi Tas    : {bag_items_desc}")
        print(f" Senjata    : {player.equipped_weapon.name if player.equipped_weapon else 'None'}")
        print(f" Zirah      : {player.equipped_armor.name if player.equipped_armor else 'None'}")
        print(f" Radar      : Musuh Terdeteksi: {len(state.visible_enemies)} (Satu Area: {enemies_same_region} | Luar Area: {enemies_outside_region})")
        print(f" Alert Ruin : {alert_desc}")
        print(f" Loot Tanah : {ground_items_desc}")
        print(f" Koneksi    : {connections_desc}")
        print(f" Badai      : {danger_status}")
        print(f" Keputusan  : {act_type} -> {act_desc}")
        print(f" Alasan AI  : {thought}")
        print(f" Status Act : {cooldown_status}")
        print("-"*65 + "\n")
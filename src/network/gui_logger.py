"""
src/network/gui_logger.py
Tanggung jawab: Memformat dan mencetak visualisasi data taktis agen per turn 
               dalam bentuk log bergulir (rolling logs) yang terstruktur, rapi, dan padat angka.
               Mendukung rincian tas, pertahanan DEF (Armor), jumlah Kills, Senjata, dan Zirah terpasang.
               Menerapkan lokalisasi nama region otomatis (Fog of War) tanpa penginputan manual.
               Kini mendukung pengelompokan item kembar (contoh: Potion x2).
"""

from typing import Optional
from src.models.game_state import GameState
from src.models.action import Action

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
        
        # [PERBAIKAN VISUAL]: Pengelompokan daftar isi tas agar rapi (Contoh: Potion x2)
        bag_counts = {}
        for item in player.inventory:
            itype = getattr(item, 'item_type', getattr(item, 'type', 'item'))
            key = f"{item.name} ({itype})"
            bag_counts[key] = bag_counts.get(key, 0) + 1
        bag_items_desc = ", ".join([f"{key} x{count}" for key, count in bag_counts.items()]) if bag_counts else "None"

        # [PERBAIKAN VISUAL]: Pengelompokan daftar barang di tanah agar rapi
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

        # Cetak blok per turn yang bersih, ringkas, dan mudah di-scroll
        print("\n" + "-"*65)
        print(f"[TURN {state.turn:02d}] Lokasi: {region.name} ({region.id[:8]}...)")
        print("-"*65)
        # SINKRONISASI VISUAL: Menampilkan stats fisik lengkap
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
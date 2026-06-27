"""
src/network/gui_logger.py
Tanggung jawab: Memformat dan mencetak visualisasi data taktis agen per turn 
               dalam bentuk log bergulir (rolling logs) yang terstruktur, rapi, dan padat angka.
               Mendukung rincian tas, pertahanan DEF (Armor), jumlah Kills, Senjata, dan Zirah terpasang.
               Kini dilengkapi rincian Loot Tanah, Koneksi Wilayah, dan status Reruntuhan.
"""

from typing import Optional
from src.models.game_state import GameState
from src.models.action import Action

class GUILogger:
    @staticmethod
    def log_turn(state: GameState, action: Optional[Action], can_act: bool = True):
        player = state.player
        region = state.current_region
        
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
                act_desc = f"{action.data}" if action.data else "None"
                thought = f'"{action.thought}"' if action.thought else "None"
            else:
                act_type = "NONE (COOLDOWN)"
                act_desc = "None"
                thought = '"Sedang menunggu cooldown aksi selesai"'
            cooldown_status = "Menunggu Cooldown (30s)" if not can_act else "SIAP BERTINDAK!"
        
        # Format daftar isi tas (Inventory)
        bag_items_desc = ", ".join([f"{item.name} ({getattr(item, 'item_type', getattr(item, 'type', 'item'))})" for item in player.inventory]) if player.inventory else "None"

        # [BARU]: Format daftar barang di tanah (Ground Loot) di region saat ini
        ground_items = getattr(region, "items", [])
        ground_items_desc = ", ".join([f"{item.name} ({getattr(item, 'item_type', getattr(item, 'type', 'item'))})" for item in ground_items]) if ground_items else "None"

        # [BARU]: Format daftar koneksi region tetangga yang bisa dituju
        connections_desc = ", ".join(region.connections) if region.connections else "None"

        # [BARU]: Format status Reruntuhan (Ruin) & Gauge Alert Guardian lokal
        ruin_gauge = getattr(region, "ruin_gauge", 0)
        ruin_status = "Tidak Ada" if ruin_gauge == 0 else f"Progress: {ruin_gauge}% (Guardian Alert: {getattr(player, 'alert_gauge', 0)}/10)"

        # Kalkulasi Detail Radar
        enemies_same_region = sum(1 for e in state.visible_enemies if e.region_id == region.id)
        enemies_outside_region = len(state.visible_enemies) - enemies_same_region

        # Cetak blok per turn yang bersih, ringkas, dan sangat informatif
        print("\n" + "-"*65)
        print(f"[TURN {state.turn:02d}] Lokasi: {region.name} ({region.id})")
        print("-"*65)
        # SINKRONISASI VISUAL: Menampilkan stats fisik lengkap
        print(f" Stat Fisik : HP: {player.hp}/{player.max_hp} | EP: {player.ep}/{player.max_ep} | Tas: {len(player.inventory)}/10 | DEF: {player.defense} | Kills: {player.kills}")
        print(f" Isi Tas    : {bag_items_desc}")
        # BARIS DETAIL BARU: Deteksi loot tanah, koneksi jalan keluar, dan status ruin
        print(f" Loot Tanah : {ground_items_desc}")
        print(f" Koneksi    : {connections_desc}")
        print(f" Reruntuhan : {ruin_status}")
        print(f" Senjata    : {player.equipped_weapon.name if player.equipped_weapon else 'None'}")
        print(f" Zirah      : {player.equipped_armor.name if player.equipped_armor else 'None'}")
        print(f" Radar      : Musuh Terdeteksi: {len(state.visible_enemies)} (Satu Area: {enemies_same_region} | Luar Area: {enemies_outside_region})")
        print(f" Badai      : {danger_status}")
        print(f" Keputusan  : {act_type} -> {act_desc}")
        print(f" Alasan AI  : {thought}")
        print(f" Status Act : {cooldown_status}")
        print("-"*65 + "\n")
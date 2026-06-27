"""
src/network/frame_processor.py
Tanggung jawab: Memproses, mendekode, dan merutekan pesan/frame masuk dari WebSocket
               (Game State, Welcome, Action Result, can_act_changed, dll).
"""

import asyncio
import json
import logging
import time
import traceback
from typing import Any
from src.models.game_state import GameState
from src.network.gui_logger import GUILogger

logger = logging.getLogger("ClawRoyale.FrameProcessor")

class FrameProcessor:
    def __init__(self, client: Any):
        self.client = client
        self.brain = client.brain
        self._last_turn_dead = None
        self._last_state = None 
        self._last_action_turn = -1 
        self._last_dead_game_id = None 
        self._game_over_logged = False # Mencegah spam cetakan box Game Over raksasa

    async def process_message(self, message: str):
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            logger.error("[WS] Gagal mendekode JSON frame masuk.")
            return

        # --- PENYEMPURNAAN FILTER GAME STATE ---
        is_game_state = False
        if isinstance(payload, dict):
            frame_type = str(payload.get("type", "")).lower()
            
            # Jika tipe frame adalah kontrol resmi, dipastikan BUKAN game state (mencegah TURN 00)
            if frame_type in [
                "can_act_changed", "action_result", "error", "welcome", 
                "game_ended", "game_settled", "chat", "whisper", "talk", 
                "broadcast", "ping", "pong"
            ]:
                is_game_state = False
            else:
                # Fallback pencarian objek utama "self" untuk kompatibilitas hibrida
                if "self" in payload:
                    is_game_state = True
                elif "view" in payload and isinstance(payload["view"], dict) and "self" in payload["view"]:
                    is_game_state = True
                elif "data" in payload and isinstance(payload["data"], dict) and "self" in payload["data"]:
                    is_game_state = True
                elif frame_type in ["agent_view", "state_update", "game_state"]:
                    is_game_state = True
        # ----------------------------------------

        if is_game_state:
            state = GameState(payload)
            self._last_state = state # Simpan snapshot state aktif ke memori sasis
            game_status = payload.get("status", "running")
            
            # --- PENANGANAN GAME SELESAI / GUGUR ---
            if game_status == "finished":
                if not self.client._finished_flag_logged:
                    logger.info("\n=== PERTANDINGAN SELESAI (STATUS: FINISHED) ===")
                    logger.info("[WS] Meninggalkan ruangan. Bersiap mencari antrean game baru...")
                    self.client._finished_flag_logged = True
                    
                self.brain.planner.clear(reason="Game Finished")
                
                from src.network.websocket import is_ws_closed
                if self.client.websocket and not is_ws_closed(self.client.websocket):
                    asyncio.create_task(self.client.websocket.close())
                return
            
            if not state.is_player_alive:
                self.brain.planner.clear(reason="Agent Gugur (HP 0)")
                
                # 1. Cetak Kotak Raksasa GAME OVER tepat SEKALI saja sepanjang sisa pertandingan
                if not self._game_over_logged:
                    try:
                        GUILogger.log_turn(state, None, getattr(self.client, 'can_act', True))
                    except Exception as e:
                        logger.error(f"[GUI ERROR] Terjadi kerusakan pada gui_logger:\n{traceback.format_exc()}")
                    self._game_over_logged = True
                    self._last_turn_dead = state.turn

                # 2. Jika kita dirutekan kembali ke game yang SAMA tempat kita baru saja gugur,
                # jangan putuskan koneksi lagi (standby) agar tidak memicu pemblokiran IP (Error 4003).
                if self._last_dead_game_id == state.game_id:
                    if not self.client._dead_flag_logged:
                        logger.info("[WS] Masih terikat Match Lock server. Standby menunggu Match ini selesai dari sisi server...")
                        self.client._dead_flag_logged = True
                    
                    # Cetak baris tunggal pendek setiap kali turn bertambah untuk menggantikan spam box raksasa
                    if not self._last_turn_dead == state.turn:
                        logger.info(f"[WS] Sesi Standby - Menunggu pertandingan selesai dari sisi server... (Turn {state.turn:02d})")
                        self._last_turn_dead = state.turn
                    return

                # Jika ini adalah kematian pertama di game ini, catat ID game dan langsung tutup soket agar auto-reconnect mencari game baru
                self._last_dead_game_id = state.game_id
                logger.info("[WS] Agen GUGUR (HP 0). Mencoba keluar dan mengantre langsung ke game baru...")
                
                from src.network.websocket import is_ws_closed
                if self.client.websocket and not is_ws_closed(self.client.websocket):
                    asyncio.create_task(self.client.websocket.close())
                return
            # ----------------------------------------------
            
            action = self.brain.think(state)
            
            try:
                GUILogger.log_turn(state, action, getattr(self.client, 'can_act', True))
            except Exception as e:
                logger.error(f"[GUI ERROR] Terjadi kerusakan pada src/network/gui_logger.py:\n{traceback.format_exc()}")

            if action:
                # Catat turn aktif saat ini agar tidak terjadi double-action di turn yang sama
                self._last_action_turn = state.turn
                await self.client.send_action(action)
            return

        frame_type = payload.get("type", "").lower() if isinstance(payload, dict) else ""

        if frame_type == "error":
            code = payload.get("code", "UNKNOWN")
            msg = payload.get("message", "Terjadi kesalahan")
            logger.error(f"[WS ERROR] Dari server: {code} - {msg}")
            
            # Jika server mengembalikan error Rate Limit dalam bentuk payload
            if "limit exceeded" in msg.lower() or code == 4003:
                self.client._force_long_cooldown = True
            return
            
        elif frame_type == "action_result":
            # Parsing flat frame asinkron
            data_dict = payload.get("data", {}) if isinstance(payload.get("data"), dict) else {}
            success = payload.get("success", data_dict.get("success", True))
            reason = payload.get("reason", data_dict.get("reason", "None"))
            cd_rem = payload.get("cooldownRemainingMs", data_dict.get("cooldownRemainingMs"))
            self.client.can_act = payload.get("canAct", payload.get("can_act", data_dict.get("canAct", True)))
            
            if cd_rem is not None:
                self.brain.local_cooldown_end = time.time() + (float(cd_rem) / 1000.0)
                
            if not success:
                logger.error(f"[WS SERVER_ACK] GAGAL: {reason}")
                self.brain.planner.clear(reason=f"Server Reject ({reason})")
            else:
                logger.info("[WS SERVER_ACK] Aksi BERHASIL diproses server.")
            return

        elif frame_type == "can_act_changed":
            can_act = payload.get("canAct", payload.get("can_act", True))
            self.client.can_act = can_act
            if can_act:
                self.brain.local_cooldown_end = time.time()
                logger.info("[WS] Cooldown selesai. Agen SIAP BERTINDAK!")
                
                # [PERBAIKAN SINKRONISASI]: Hanya re-think jika turn ini BELUM PERNAH diambil keputusan aksi taktis
                if self._last_state is not None:
                    state = self._last_state
                    if state.is_player_alive and state.turn != getattr(self, "_last_action_turn", -1):
                        action = self.brain.think(state)
                        try:
                            # Cetak pembaruan log visual dengan keputusan terbaru
                            GUILogger.log_turn(state, action, True)
                        except Exception:
                            pass
                        if action:
                            self._last_action_turn = state.turn
                            await self.client.send_action(action)
            return
            
        elif frame_type == "game_ended":
            logger.info("\n=== PERTANDINGAN SELESAI (GAME_ENDED FRAME) ===")
            self.brain.planner.clear(reason="Game Ended")
            from src.network.websocket import is_ws_closed
            if self.client.websocket and not is_ws_closed(self.client.websocket):
                asyncio.create_task(self.client.websocket.close())
            return
            
        elif frame_type == "game_settled":
            logger.info("[WS] Settlement data diterima. Pertandingan sepenuhnya ditutup oleh server.")
            return

        elif frame_type in ["chat", "whisper", "talk", "broadcast"]:
            sender = payload.get("sender", "Unknown")
            content = payload.get("message", "")
            logger.info(f"\n[WS RECEIVE {frame_type.upper()}] Dari: {sender} | Pesan: '{content}'\n")
            return

        elif frame_type == "welcome":
            # Ekstrak pesan welcome
            welcome_msg = payload.get("message", "")
            if not welcome_msg:
                data_val = payload.get("data")
                if isinstance(data_val, str):
                    welcome_msg = data_val
                elif isinstance(data_val, dict):
                    welcome_msg = data_val.get("entryType", "")
            
            decision = payload.get("decision", "")
            logger.info(f"[WS JOIN] Welcome Frame: {welcome_msg}")
            
            welcome_lower = str(welcome_msg).lower()
            decision_lower = str(decision).lower()
            
            # Jika terdeteksi game aktif, cukup re-sync (tidak perlu hello)
            if "active game found" in welcome_lower or "already" in welcome_lower or decision_lower == "already_in_game":
                logger.info("[WS JOIN] Agen terdeteksi di game yang masih berjalan. Melakukan Re-sync...")
            else:
                # Untuk welcome lainnya, kirim hello frame untuk masuk antrean matchmaking
                self._last_dead_game_id = None # Reset memori kematian karena kita resmi memasuki antrean game baru
                join_payload = {
                    "type": "hello",
                    "entryType": "free"
                }
                await self.client.websocket.send(json.dumps(join_payload))
                logger.info("[WS JOIN] Mengirim Hello Frame. Memilih tipe ruangan: free. Memasuki Antrean Matchmaking...")
            return
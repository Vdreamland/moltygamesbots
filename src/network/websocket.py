"""
src/network/websocket.py
Tanggung jawab: Menangani koneksi WebSocket terpadu, pemrosesan frame masuk,
               ping/pong keepalive, auto-reconnect, pengamanan soket (Safe-Filter),
               serta menampilkan GUI Player Stats ke konsol.
"""

import asyncio
import json
import logging
import time
import traceback
import websockets
from typing import Optional, Any
from src.models.game_state import GameState
from src.ai.brain import Brain
from src.network.gui_logger import GUILogger
from src.config.constants import (
    WS_BASE_URL, API_KEY, PING_INTERVAL_SECONDS, 
    WS_TIMEOUT_SECONDS, MAX_CONNECTION_RETRIES, RECONNECT_DELAY_SECONDS
)

logger = logging.getLogger("ClawRoyale.WebSocket")

def is_ws_closed(ws: Any) -> bool:
    if ws is None:
        return True
    if hasattr(ws, "state"):
        state_str = str(ws.state).upper()
        return "CLOSED" in state_str or "CLOSING" in state_str
    return getattr(ws, "closed", False)

class ClawRoyaleWSClient:
    def __init__(self, api_client: Any = None, brain: Optional[Brain] = None):
        self.api_client = api_client
        self.brain = brain if brain is not None else Brain()
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_running = False
        self.reconnect_attempts = 0
        self._dead_flag_logged = False
        self._finished_flag_logged = False

    async def connect_and_loop(self):
        self.is_running = True
        uri = f"{WS_BASE_URL}/join"
        
        api_key_active = API_KEY
        x_version = "1.0.0"
        
        if self.api_client and hasattr(self.api_client, "session"):
            api_key_active = self.api_client.session.headers.get("X-API-Key", API_KEY)
            x_version = self.api_client.session.headers.get("X-Version", "1.0.0")

        headers = {
            "X-API-Key": api_key_active,
            "X-Version": x_version
        }

        connect_kwargs = {}
        try:
            import websockets.asyncio.client
            connect_kwargs["additional_headers"] = headers
        except ImportError:
            connect_kwargs["extra_headers"] = headers

        while self.is_running:
            try:
                logger.info(f"[WS] Menghubungkan ke: {uri}")
                async with websockets.connect(
                    uri, 
                    open_timeout=WS_TIMEOUT_SECONDS, 
                    **connect_kwargs
                ) as websocket:
                    self.websocket = websocket
                    self.reconnect_attempts = 0
                    self._dead_flag_logged = False
                    self._finished_flag_logged = False
                    logger.info("[WS] Koneksi terbuka murni. Menunggu Welcome Frame...")
                    
                    ping_task = asyncio.create_task(self._send_ping_loop())
                    
                    try:
                        async for message in websocket:
                            await self._handle_incoming_frame(message)
                    except websockets.exceptions.ConnectionClosed as e:
                        # Menambahkan logger code & reason agar mudah melacak alasan proxy memutus soket
                        logger.warning(f"[WS] Soket terputus secara mendadak dari sisi server. (Code: {e.code}, Reason: {e.reason})")
                    finally:
                        ping_task.cancel()
                        
            except Exception as e:
                logger.error(f"[WS] Gagal terhubung ke server: {str(e)}")
                
            if not self.is_running:
                break
                
            self.reconnect_attempts += 1
            if self.reconnect_attempts > MAX_CONNECTION_RETRIES:
                logger.error("[WS] Batas maksimal reconnect terlampaui. Menghentikan proses.")
                break
                
            # DYNAMIC BACKOFF: Perpanjang waktu delay jika terjadi diskoneksi terus-menerus 
            # untuk memberi waktu pada cache proxy server membersihkan Match lama yang sudah usai.
            delay = RECONNECT_DELAY_SECONDS
            if self.reconnect_attempts > 2:
                delay = min(30, int(RECONNECT_DELAY_SECONDS * self.reconnect_attempts))
                
            logger.info(f"[WS] Mencoba menyambungkan kembali dalam {delay} detik...")
            await asyncio.sleep(delay)

    async def _handle_incoming_frame(self, message: str):
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            logger.error("[WS] Gagal mendekode JSON frame masuk.")
            return

        is_game_state = False
        if isinstance(payload, dict):
            if "self" in payload:
                is_game_state = True
            elif "view" in payload and isinstance(payload["view"], dict) and "self" in payload["view"]:
                is_game_state = True
            elif "data" in payload and isinstance(payload["data"], dict) and "self" in payload["data"]:
                is_game_state = True

        if is_game_state:
            state = GameState(payload)
            
            # --- PENANGANAN GAME SELESAI / GUGUR ---
            game_status = payload.get("status", "running")
            
            if game_status == "finished":
                if not self._finished_flag_logged:
                    logger.info("\n=== PERTANDINGAN SELESAI (STATUS: FINISHED) ===")
                    logger.info("[WS] Meninggalkan ruangan. Bersiap mencari antrean game baru...")
                    self._finished_flag_logged = True
                    
                self.brain.planner.clear(reason="Game Finished")
                
                if self.websocket and not is_ws_closed(self.websocket):
                    asyncio.create_task(self.websocket.close())
                return
            
            if not state.is_player_alive:
                self.brain.planner.clear(reason="Agent Gugur (HP 0)")
                
                if not getattr(self, '_last_turn_dead', None) == state.turn:
                    try:
                        GUILogger.log_turn(state, None, getattr(self, 'can_act', True))
                    except Exception as e:
                        logger.error(f"[GUI ERROR] Terjadi kerusakan pada gui_logger:\n{traceback.format_exc()}")
                    self._last_turn_dead = state.turn
                
                if not self._dead_flag_logged:
                    logger.info("[WS] Agen GUGUR. Standby di dalam room menunggu server menyelesaikan Match ini...")
                    self._dead_flag_logged = True
                
                return
            # ----------------------------------------------
            
            action = self.brain.think(state)
            
            try:
                GUILogger.log_turn(state, action, getattr(self, 'can_act', True))
            except Exception as e:
                logger.error(f"[GUI ERROR] Terjadi kerusakan pada src/network/gui_logger.py:\n{traceback.format_exc()}")

            if action:
                await self.send_action(action)
            return

        frame_type = payload.get("type", "").lower() if isinstance(payload, dict) else ""

        # Mencegat pesan Error & Game Ended khusus dari server
        if frame_type == "error":
            code = payload.get("code", "UNKNOWN")
            msg = payload.get("message", "Terjadi kesalahan")
            logger.error(f"[WS ERROR] Dari server: {code} - {msg}")
            return
            
        elif frame_type == "game_ended":
            logger.info("\n=== PERTANDINGAN SELESAI (GAME_ENDED FRAME) ===")
            self.brain.planner.clear(reason="Game Ended")
            if self.websocket and not is_ws_closed(self.websocket):
                asyncio.create_task(self.websocket.close())
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
            welcome_msg = ""
            data_val = payload.get("data")
            if isinstance(data_val, str):
                welcome_msg = data_val
            elif isinstance(data_val, dict):
                welcome_msg = data_val.get("entryType", "")
            else:
                welcome_msg = payload.get("message", "")

            decision = payload.get("decision", "")
            logger.info(f"[WS JOIN] Welcome Frame: {welcome_msg}")
            
            welcome_lower = welcome_msg.lower()
            decision_lower = decision.lower()
            
            if "ask_entry_type" in welcome_lower or "choose entrytype" in welcome_lower or "both free and paid" in welcome_lower or decision_lower == "ask_entry_type":
                join_payload = {
                    "type": "hello",
                    "entryType": "free"
                }
                await self.websocket.send(json.dumps(join_payload))
                logger.info("[WS JOIN] Mengirim Hello Frame. Memilih tipe ruangan: free. Memasuki Antrean Matchmaking...")
            elif "active game found" in welcome_lower or welcome_msg == "ALREADY_IN_GAME" or decision_lower == "already_in_game":
                logger.info("[WS JOIN] Agen terdeteksi di game yang masih berjalan. Melakukan Re-sync...")
            return

        elif frame_type == "action_result":
            data_block = payload.get("data", {})
            success = data_block.get("success", False)
            reason = data_block.get("reason", "None")
            cd_rem = data_block.get("cooldownRemainingMs")
            
            if cd_rem is not None:
                self.brain.local_cooldown_end = time.time() + (cd_rem / 1000.0)
                
            if not success:
                logger.error(f"[WS SERVER_ACK] GAGAL: {reason}")
                self.brain.planner.clear(reason=f"Server Reject ({reason})")
            else:
                logger.info("[WS SERVER_ACK] Aksi BERHASIL diproses server.")
            return

    async def send_action(self, action):
        if not self.websocket or is_ws_closed(self.websocket):
            logger.error("[WS] Gagal mengirim aksi: Koneksi soket ditutup.")
            return

        payload = {
            "type": "action",
            "data": {
                "type": action.action_type,
                **action.data
            },
            "thought": getattr(action, "thought", "")
        }
        
        try:
            await self.websocket.send(json.dumps(payload))
            logger.info(f"[WS SEND] Mengirim aksi: {action.action_type}")
            
            if action.action_type not in ["pickup", "equip", "talk"]:
                self.brain.local_cooldown_end = time.time() + 30.0
                
        except Exception as e:
            logger.error(f"[WS SEND] Gagal mengirim payload aksi: {str(e)}")

    async def _send_ping_loop(self):
        while self.is_running:
            await asyncio.sleep(PING_INTERVAL_SECONDS)
            if self.websocket and not is_ws_closed(self.websocket):
                try:
                    # Menerapkan JSON ping payload resmi agar server proxy tidak salah mendeteksi inactivity
                    await self.websocket.send(json.dumps({"type": "ping"}))
                except Exception:
                    break

    def stop(self):
        self.is_running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())
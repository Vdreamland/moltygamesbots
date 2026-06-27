"""
src/network/websocket.py
Tanggung jawab: Menangani koneksi WebSocket terpadu, inisialisasi jaringan,
               ping/pong keepalive, auto-reconnect, pengamanan soket (Safe-Filter).
"""

import asyncio
import json
import logging
import time
import websockets
from typing import Optional, Any
from src.ai.brain import Brain
from src.network.frame_processor import FrameProcessor
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
        self._force_long_cooldown = False
        self.can_act = True 
        
        # Inisialisasi delegasi pemrosesan frame
        self.processor = FrameProcessor(self)

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
                self._force_long_cooldown = False
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
                    
                    # [BARU - RESET MEMORI GAME BARU]: Bersihkan sisa ingatan/turn game lama dari processor
                    self.processor._last_state = None
                    self.processor._last_turn_dead = None
                    self.processor._game_over_logged = False
                    
                    logger.info("[WS] Koneksi terbuka murni. Menunggu Welcome Frame...")
                    
                    ping_task = asyncio.create_task(self._send_ping_loop())
                    
                    try:
                        async for message in websocket:
                            await self.processor.process_message(message)
                    except websockets.exceptions.ConnectionClosed as e:
                        logger.warning(f"[WS] Soket terputus dari sisi server. (Code: {e.code}, Reason: {e.reason})")
                        
                        # PENANGANAN RATE LIMIT (Code 4003)
                        if e.code == 4003 or "ip agent limit" in str(e.reason).lower():
                            logger.error("[WS RATE LIMIT] Terdeteksi pembatasan IP/Agent dari server (Phantom Socket).")
                            self._force_long_cooldown = True
                            
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
                
            # PENJADWALAN DELAY (BACKOFF)
            if self._force_long_cooldown:
                delay = 60  # Wajib tunggu 60 detik agar server mematikan sesi lama
                logger.info(f"[WS RATE LIMIT] Menunda koneksi selama {delay} detik untuk menghindari pemblokiran permanen...")
            else:
                delay = RECONNECT_DELAY_SECONDS
                if self.reconnect_attempts > 2:
                    delay = min(30, int(RECONNECT_DELAY_SECONDS * self.reconnect_attempts))
                logger.info(f"[WS] Mencoba menyambungkan kembali dalam {delay} detik...")
                
            await asyncio.sleep(delay)

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
                    await self.websocket.send(json.dumps({"type": "ping"}))
                except Exception:
                    break

    def stop(self):
        self.is_running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())
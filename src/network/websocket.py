"""
src/network/websocket.py
Tanggung jawab: Menangani koneksi WebSocket terpadu, pemrosesan frame masuk,
               ping/pong keepalive, auto-reconnect, dan pengamanan soket (Safe-Filter).
"""

import asyncio
import json
import logging
import websockets
from typing import Optional, Any
from src.models.game_state import GameState
from src.ai.brain import Brain
from src.config.constants import (
    WS_BASE_URL, API_KEY, PING_INTERVAL_SECONDS, 
    WS_TIMEOUT_SECONDS, MAX_CONNECTION_RETRIES, RECONNECT_DELAY_SECONDS
)

logger = logging.getLogger("ClawRoyale.WebSocket")

class ClawRoyaleWSClient:
    def __init__(self, api_client: Any = None, brain: Optional[Brain] = None):
        self.api_client = api_client
        self.brain = brain if brain is not None else Brain()
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_running = False
        self.reconnect_attempts = 0

    async def connect_and_loop(self):
        self.is_running = True
        uri = f"{WS_BASE_URL}/join"
        
        api_key_active = API_KEY
        if self.api_client and hasattr(self.api_client, "session"):
            api_key_active = self.api_client.session.headers.get("X-API-Key", API_KEY)

        headers = {
            "X-API-Key": api_key_active
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
                    logger.info("[WS] Koneksi terbuka murni. Menunggu Welcome Frame...")
                    
                    ping_task = asyncio.create_task(self._send_ping_loop())
                    
                    try:
                        async for message in websocket:
                            await self._handle_incoming_frame(message)
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("[WS] Soket terputus secara mendadak dari sisi server.")
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
                
            logger.info(f"[WS] Mencoba menyambungkan kembali dalam {RECONNECT_DELAY_SECONDS} detik...")
            await asyncio.sleep(RECONNECT_DELAY_SECONDS)

    async def _handle_incoming_frame(self, message: str):
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            logger.error("[WS] Gagal mendekode JSON frame masuk.")
            return

        # [REVISI INTEGRAL]: Deteksi Game State Utama berdasarkan keberadaan 'player' di root level JSON
        if isinstance(payload, dict) and "player" in payload:
            state = GameState(payload)
            action = self.brain.think(state)
            if action:
                await self.send_action(action)
            return

        frame_type = payload.get("type", "").lower() if isinstance(payload, dict) else ""

        if frame_type in ["chat", "whisper"]:
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

            logger.info(f"[WS JOIN] Welcome Frame: {welcome_msg}")
            
            if welcome_msg == "ASK_ENTRY_TYPE":
                join_payload = {
                    "type": "entry_type",
                    "data": "free_room"
                }
                await self.websocket.send(json.dumps(join_payload))
                logger.info("[WS JOIN] Memasuki Antrean Matchmaking (Free Room)...")
            elif "active game found" in welcome_msg.lower() or welcome_msg == "ALREADY_IN_GAME":
                logger.info("[WS JOIN] Agen berada di dalam game aktif. Menunggu Game State...")
            return

        elif frame_type == "action_result":
            success = payload.get("data", {}).get("success", False)
            reason = payload.get("data", {}).get("reason", "None")
            if not success:
                logger.error(f"[WS SERVER_ACK] GAGAL: {reason}")
            else:
                logger.info("[WS SERVER_ACK] Aksi BERHASIL diproses server.")
            return

    async def send_action(self, action):
        if not self.websocket or self.websocket.closed:
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
        except Exception as e:
            logger.error(f"[WS SEND] Gagal mengirim payload aksi: {str(e)}")

    async def _send_ping_loop(self):
        while self.is_running:
            await asyncio.sleep(PING_INTERVAL_SECONDS)
            if self.websocket and not self.websocket.closed:
                try:
                    await self.websocket.ping()
                except Exception:
                    break

    def stop(self):
        self.is_running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())
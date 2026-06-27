"""
src/network/websocket.py
Tanggung jawab: Mengelola koneksi asinkron Unified Join WebSocket (/ws/join), 
               mengirim jabat tangan (hello) matchmaking, auto-reconnection,
               keepalive pings berkala, dan penanganan state transisi gameplay.
               Mengamankan sinkronisasi turn_advanced dan canAct pasca eksekusi aksi.
"""

import asyncio
import json
import logging
import sys
import websockets
from typing import Optional, Dict, Any

from src.config.constants import (
    WS_BASE_URL, API_KEY, PING_INTERVAL_SECONDS, 
    MAX_WS_MESSAGES_PER_MINUTE, WS_THROTTLE_DELAY
)
from src.network.api import ClawRoyaleAPIClient
from src.models.game_state import GameState
from src.ai.brain import Brain
from src.network.gui_logger import GUILogger

logger = logging.getLogger("ClawRoyale.WebSocket")

# Diamkan logger background lain agar tidak mengotori log taktis Anda
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class ClawRoyaleWSClient:
    def __init__(self, api_client: ClawRoyaleAPIClient, brain: Brain):
        self.api_client = api_client
        self.brain = brain
        self.ws_url = f"{WS_BASE_URL.rstrip('/')}/join"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        
        # State kontrol asinkron
        self.message_semaphore = asyncio.Semaphore(1)
        self.is_running = False
        self.can_act = False  # Default False saat baru menyambung (mencegah COOLDOWN_ACTIVE)
        self.last_state: Optional[GameState] = None

    async def connect_and_loop(self):
        """Memulai loop asinkron koneksi WebSocket dan auto-reconnection"""
        self.is_running = True
        retry_delay = 5

        while self.is_running:
            try:
                version = self.api_client.fetch_server_version()
                if not version:
                    logger.error("Gagal mengambil versi API dari REST. Reconnecting...")
                    await asyncio.sleep(retry_delay)
                    continue

                headers = {
                    "X-API-Key": API_KEY,
                    "X-Version": version
                }

                logger.info(f"Menghubungkan ke Unified Join WebSocket: {self.ws_url}")
                # Kompatibilitas websockets v13+: Menggunakan additional_headers
                async with websockets.connect(self.ws_url, additional_headers=headers) as websocket:
                    self.websocket = websocket
                    logger.info("Koneksi WebSocket Terbuka. Menunggu Welcome Frame...")
                    
                    # Jalankan sub-task pengiriman ping secara pararel
                    ping_task = asyncio.create_task(self._send_pings_loop())
                    
                    try:
                        # Alur iterasi standar asinkron yang 100% stabil & aman
                        async for message in websocket:
                            await self._handle_incoming_frame(message)
                    except websockets.exceptions.ConnectionClosed as cc:
                        logger.warning(f"Koneksi WebSocket ditutup oleh server (Code: {cc.code}).")
                    finally:
                        ping_task.cancel()
                        
            except Exception as e:
                logger.error(f"Error pada loop WebSocket: {e}", exc_info=True)
                
            if self.is_running:
                logger.info(f"Mencoba menyambungkan / mengantre kembali dalam {retry_delay} detik...")
                await asyncio.sleep(retry_delay)

    async def _send_pings_loop(self):
        """Mengirimkan frame ping taktis berkala setiap 15 detik demi menjaga keaktifan soket"""
        while True:
            try:
                await asyncio.sleep(PING_INTERVAL_SECONDS)
                # Kompatibilitas websockets v13+: Periksa apakah status state bernilai OPEN
                if self.websocket and getattr(self.websocket, "state", None) and self.websocket.state.name == "OPEN":
                    await self._send_frame({"type": "ping"})
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Gagal mengirim keepalive ping: {e}")

    async def _handle_incoming_frame(self, raw_message: str):
        """Menganalisis frame data masuk dari server"""
        try:
            payload = json.loads(raw_message)
            event_type = payload.get("type")
            
            # 1. Alur Jabat Tangan Unified Join
            if event_type == "welcome":
                decision = payload.get("decision")
                logger.info(f"[WS JOIN] Welcome Frame: {decision}")
                if decision != "ALREADY_IN_GAME":
                    await self._send_frame({"type": "hello", "entryType": "free"})
                    logger.info("[WS JOIN] Memasuki Antrean Matchmaking (Free Room)...")
            
            elif event_type == "assigned":
                logger.info(f"=== [WS] PERTANDINGAN BARU DIMULAI! GameId: {payload.get('gameId')} ===")
                # KOREKSI 1: Game baru dimulai, agen bebas cooldown dan berhak bertindak langsung di Turn 1
                self.can_act = True
                self.last_state = None

            # 2. Konfirmasi Eksekusi Aksi dari Server
            elif event_type == "action_result":
                success = payload.get("success", False)
                error_msg = payload.get("error", "")
                action_data = payload.get("action", {})
                act_type = action_data.get("type", "Unknown")
                
                # Ambil canAct secara dinamis dari root maupun data
                data_payload = payload.get("data", {}) if isinstance(payload.get("data"), dict) else {}
                can_act_val = payload.get("canAct", data_payload.get("canAct"))
                
                if can_act_val is not None:
                    self.can_act = bool(can_act_val)
                
                if success:
                    logger.info(f"[WS SERVER_ACK] Aksi '{act_type}' BERHASIL diproses server. (canAct: {self.can_act})")
                else:
                    logger.error(f"[WS SERVER_ACK] Aksi '{act_type}' GAGAL: {error_msg}")

                # Dual-Trigger Instan: Hanya jalankan jika aksi BERHASIL (mencegah loop spam pada aksi gagal)
                if success and self.can_act and self.last_state and self.last_state.is_player_alive:
                    self.can_act = False
                    action = self.brain.think(self.last_state)
                    GUILogger.log_turn(self.last_state, action, can_act=False)
                    await self._send_frame(action.to_json())

            # 3. Transisi Gameplay Real-time
            elif event_type == "agent_view":
                state = GameState(payload)
                self.last_state = state
                
                if state.is_player_alive:
                    if self.can_act:
                        self.can_act = False
                        action = self.brain.think(state)
                        GUILogger.log_turn(state, action, can_act=False)
                        await self._send_frame(action.to_json())
                    else:
                        GUILogger.log_turn(state, None, can_act=False)
                else:
                    GUILogger.log_turn(state, None, can_act=False)
                    logger.warning("[WS] Agen dinyatakan telah gugur! Memutuskan koneksi untuk mengantre game baru...")
                    await self.websocket.close(code=1000, reason="Agent died, auto-requeue")
                    return

            # 4. Transisi Pergantian Turn Baru (Turn Advanced)
            elif event_type == "turn_advanced":
                state = GameState(payload)
                self.last_state = state
                self.can_act = True  # Force True saat turn baru
                
                if state.is_player_alive:
                    self.can_act = False
                    action = self.brain.think(state)
                    GUILogger.log_turn(state, action, can_act=False)
                    await self._send_frame(action.to_json())
                else:
                    GUILogger.log_turn(state, None, can_act=False)
                    logger.warning("[WS] Agen dinyatakan telah gugur! Memutuskan koneksi untuk mengantre game baru...")
                    await self.websocket.close(code=1000, reason="Agent died, auto-requeue")
                    return
                    
            elif event_type == "can_act_changed":
                can_act = payload.get("data", {}).get("canAct", False)
                if can_act:
                    # KOREKSI 2: Setel can_act True terlebih dahulu sebelum meluncurkan tindakan pengunci
                    self.can_act = True
                    if self.last_state and self.last_state.is_player_alive:
                        self.can_act = False
                        action = self.brain.think(self.last_state)
                        GUILogger.log_turn(self.last_state, action, can_act=False)
                        await self._send_frame(action.to_json())
                else:
                    self.can_act = False
                
            # ==========================================================================
            # 5. PENANGKAPAN REAL-TIME EVENT (Serangan Musuh, Serigala, Cuaca, dll)
            # Dilengkapi parser struktural defensif jika server mengirim objek data
            # ==========================================================================
            elif event_type == "event":
                event_name = payload.get("event", "game_event")
                data_payload = payload.get("data", {}) or {}
                msg = payload.get("message", data_payload.get("message"))
                
                if msg:
                    logger.info(f"[GAME EVENT] {msg}")
                else:
                    # Jalankan parser asinkron struktural
                    if event_name == "combat":
                        attacker = data_payload.get("attackerName", data_payload.get("attackerId", "Seseorang"))
                        target = data_payload.get("targetName", data_payload.get("targetId", "Target"))
                        damage = data_payload.get("damage", 0)
                        logger.info(f"[GAME EVENT] {attacker} menyerang {target} sebesar {damage} HP damage.")
                        
                    elif event_name == "movement":
                        subject = data_payload.get("subjectName", data_payload.get("subjectId", "Seseorang"))
                        destination = data_payload.get("destinationName", data_payload.get("destinationId", "wilayah baru"))
                        logger.info(f"[GAME EVENT] {subject} berpindah ke {destination}.")
                        
                    else:
                        logger.info(f"[GAME EVENT] Kejadian {event_name}: {data_payload}")

            elif event_type == "game_ended":
                logger.info("=== [WS] GAME ENDED: Pertandingan Selesai! ===")
                self.last_state = None
                
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.error(f"Kesalahan memproses frame masuk: {e}", exc_info=True)

    async def _send_frame(self, payload: Dict[str, Any]):
        """Mengirimkan frame asinkron dengan throttler penjaga rate-limit"""
        if not self.websocket or not getattr(self.websocket, "state", None) or self.websocket.state.name != "OPEN":
            return

        async with self.message_semaphore:
            try:
                raw_data = json.dumps(payload)
                await self.websocket.send(raw_data)
                await asyncio.sleep(WS_THROTTLE_DELAY)
            except Exception as e:
                logger.error(f"Gagal mengirim frame JSON ke server: {e}")

    def stop(self):
        self.is_running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())
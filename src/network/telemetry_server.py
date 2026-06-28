"""
src/network/telemetry_server.py
Tanggung jawab: Menjalankan server WebSocket lokal ringan (port 8000) di latar belakang
               untuk menyalurkan data taktis agen (telemetri) ke Dashboard Web GUI.
"""

import asyncio
import json
import logging
import websockets
from typing import Set, Any

logger = logging.getLogger("ClawRoyale.TelemetryServer")

# Set penampung seluruh koneksi browser aktif
connected_clients: Set[Any] = set()
server_instance = None

async def handler(websocket):
    # Daftarkan browser client baru
    connected_clients.add(websocket)
    logger.info(f"[TELEMETRY] Dashboard Web terhubung! (Total Client: {len(connected_clients)})")
    try:
        async for _ in websocket:
            # Kita hanya menerima satu arah (bot -> dashboard).
            # Hiraukan jika ada pesan masuk dari dashboard.
            pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
        logger.info(f"[TELEMETRY] Dashboard Web terputus. (Sisa Client: {len(connected_clients)})")

async def start_telemetry_server(port: int = 8000):
    global server_instance
    try:
        # Menjalankan WebSocket Server lokal
        async with websockets.serve(handler, "127.0.0.1", port) as server:
            server_instance = server
            await asyncio.Future()  # Menjaga server tetap berjalan terus-menerus
    except Exception as e:
        logger.error(f"[TELEMETRY ERROR] Gagal menjalankan Server Telemetri: {str(e)}")

async def broadcast_telemetry(data: dict):
    """Memancarkan data taktis JSON ke seluruh browser dashboard yang terhubung."""
    if not connected_clients:
        return
    
    payload = json.dumps(data)
    # Gunakan asyncio.gather untuk memancarkan ke semua client secara asinkron
    await asyncio.gather(
        *[client.send(payload) for client in connected_clients],
        return_exceptions=True
    )
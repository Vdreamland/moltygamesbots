"""
run.py
Tanggung jawab: Berkas peluncur utama sistem. Menangani handshake versi,
               verifikasi profil, inisialisasi server telemetri lokal, 
               dan menjalankan perulangan taktis WebSocket.
"""

import asyncio
import os
import sys
import logging
from src.network.api import ClawRoyaleAPIClient
from src.network.websocket import ClawRoyaleWSClient

# Setup Logger Utama (Mematikan spam logs perantara agar terminal asri)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ClawRoyale.Runner")

# Matikan spam log dari pustaka pihak ketiga websockets
logging.getLogger("websockets").setLevel(logging.WARNING)

async def main():
    logger.info("=== CLAWROYALE AGENT INITIALIZATION ===")
    
    # 1. Melakukan Verifikasi Handshake Versi API ke Server
    api_client = ClawRoyaleAPIClient()
    logger.info("Mengambil informasi versi server aktif...")
    version_success = await api_client.handshake()
    if not version_success:
        logger.error("Gagal melakukan handshake versi ke server. Menghentikan program.")
        sys.exit(1)
        
    # 2. Verifikasi Profil Agen
    logger.info("Memulai verifikasi profil agen ke server...")
    profile = await api_client.get_profile()
    if not profile:
        logger.error("Gagal melakukan verifikasi profil agen. Menghentikan program.")
        sys.exit(1)
        
    logger.info(f"Profil Terverifikasi. Nama Agen: {profile.get('name', 'Unknown')}")
    
    # 3. [BARU] Inisialisasi Server Telemetri Lokal untuk Web Dashboard
    from src.config.constants import WEB_DASHBOARD_MODE, TELEMETRY_PORT
    if WEB_DASHBOARD_MODE:
        from src.network.telemetry_server import start_telemetry_server
        asyncio.create_task(start_telemetry_server(port=TELEMETRY_PORT))
    
    # 4. Meluncurkan Sesi Pertempuran WebSocket Utama
    ws_client = ClawRoyaleWSClient(api_client=api_client)
    await ws_client.connect_and_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program dihentikan oleh pengguna secara aman.")
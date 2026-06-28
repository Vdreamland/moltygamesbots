"""
run.py
Tanggung jawab: Berkas peluncur utama sistem. Menangani handshake versi,
               verifikasi profil, inisialisasi server telemetri lokal, 
               dan menjalankan perulangan taktis WebSocket.
               Telah disempurnakan untuk membisukan seluruh spam log di PowerShell.
"""

import asyncio
import os
import sys
import logging
from src.network.api import ClawRoyaleAPIClient
from src.network.websocket import ClawRoyaleWSClient

# 1. Set Log Level Global ke WARNING untuk membisukan seluruh spam taktis di PowerShell/CMD
logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# 2. Pertahankan hanya logger Runner & Telemetry pada level INFO khusus untuk fase start-up
runner_logger = logging.getLogger("ClawRoyale.Runner")
runner_logger.setLevel(logging.INFO)

telemetry_logger = logging.getLogger("ClawRoyale.TelemetryServer")
telemetry_logger.setLevel(logging.INFO)

async def main():
    runner_logger.info("=== CLAWROYALE AGENT INITIALIZATION ===")
    
    # Melakukan Verifikasi Handshake Versi API ke Server
    api_client = ClawRoyaleAPIClient()
    runner_logger.info("Mengambil informasi versi server aktif...")
    version_success = await api_client.handshake()
    if not version_success:
        runner_logger.error("Gagal melakukan handshake versi ke server. Menghentikan program.")
        sys.exit(1)
        
    # Verifikasi Profil Agen
    runner_logger.info("Memulai verifikasi profil agen ke server...")
    profile = await api_client.get_profile()
    if not profile:
        runner_logger.error("Gagal melakukan verifikasi profil agen. Menghentikan program.")
        sys.exit(1)
        
    runner_logger.info(f"Profil Terverifikasi. Nama Agen: {profile.get('name', 'Unknown')}")
    
    # Inisialisasi Server Telemetri Lokal untuk Web Dashboard
    from src.config.constants import WEB_DASHBOARD_MODE, TELEMETRY_PORT
    if WEB_DASHBOARD_MODE:
        from src.network.telemetry_server import start_telemetry_server
        asyncio.create_task(start_telemetry_server(port=TELEMETRY_PORT))
        
        # Berikan jeda milidetik agar server siap
        await asyncio.sleep(0.5)
        telemetry_logger.info("[TELEMETRY] Server Telemetri Lokal SIAP! Silakan buka file 'dashboard/index.html' di browser Anda.")
    
    # 3. BISUKAN MUTLAK: Turunkan level logger start-up ke WARNING agar terminal 100% diam selama game berlangsung
    runner_logger.setLevel(logging.WARNING)
    telemetry_logger.setLevel(logging.WARNING)
    
    # Meluncurkan Sesi Pertempuran WebSocket Utama
    ws_client = ClawRoyaleWSClient(api_client=api_client)
    await ws_client.connect_and_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
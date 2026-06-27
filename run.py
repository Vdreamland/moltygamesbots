"""
run.py
Tanggung jawab: Berkas peluncur utama (entry point) aplikasi.
               Menginisialisasi modul REST API, mengorkestrasi event loop,
               dan menjalankan AI Agent WebSocket dengan mematikan spam log perantara.
"""

import asyncio
import logging
import os
import sys

# Tambahkan direktori root ke path agar modul internal terbaca dengan baik
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Memuat berkas .env secara otomatis di awal eksekusi program
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.network.api import ClawRoyaleAPIClient
from src.ai.brain import Brain
from src.network.websocket import ClawRoyaleWSClient
from src.config.constants import API_KEY

# 1. Konfigurasi Sistem Logging Terpusat
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ClawRoyale.Runner")

# ==============================================================================
# PEMBUNGKAM SPAM LOG PERANTARA (Membatasi output agar terminal bersih & rapi)
# ==============================================================================
logging.getLogger("ClawRoyale.Brain").setLevel(logging.WARNING)
logging.getLogger("ClawRoyale.TargetSelector").setLevel(logging.WARNING)
logging.getLogger("ClawRoyale.RetreatStrategy").setLevel(logging.WARNING)
logging.getLogger("ClawRoyale.CombatEvaluator").setLevel(logging.WARNING)
logging.getLogger("ClawRoyale.Evaluator").setLevel(logging.WARNING)
logging.getLogger("ClawRoyale.GoalSelector").setLevel(logging.WARNING)
logging.getLogger("ClawRoyale.ActionSelector").setLevel(logging.WARNING)
logging.getLogger("ClawRoyale.LootStrategy").setLevel(logging.WARNING)
logging.getLogger("ClawRoyale.EquipStrategy").setLevel(logging.WARNING)
logging.getLogger("ClawRoyale.ConsumableStrategy").setLevel(logging.WARNING)
logging.getLogger("ClawRoyale.DangerCalculator").setLevel(logging.WARNING)
logging.getLogger("ClawRoyale.SurvivalEvaluator").setLevel(logging.WARNING)
logging.getLogger("ClawRoyale.MovementEvaluator").setLevel(logging.WARNING)
logging.getLogger("ClawRoyale.PathScoring").setLevel(logging.WARNING)

def bootstrap():
    """Menginisialisasi validitas sistem sebelum diluncurkan"""
    logger.info("=== CLAWROYALE AGENT INITIALIZATION ===")
    
    # Ambil API KEY setelah .env dimuat
    api_key_active = os.getenv("CLAWROYALE_API_KEY", API_KEY)
    
    # Validasi API Key
    if not api_key_active:
        logger.critical(
            "CRITICAL: Kunci API (API_KEY) tidak terdeteksi pada berkas .env maupun environment variable!\n"
            "Silakan buat berkas .env di folder yang sama dengan run.py dan isi:\n"
            "CLAWROYALE_API_KEY=mr_live_xxx..."
        )
        sys.exit(1)

    # 2. Inisialisasi Klien API
    api_client = ClawRoyaleAPIClient()
    api_client.session.headers.update({"X-API-Key": api_key_active})

    # Ambil versi server aktif
    logger.info("Mengambil informasi versi server aktif...")
    version = api_client.fetch_server_version()
    if not version:
        logger.critical("Gagal mengambil versi server aktif. Menutup inisialisasi.")
        sys.exit(1)

    # Verifikasi Profil Agen
    logger.info("Memulai verifikasi profil agen ke server...")
    profile = api_client.get_profile()
    if profile:
        logger.info(f"Profil Terverifikasi. Nama Agen: {profile.get('name', 'Unknown')}")
    else:
        logger.warning("Gagal memverifikasi profil melalui REST API. Mencoba melanjutkan langsung ke WebSocket...")

    # 4. Inisialisasi AI Brain & WebSocket
    brain = Brain()
    ws_client = ClawRoyaleWSClient(api_client, brain)

    # 5. Jalankan Event Loop Asinkron untuk WebSocket Gameplay
    try:
        asyncio.run(ws_client.connect_and_loop())
    except KeyboardInterrupt:
        logger.info("Aplikasi dihentikan secara manual oleh pengguna (KeyboardInterrupt).")
        ws_client.stop()
    except Exception as e:
        logger.critical(f"Aplikasi terhenti karena kesalahan fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    bootstrap()
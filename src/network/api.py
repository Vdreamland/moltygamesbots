"""
src/network/api.py
Tanggung jawab: Mengelola handshake versi API ke server (GET /api/version),
               mengecek kredensial profil (GET /api/profile),
               dan memelihara HTTP session asinkronus (aiohttp).
"""

import logging
import aiohttp
from typing import Optional, Dict, Any
from src.config.constants import BASE_URL, API_KEY

logger = logging.getLogger("ClawRoyale.API")

class ClawRoyaleAPIClient:
    def __init__(self):
        # Inisialisasi headers dasar untuk autentikasi dan handshake versi
        self.headers = {
            "X-API-Key": API_KEY,
            "X-Version": "1.0.0"
        }
        # Memelihara HTTP session asinkronus secara persisten
        self.session = aiohttp.ClientSession(headers=self.headers)

    async def handshake(self) -> bool:
        """
        Melakukan handshake verifikasi versi ke server (GET /api/version)
        dan memperbarui header X-Version secara dinamis.
        """
        url = f"{BASE_URL}/version"
        logger.info("Melakukan verifikasi handshake versi ke server...")
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    version = data.get("version", "1.0.0")
                    
                    # Sinkronisasikan versi asinkron ke headers
                    self.headers["X-Version"] = version
                    self.session.headers["X-Version"] = version
                    logger.info(f"Handshake Sukses. Versi Server Aktif: {version}")
                    return True
                else:
                    logger.error(f"Handshake Gagal. HTTP Status: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Gagal melakukan koneksi handshake ke server: {str(e)}")
            return False

    async def get_profile(self) -> Optional[Dict[str, Any]]:
        """
        Mengambil detail profil agen (GET /api/profile) untuk verifikasi API Key.
        """
        url = f"{BASE_URL}/profile"
        try:
            # Pastikan API Key terpasang kuat di header sebelum menembak
            self.session.headers["X-API-Key"] = API_KEY
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    # Kembalikan payload data profil aslinya
                    profile_data = data.get("data", data)
                    return profile_data
                elif response.status == 401:
                    logger.error("Verifikasi Gagal: API Key tidak valid / Unauthorized (HTTP 401).")
                    return None
                else:
                    logger.error(f"Gagal memverifikasi profil. HTTP Status: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Gagal menghubungi server untuk verifikasi profil: {str(e)}")
            return None

    async def close(self):
        """Menutup HTTP session secara aman sebelum menghentikan proses."""
        if self.session and not self.session.closed:
            await self.session.close()
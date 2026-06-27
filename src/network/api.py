"""
src/network/api.py
Tanggung jawab: Klien REST API untuk autentikasi, pengecekan versi server, profil akun,
               dan registrasi/loadout game.
Jangan berisi: Logika keputusan AI atau kalkulasi strategi.
"""

import logging
import requests
from typing import Dict, Any, Optional
from src.config.constants import BASE_URL, API_KEY

logger = logging.getLogger("ClawRoyale.API")

class ClawRoyaleAPIClient:
    def __init__(self):
        self.base_url = BASE_URL.rstrip("/")
        self.api_key = API_KEY
        self.version: Optional[str] = None
        self.session = requests.Session()
        
        # Siapkan header autentikasi bawaan
        if self.api_key:
            self.session.headers.update({"X-API-Key": self.api_key})
        else:
            logger.warning("Peringatan: API Key tidak ditemukan pada env variabel CLAWROYALE_API_KEY")

    def fetch_server_version(self) -> Optional[str]:
        """
        Mengambil versi server saat ini untuk mencegah error 426 VERSION_MISMATCH.
        Menyimpannya ke session headers sebagai 'X-Version'.
        """
        url = f"{self.base_url}/version"
        try:
            logger.info("Melakukan verifikasi handshake versi ke server...")
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.version = data.get("version")
                if self.version:
                    self.session.headers.update({"X-Version": self.version})
                    logger.info(f"Handshake Sukses. Versi Server Aktif: {self.version}")
                    return self.version
            
            logger.error(f"Gagal mengambil versi server. HTTP Status: {response.status_code}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Gagal melakukan request versi server karena masalah koneksi: {e}")
            return None

    def get_profile(self) -> Optional[Dict[str, Any]]:
        """
        Mendapatkan data profil agen aktif saat ini.
        """
        url = f"{self.base_url}/accounts/me"
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.error("Akses Ditolak (401): API Key tidak valid.")
            else:
                logger.error(f"Gagal mengambil profil akun. Status: {response.status_code}, Msg: {response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Gagal memanggil API profil: {e}")
            return None

    def get_loadout(self) -> Optional[Dict[str, Any]]:
        """
        Mendapatkan pengaturan konfigurasi loadout bawaan agen.
        """
        url = f"{self.base_url}/api/loadout"
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            logger.error(f"Gagal mengambil data loadout. Status: {response.status_code}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Gagal memanggil API loadout: {e}")
            return None
"""
src/ai/combat/attack_strategy.py
Tanggung jawab: Menentukan kelayakan menyerang (Attack Rules).
               Menerapkan audit keberanian pembunuh oportunis (Finish-Kill Instinct):
               Tetap izinkan serangan tangan kosong untuk eksekusi finisher (HP <= 5)
               di region yang sama demi merebut senjata jarahan mereka.
"""

import logging
from src.models.game_state import GameState
from src.models.entities import Agent
from src.config.constants import HP_RETREAT_THRESHOLD, EP_MIN_RESERVE
from src.ai.combat.win_probability import WinProbabilityCalculator

logger = logging.getLogger("ClawRoyale.AttackStrategy")

class AttackStrategy:
    @staticmethod
    def should_attack(state: GameState, target: Agent) -> bool:
        player = state.player

        # ==========================================================================
        # BYPASS FINISHER TANGAN KOSONG:
        # Jika tidak memegang senjata, tetapi target sangat sekarat (HP <= 5) 
        # satu ruangan, loloskan pengecekan karena kita bisa membunuhnya dengan 1 pukulan!
        # ==========================================================================
        is_unarmed_finisher = (
            player.equipped_weapon is None and 
            target.hp <= 5 and 
            target.region_id == state.current_region.id
        )

        # 1. Validasi Kepemilikan Senjata (Dengan Pengecualian Finisher)
        if not player.equipped_weapon and not is_unarmed_finisher:
            logger.warning("[ATTACK CHECK] Ditolak: Agen tidak membawa senjata.")
            return False

        # 2. Validasi HP & EP Minimum
        hp_ratio = player.hp / player.max_hp
        if hp_ratio <= HP_RETREAT_THRESHOLD and not is_unarmed_finisher:
            logger.warning(f"[ATTACK CHECK] Ditolak: HP rendah ({player.hp}). Wajib Retreat.")
            return False

        if player.ep <= EP_MIN_RESERVE:
            logger.warning(f"[ATTACK CHECK] Ditolak: EP kritis ({player.ep}). Sisa EP wajib untuk kabur.")
            return False

        # 3. Validasi Kondisi Badai / Storm (Combat Rule: STORM RULES)
        if state.current_region.is_death_zone:
            logger.warning("[ATTACK CHECK] Ditolak: Sedang berada di dalam Death Zone. Prioritas keluar badai.")
            return False

        # 4. Kalkulasi Expected Value / Peluang Kemenangan
        win_prob = WinProbabilityCalculator.calculate(player, target)
        if win_prob < 0.30 and not is_unarmed_finisher:
            logger.warning(f"[ATTACK CHECK] Ditolak: Peluang menang terlalu rendah ({win_prob:.2%}).")
            return False

        # 5. Pengecualian Risiko Kepungan jika Finisher
        is_finish_kill_opportunity = (target.hp < 15 and win_prob > 0.80) or is_unarmed_finisher

        enemies_in_same_region = [e for e in state.visible_enemies if e.region_id == state.current_region.id]
        if len(enemies_in_same_region) >= 2 and not is_finish_kill_opportunity:
            logger.warning(f"[ATTACK CHECK] Ditolak: Terdeteksi {len(enemies_in_same_region)} musuh satu region. Risiko dikepung.")
            return False

        logger.info(f"[ATTACK CHECK] Sukses: Diizinkan menyerang {target.name} (Peluang Menang: {win_prob:.2%}).")
        return True
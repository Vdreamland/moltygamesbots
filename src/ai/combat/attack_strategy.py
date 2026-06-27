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
from src.config.constants import HP_RETREAT_THRESHOLD, EP_MIN_RESERVE, EP_COST_ATTACK, WEAPON_EP_COSTS
from src.ai.combat.win_probability import WinProbabilityCalculator

logger = logging.getLogger("ClawRoyale.AttackStrategy")

class AttackStrategy:
    @staticmethod
    def should_attack(state: GameState, target: Agent) -> bool:
        player = state.player

        # [REVISI]: Pastikan target masih hidup
        if not target.is_alive:
            logger.debug(f"[ATTACK CHECK] Target {target.name} sudah mati. Serangan dibatalkan.")
            return False

        is_unarmed_finisher = (
            player.equipped_weapon is None and 
            target.hp <= 5 and 
            target.region_id == state.current_region.id and
            target.is_alive
        )

        is_kill_opportunity = (
            is_unarmed_finisher or
            (player.equipped_weapon is not None and target.hp <= 25 and target.region_id == state.current_region.id and target.is_alive) or
            (target.equipped_weapon is None and target.region_id == state.current_region.id and target.is_alive)
        )

        distance = 0
        if target.region_id != state.current_region.id:
            if target.region_id in state.current_region.connections:
                distance = 1
            else:
                distance = 2
        
        weapon_range = player.equipped_weapon.range if player.equipped_weapon else 0
        if distance > weapon_range:
            logger.warning(f"[ATTACK CHECK] Ditolak: Target {target.name} berada di luar jangkauan (Jarak: {distance}, Range Senjata: {weapon_range}).")
            return False

        if not player.equipped_weapon and not is_unarmed_finisher:
            logger.warning("[ATTACK CHECK] Ditolak: Agen tidak membawa senjata.")
            return False

        is_target_weak = (
            target.equipped_weapon is None or
            target.ep <= 1 or
            target.hp < player.hp
        )

        hp_ratio = player.hp / player.max_hp
        if hp_ratio <= HP_RETREAT_THRESHOLD and not is_kill_opportunity and not is_target_weak:
            logger.warning(f"[ATTACK CHECK] Ditolak: HP rendah ({player.hp}) melawan musuh kuat. Wajib Retreat.")
            return False

        # [REVISI EP SERANGAN DINAMIS]: Cek biaya EP senjata taktis
        attack_cost = EP_COST_ATTACK
        if player.equipped_weapon:
            weapon_name = player.equipped_weapon.name.lower()
            for key, cost in WEAPON_EP_COSTS.items():
                if key in weapon_name:
                    attack_cost = cost
                    break

        if player.ep < attack_cost:
            logger.warning(f"[ATTACK CHECK] Ditolak: EP tidak mencukupi untuk menyerang dengan {player.equipped_weapon.name if player.equipped_weapon else 'Fist'} (Dibutuhkan: {attack_cost}, Sisa: {player.ep}).")
            return False

        if player.ep - attack_cost < EP_MIN_RESERVE and not is_kill_opportunity:
            logger.warning(f"[ATTACK CHECK] Ditolak: EP setelah menyerang ({player.ep - attack_cost}) di bawah batas aman cadangan ({EP_MIN_RESERVE}). Sisa EP wajib untuk kabur.")
            return False

        if state.current_region.is_death_zone:
            logger.warning("[ATTACK CHECK] Ditolak: Sedang berada di dalam Death Zone. Prioritas keluar badai.")
            return False

        win_prob = WinProbabilityCalculator.calculate(player, target)
        
        min_win_prob = 0.20 if is_target_weak else 0.30
        if win_prob < min_win_prob and not is_kill_opportunity:
            logger.warning(f"[ATTACK CHECK] Ditolak: Peluang menang terlalu rendah ({win_prob:.2%}).")
            return False

        is_finish_kill_opportunity = (target.hp < 15 and win_prob > 0.80) or is_kill_opportunity

        # [REVISI]: Filter musuh aktif/hidup saja
        enemies_in_same_region = [e for e in state.visible_enemies if e.region_id == state.current_region.id and e.is_alive]
        if len(enemies_in_same_region) >= 2 and not is_finish_kill_opportunity:
            logger.warning(f"[ATTACK CHECK] Ditolak: Terdeteksi {len(enemies_in_same_region)} musuh aktif satu region. Risiko dikepung.")
            return False

        logger.info(f"[ATTACK CHECK] Sukses: Diizinkan menyerang {target.name} (Peluang Menang: {win_prob:.2%}).")
        return True
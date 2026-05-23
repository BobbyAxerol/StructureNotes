"""
strategies/participation_rate.py
══════════════════════════════════
ParticipationRateStrategy — Uncapped Participation Rate Note.

Leg 1 → Zero-Coupon Bond  (100 % protection)
Leg 2 → Short OTM Put     (premium subsidy)
Leg 3 → Long ATM vanilla Call  (unlimited upside × participation_rate)

Trade-off: lower initial leverage but no profit ceiling.
"""

from __future__ import annotations

from typing import Dict, Tuple

from structured_notes.config import StrategyConfig, StrategyType
from structured_notes.strategies.base import BaseStrategy


class ParticipationRateStrategy(BaseStrategy):
    """Uncapped Participation Rate Note."""

    def __init__(self, config: StrategyConfig):
        assert config.enable_participation_rate, \
            "Set config.enable_participation_rate = True"
        super().__init__(config)
        self.strategy_type = StrategyType.PARTICIPATION_RATE

    def build_note(self, spot_start: float, vol: float, rate: float, **kwargs) -> Dict:
        T = self.config.duration_years

        bond_px    = self._bond_price(rate)
        opt_budget = self.config.initial_capital - bond_px

        # Short put subsidy
        put_K         = spot_start * self.config.put_cushion
        put_shares    = self.config.num_put_contracts * 100
        put_prem      = self.pricer.price(spot_start, put_K, T, rate, vol, "put")
        put_collected = put_prem * put_shares
        total_budget  = opt_budget + put_collected

        # Long ATM call  (no short call → uncapped)
        call_prem    = self.pricer.price(spot_start, spot_start, T, rate, vol, "call")
        num_call_sh  = int(total_budget / call_prem) if call_prem > 0 else 0
        residual     = total_budget - num_call_sh * call_prem

        effective_p  = (num_call_sh * call_prem) / self.config.initial_capital

        return dict(
            bond_invested           = bond_px,
            opt_budget              = opt_budget,
            put_strike              = put_K,
            put_shares              = put_shares,
            put_prem_per_share      = put_prem,
            put_collected           = put_collected,
            call_strike             = spot_start,
            call_prem               = call_prem,
            num_call_shares         = num_call_sh,
            residual_cash           = residual,
            total_opt_budget        = total_budget,
            participation_rate      = self.config.participation_rate,
            effective_participation = effective_p,
        )

    def compute_payoff(self, note: Dict, spot_end: float,
                       **kwargs) -> Tuple[float, float, float]:
        bond_val = self.config.initial_capital

        put_payoff = 0.0
        if spot_end < note["put_strike"]:
            put_payoff = (spot_end - note["put_strike"]) * note["put_shares"]

        call_payoff = 0.0
        if spot_end > note["call_strike"] and note["num_call_shares"] > 0:
            raw_gain    = (spot_end - note["call_strike"]) * note["num_call_shares"]
            call_payoff = raw_gain * note["participation_rate"]

        total = bond_val + put_payoff + call_payoff + note["residual_cash"]
        return total, put_payoff, call_payoff

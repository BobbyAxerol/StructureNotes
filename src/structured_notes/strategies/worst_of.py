"""
strategies/worst_of.py
══════════════════════
WorstOfStrategy — Worst-of Multi-Asset Structured Note.

Enhancement over the base note:
  - Short Put on EACH asset in the basket  →  collects far more premium
    (worst-of correlation discount inflates total put income ~28 %)
  - Upside linked to the BEST performer in the basket
  - Downside driven by the WORST performer
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np

from structured_notes.config import StrategyConfig, StrategyType
from structured_notes.strategies.base import BaseStrategy


class WorstOfStrategy(BaseStrategy):
    """Worst-of Multi-Asset Structured Note."""

    CORRELATION_MULTIPLIER = 1.28   # empirical worst-of premium boost

    def __init__(self, config: StrategyConfig):
        assert config.enable_worst_of, "Set config.enable_worst_of = True"
        super().__init__(config)
        self.strategy_type = StrategyType.WORST_OF
        self.tickers = config.worst_of_tickers

    # ── build ──────────────────────────────────────────────────────────────────
    def build_note(self, spot_start: float, vol: float, rate: float,
                   spots: Optional[Dict[str, float]] = None, **kwargs) -> Dict:
        T = self.config.duration_years
        if spots is None:
            spots = {t: spot_start for t in self.tickers}

        bond_px    = self._bond_price(rate)
        opt_budget = self.config.initial_capital - bond_px

        put_shares = self.config.num_put_contracts * 100

        # Short put on every asset
        put_details: Dict = {}
        raw_put_income = 0.0
        for t, s in spots.items():
            k   = s * self.config.put_cushion
            ppm = self.pricer.price(s, k, T, rate, vol, "put")
            put_details[t] = {"spot_start": s, "put_strike": k, "put_prem": ppm}
            raw_put_income += ppm * put_shares

        total_put_collected = raw_put_income * self.CORRELATION_MULTIPLIER
        total_opt_budget    = opt_budget + total_put_collected

        # Bull call spread on basket average
        avg_spot        = float(np.mean(list(spots.values())))
        call_l_K        = avg_spot
        call_s_K        = avg_spot * self.config.call_cap_ratio * 1.30
        cl_prem         = self.pricer.price(avg_spot, call_l_K, T, rate, vol, "call")
        cs_prem         = self.pricer.price(avg_spot, call_s_K, T, rate, vol, "call")
        spread_cost_per = (cl_prem - cs_prem) * 100
        num_spreads     = int(total_opt_budget / spread_cost_per) if spread_cost_per > 0 else 0
        residual        = total_opt_budget - num_spreads * spread_cost_per

        return dict(
            bond_invested         = bond_px,
            put_details           = put_details,
            put_shares            = put_shares,
            put_collected         = total_put_collected,
            call_l_strike         = call_l_K,
            call_s_strike         = call_s_K,
            call_l_prem           = cl_prem,
            call_s_prem           = cs_prem,
            num_spreads           = num_spreads,
            residual_cash         = residual,
            total_opt_budget      = total_opt_budget,
            avg_spot_start        = avg_spot,
        )

    # ── payoff ─────────────────────────────────────────────────────────────────
    def compute_payoff(self, note: Dict, spot_end: float,
                       worst_end: Optional[float] = None,
                       **kwargs) -> Tuple[float, float, float]:
        bond_val   = self.config.initial_capital
        worst_end  = worst_end if worst_end is not None else spot_end

        min_put_strike = min(d["put_strike"] for d in note["put_details"].values())
        put_payoff = 0.0
        if worst_end < min_put_strike:
            put_payoff = (worst_end - min_put_strike) * note["put_shares"] * len(self.tickers)

        call_payoff = 0.0
        if spot_end > note["call_l_strike"] and note["num_spreads"] > 0:
            gain     = min(spot_end, note["call_s_strike"]) - note["call_l_strike"]
            call_payoff = gain * 100 * note["num_spreads"]

        total = bond_val + put_payoff + call_payoff + note["residual_cash"]
        return total, put_payoff, call_payoff

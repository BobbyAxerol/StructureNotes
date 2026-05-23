"""
strategies/autocallable.py
══════════════════════════
AutocallableNoteStrategy — Autocallable extension of StructuredNoteStrategy.

At each observation date (e.g. 6, 12, 18 months), if the index
is at or above the barrier, the note terminates early and pays:
    par × (1 + autocall_coupon_rate × elapsed_years)

If never called, the note runs to maturity with the standard payoff.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import pandas as pd

from structured_notes.config import StrategyConfig, StrategyType
from structured_notes.strategies.structured_note import StructuredNoteStrategy


class AutocallableNoteStrategy(StructuredNoteStrategy):
    """Autocallable extension of StructuredNoteStrategy."""

    def __init__(self, config: StrategyConfig):
        assert config.enable_autocall, "Set config.enable_autocall = True"
        super().__init__(config)
        self.strategy_type = StrategyType.AUTOCALLABLE

    def compute_payoff_with_path(
        self,
        note:        Dict,
        path:        pd.DataFrame,
        spot_start:  float,
    ) -> Tuple[float, float, float, bool, Optional[int]]:
        """
        Walk observation dates; call early when barrier is breached.
        Returns (final_value, put_payoff, call_payoff, triggered, obs_month).
        """
        tdays = 252
        for obs_month, barrier in zip(self.config.autocall_observation_months,
                                       self.config.autocall_barriers):
            obs_idx = int(obs_month / 12 * tdays)
            if obs_idx >= len(path):
                continue
            spot_obs = float(path.iloc[obs_idx]["spot"])
            if spot_obs >= spot_start * barrier:
                elapsed_yr  = obs_month / 12
                redemption  = self.config.initial_capital * (
                    1 + self.config.autocall_coupon_rate * elapsed_yr)
                coupon_gain = redemption - self.config.initial_capital
                return redemption, 0.0, coupon_gain, True, obs_month

        # No autocall → standard maturity
        spot_end = float(path.iloc[-1]["spot"])
        val, pp, cp = self.compute_payoff(note, spot_end)
        return val, pp, cp, False, None

    def describe(self, note: Dict, spot_start: float) -> None:
        super().describe(note, spot_start)
        print("  [Autocall Parameters]")
        for m, b in zip(self.config.autocall_observation_months,
                        self.config.autocall_barriers):
            print(f"    Month {m:>3}: barrier {b*100:.0f}%  "
                  f"→ redeem at {self.config.autocall_coupon_rate*m/12*100:.1f}% coupon")
        print()

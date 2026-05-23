"""
strategies/structured_note.py
══════════════════════════════
StructuredNoteStrategy — Capital-Protected Structured Note.

Leg 1  →  Long Zero-Coupon Bond          (capital anchor, 100 % protection)
Leg 2  →  Short OTM Put  @ put_cushion   (premium subsidy to fund Leg 3)
Leg 3  →  Long Bull Call Spread ATM/cap  (upside engine with leverage)
"""

from __future__ import annotations

from typing import Dict, Tuple

from structured_notes.config import StrategyConfig, StrategyType
from structured_notes.strategies.base import BaseStrategy


class StructuredNoteStrategy(BaseStrategy):
    """Capital-Protected Structured Note."""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.strategy_type = StrategyType.STRUCTURED_NOTE

    def build_note(self, spot_start: float, vol: float, rate: float, **kwargs) -> Dict:
        T = self.config.duration_years
        bond_px    = self._bond_price(rate)
        opt_budget = self.config.initial_capital - bond_px
        put_K    = spot_start * self.config.put_cushion
        call_l_K = spot_start
        call_s_K = spot_start * self.config.call_cap_ratio
        put_prem    = self.pricer.price(spot_start, put_K,    T, rate, vol, "put")
        call_l_prem = self.pricer.price(spot_start, call_l_K, T, rate, vol, "call")
        call_s_prem = self.pricer.price(spot_start, call_s_K, T, rate, vol, "call")
        put_shares       = self.config.num_put_contracts * 100
        put_collected    = put_prem * put_shares
        total_opt_budget = opt_budget + put_collected
        spread_cost_per = (call_l_prem - call_s_prem) * 100
        num_spreads     = int(total_opt_budget / spread_cost_per) if spread_cost_per > 0 else 0
        residual        = total_opt_budget - num_spreads * spread_cost_per

        return dict(
            bond_invested         = bond_px,
            opt_budget_pre_put    = opt_budget,
            put_strike            = put_K,
            put_shares            = put_shares,
            put_prem_per_share    = put_prem,
            put_collected         = put_collected,
            call_l_strike         = call_l_K,
            call_s_strike         = call_s_K,
            call_l_prem           = call_l_prem,
            call_s_prem           = call_s_prem,
            spread_cost_per       = spread_cost_per,
            num_spreads           = num_spreads,
            residual_cash         = residual,
            total_opt_budget      = total_opt_budget,
        )

    def compute_payoff(self, note: Dict, spot_end: float,
                       **kwargs) -> Tuple[float, float, float]:
        bond_val = self.config.initial_capital

        # Short Put: loss only if spot falls below cushion
        put_payoff = 0.0
        if spot_end < note["put_strike"]:
            put_payoff = (spot_end - note["put_strike"]) * note["put_shares"]

        # Long Call Spread: gain between ATM and cap
        call_payoff = 0.0
        if spot_end > note["call_l_strike"] and note["num_spreads"] > 0:
            gain_per_sh = min(spot_end, note["call_s_strike"]) - note["call_l_strike"]
            call_payoff = gain_per_sh * 100 * note["num_spreads"]

        total = bond_val + put_payoff + call_payoff + note["residual_cash"]
        return total, put_payoff, call_payoff

    # ── describe ───────────────────────────────────────────────────────────────
    def describe(self, note: Dict, spot_start: float) -> None:
        cap   = self.config.initial_capital
        max_p = (note["call_s_strike"] - note["call_l_strike"]) * 100 * note["num_spreads"]
        W = 60

        def row(label, val): print(f"  {label:<30} {val}")

        print("\n" + "═" * W)
        print(f"  {self.strategy_type.value}")
        print("─" * W)
        row("Initial Capital",     f"${cap:>12,.0f}")
        row("  Bond invested",     f"${note['bond_invested']:>12,.2f}  ({note['bond_invested']/cap*100:.1f}%)")
        row("  Options budget",    f"${note['opt_budget_pre_put']:>12,.2f}  ({note['opt_budget_pre_put']/cap*100:.1f}%)")
        row("  + Put subsidy",     f"+${note['put_collected']:>11,.2f}  ({note['put_collected']/cap*100:.1f}%)")
        row("  = Total opt budget",f"${note['total_opt_budget']:>12,.2f}")
        print("─" * W)
        row("LEG A  Short Put",
            f"strike {note['put_strike']:>7.2f}  | {self.config.num_put_contracts}x contracts | prem ${note['put_prem_per_share']:.2f}/sh")
        row("LEG B  Long  Call",
            f"strike {note['call_l_strike']:>7.2f}  | {note['num_spreads']}x contracts | prem ${note['call_l_prem']:.2f}/sh")
        row("LEG C  Short Call",
            f"strike {note['call_s_strike']:>7.2f}  | {note['num_spreads']}x contracts | prem ${note['call_s_prem']:.2f}/sh")
        print("─" * W)
        row("Max Profit",  f"${max_p:>10,.0f}  ({max_p/cap*100:.1f}%)")
        row("Capital floor",f"${note['put_strike']:>10.2f}  ({note['put_strike']/spot_start*100:.0f}% of spot)")
        print("═" * W)

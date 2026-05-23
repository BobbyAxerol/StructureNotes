"""
config.py
═════════
StrategyConfig — tất cả tham số cấu hình của chiến lược.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


# ══════════════════════════════════════════════════════════════════════════════
#  1.  STRATEGY TYPE ENUM
# ══════════════════════════════════════════════════════════════════════════════

class StrategyType(Enum):
    STRUCTURED_NOTE    = "Capital-Protected Structured Note"
    AUTOCALLABLE       = "Autocallable Note"
    WORST_OF           = "Worst-of Multi-Asset Note"
    PARTICIPATION_RATE = "Participation Rate Note (Uncapped)"


# ══════════════════════════════════════════════════════════════════════════════
#  2.  STRATEGY CONFIG
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class StrategyConfig:
    # ── Core parameters ───────────────────────────────────────────────────────
    initial_capital:   float = 125_000
    duration_years:    float = 2.25
    put_cushion:       float = 0.80
    call_cap_ratio:    float = 1.15
    num_put_contracts: int   = 2

    # ── Backtest parameters ───────────────────────────────────────────────────
    step_months:    int   = 12
    start_date:     str   = "2012-01-01"
    end_date:       str   = "2026-01-01"
    risk_free_rate: float = 0.04

    # ── Extension 1 : Autocallable ────────────────────────────────────────────
    enable_autocall:             bool       = False
    autocall_observation_months: List[int]  = field(default_factory=lambda: [6, 12, 18])
    autocall_barriers:           List[float]= field(default_factory=lambda: [1.05, 1.05, 1.05])
    autocall_coupon_rate:        float      = 0.10

    # ── Extension 2 : Worst-of Multi-Asset ───────────────────────────────────
    enable_worst_of:   bool      = False
    worst_of_tickers:  List[str] = field(default_factory=lambda: ["SPY", "QQQ", "IWM"])

    # ── Extension 3 : Participation Rate ─────────────────────────────────────
    enable_participation_rate: bool  = False
    participation_rate:        float = 0.80

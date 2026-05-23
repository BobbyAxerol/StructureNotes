"""
models.py
══════════
NoteRecord — one row per backtest cycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class NoteRecord:
    start_date:            pd.Timestamp
    end_date:              pd.Timestamp
    spot_start:            float
    spot_end:              float
    bond_invested:         float
    put_strike:            float          # reference put strike (or min for worst-of)
    call_l_strike:         float
    call_s_strike:         float
    num_spreads:           int
    put_premium_collected: float
    put_payoff:            float
    call_payoff:           float
    final_value:           float
    strategy_return:       float
    benchmark_return:      float
    strategy_type:         str            = "Note"
    early_exit:            bool           = False
    early_exit_month:      Optional[int]  = None

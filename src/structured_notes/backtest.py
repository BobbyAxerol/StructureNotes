"""
backtest.py
═══════════
BacktestEngine — Rolling-window backtest supporting all strategy variants.

For each window [idx, idx+duration_days]:
  - Builds the note at window start
  - Computes payoff at window end (or earlier for Autocallable)
  - Records results as NoteRecord
"""

from __future__ import annotations

from typing import List

import pandas as pd

from structured_notes.analyzer import PerformanceAnalyzer
from structured_notes.config import StrategyConfig
from structured_notes.models import NoteRecord
from structured_notes.strategies.autocallable import AutocallableNoteStrategy
from structured_notes.strategies.base import BaseStrategy
from structured_notes.strategies.worst_of import WorstOfStrategy


class BacktestEngine:
    """Rolling-window backtest supporting all strategy variants."""

    TDAYS = 252

    def __init__(self, data: pd.DataFrame, strategy: BaseStrategy,
                 config: StrategyConfig):
        self.data     = data
        self.strategy = strategy
        self.config   = config
        self.records: List[NoteRecord] = []

    # ── run ────────────────────────────────────────────────────────────────────
    def run(self) -> None:
        dur_days  = int(self.config.duration_years * self.TDAYS)
        step_days = self.config.step_months * 21
        idx = 0
        n   = 0

        print(f"\n[Backtest] {self.strategy.strategy_type.value}  "
              f"({self.config.start_date} → {self.config.end_date})")

        while idx + dur_days < len(self.data):
            s_row  = self.data.iloc[idx]
            e_row  = self.data.iloc[idx + dur_days]

            spot_s = float(s_row["spot"])
            vol_s  = float(s_row["vol"])
            rate_s = float(s_row["rate"])
            spot_e = float(e_row["spot"])

            # ── build note ────────────────────────────────────────────────────
            if isinstance(self.strategy, WorstOfStrategy):
                wo_tickers = self.config.worst_of_tickers
                t_cols = [t for t in wo_tickers if t in self.data.columns]
                spots_at_start = {t: float(s_row[t]) for t in t_cols} if t_cols else None
                note = self.strategy.build_note(
                    spot_start=spot_s, vol=vol_s, rate=rate_s, spots=spots_at_start)
            else:
                note = self.strategy.build_note(
                    spot_start=spot_s, vol=vol_s, rate=rate_s)

            # ── compute payoff ────────────────────────────────────────────────
            early_exit, early_month = False, None

            if isinstance(self.strategy, AutocallableNoteStrategy):
                path = self.data.iloc[idx: idx + dur_days + 1]
                val, pp, cp, early_exit, early_month = \
                    self.strategy.compute_payoff_with_path(note, path, spot_s)

            elif isinstance(self.strategy, WorstOfStrategy):
                t_cols = [t for t in self.config.worst_of_tickers
                          if t in self.data.columns]
                if t_cols:
                    starts    = {t: float(s_row[t]) for t in t_cols}
                    ends      = {t: float(e_row[t]) for t in t_cols}
                    ret_map   = {t: ends[t] / starts[t] for t in t_cols}
                    worst_tkr = min(ret_map, key=ret_map.get)
                    best_tkr  = max(ret_map, key=ret_map.get)
                    worst_end = float(e_row[worst_tkr])
                    best_end  = float(e_row[best_tkr])
                    val, pp, cp = self.strategy.compute_payoff(
                        note, best_end, worst_end=worst_end)
                else:
                    val, pp, cp = self.strategy.compute_payoff(note, spot_e)

            else:
                val, pp, cp = self.strategy.compute_payoff(note, spot_e)

            strat_ret = (val / self.config.initial_capital) - 1
            bench_ret = (spot_e / spot_s) - 1

            # ── determine reference put_strike for NoteRecord ─────────────────
            if "put_details" in note:
                ref_put_k = min(d["put_strike"] for d in note["put_details"].values())
            else:
                ref_put_k = note.get("put_strike", 0.0)

            self.records.append(NoteRecord(
                start_date            = self.data.index[idx],
                end_date              = self.data.index[idx + dur_days],
                spot_start            = spot_s,
                spot_end              = spot_e,
                bond_invested         = note.get("bond_invested", 0.0),
                put_strike            = ref_put_k,
                call_l_strike         = note.get("call_l_strike",
                                                  note.get("call_strike", 0.0)),
                call_s_strike         = note.get("call_s_strike", 0.0),
                num_spreads           = note.get("num_spreads",
                                                  note.get("num_call_shares", 0)),
                put_premium_collected = note.get("put_collected", 0.0),
                put_payoff            = pp,
                call_payoff           = cp,
                final_value           = val,
                strategy_return       = strat_ret,
                benchmark_return      = bench_ret,
                strategy_type         = self.strategy.strategy_type.value,
                early_exit            = early_exit,
                early_exit_month      = early_month,
            ))
            idx += step_days
            n   += 1

        print(f"[Backtest] Completed {n} note cycles.")

    def analyzer(self) -> PerformanceAnalyzer:
        return PerformanceAnalyzer(self.records, self.config)

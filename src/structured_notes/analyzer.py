"""
analyzer.py
═══════════
PerformanceAnalyzer — Compute and report comprehensive performance statistics.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from structured_notes.config import StrategyConfig
from structured_notes.models import NoteRecord


class PerformanceAnalyzer:
    """Compute and report comprehensive performance statistics from NoteRecords."""

    def __init__(self, records: List[NoteRecord], config: StrategyConfig):
        self.records = records
        self.config  = config
        self.df      = pd.DataFrame([r.__dict__ for r in records])

    # ── metrics ────────────────────────────────────────────────────────────────
    def compute_metrics(self) -> Dict:
        df  = self.df
        sr  = df["strategy_return"].values
        br  = df["benchmark_return"].values
        ann = 1.0 / self.config.duration_years

        # Equity curves (reinvested)
        eq_curve = (1 + pd.Series(sr)).cumprod()
        bm_curve = (1 + pd.Series(br)).cumprod()

        # CAGR
        n_yrs  = len(sr) * self.config.duration_years
        cagr_s = eq_curve.iloc[-1] ** (1 / n_yrs) - 1 if n_yrs > 0 else 0
        cagr_b = bm_curve.iloc[-1] ** (1 / n_yrs) - 1 if n_yrs > 0 else 0

        # Sharpe (annualised)
        rf_per = self.config.risk_free_rate * self.config.duration_years
        excess = sr - rf_per
        sharpe = (excess.mean() / excess.std(ddof=1)) * np.sqrt(ann) \
                 if excess.std() > 1e-9 else np.nan

        # Sortino (annualised, only negative excess)
        neg      = excess[excess < 0]
        dn_std   = neg.std(ddof=1) if len(neg) > 1 else 1e-9
        sortino  = (excess.mean() / dn_std) * np.sqrt(ann)

        # Max Drawdown on equity curve
        roll_max  = eq_curve.cummax()
        dd_series = (eq_curve - roll_max) / roll_max
        max_dd    = float(dd_series.min())

        # Calmar
        calmar = cagr_s / abs(max_dd) if abs(max_dd) > 1e-9 else np.nan

        # Annualised vol
        vol_s = sr.std(ddof=1) * np.sqrt(ann)
        vol_b = br.std(ddof=1) * np.sqrt(ann)

        # Autocall stats (if applicable)
        early_exit_rate = df["early_exit"].mean() if "early_exit" in df else 0.0

        return dict(
            n               = len(sr),
            avg_return      = sr.mean(),
            avg_bench       = br.mean(),
            cagr_s          = cagr_s,
            cagr_b          = cagr_b,
            vol_s           = vol_s,
            vol_b           = vol_b,
            sharpe          = sharpe,
            sortino         = sortino,
            calmar          = calmar,
            max_drawdown    = max_dd,
            win_rate        = float((sr >= 0).mean()),
            beat_bench      = float((sr >= br).mean()),
            early_exit_rate = early_exit_rate,
            eq_curve        = eq_curve,
            bm_curve        = bm_curve,
            dd_series       = dd_series,
        )

    # ── print report ───────────────────────────────────────────────────────────
    def print_report(self, m: Dict) -> None:
        W = 64

        def row(label, s_val, b_val=""):
            print(f"  {label:<32} {str(s_val):>10}  {str(b_val):>10}")

        print("\n" + "═" * W)
        print(f"  BACKTEST PERFORMANCE REPORT")
        print(f"  Period : {self.config.start_date} → {self.config.end_date}")
        print(f"  Cycles : {m['n']}  |  Step {self.config.step_months}m  "
              f"|  Duration {self.config.duration_years}yr")
        print("─" * W)
        print(f"  {'Metric':<32} {'Strategy':>10}  {'Benchmark':>10}")
        print("─" * W)
        row("Avg Return / Note",
            f"{m['avg_return']*100:+.2f}%", f"{m['avg_bench']*100:+.2f}%")
        row("CAGR (annualised)",
            f"{m['cagr_s']*100:+.2f}%",    f"{m['cagr_b']*100:+.2f}%")
        row("Annualised Vol",
            f"{m['vol_s']*100:.2f}%",       f"{m['vol_b']*100:.2f}%")
        print("─" * W)
        row("Sharpe Ratio",    f"{m['sharpe']:.3f}")
        row("Sortino Ratio",   f"{m['sortino']:.3f}")
        row("Calmar Ratio",    f"{m['calmar']:.3f}")
        row("Max Drawdown",    f"{m['max_drawdown']*100:.2f}%")
        print("─" * W)
        row("Win Rate",        f"{m['win_rate']*100:.1f}%")
        row("Beat Benchmark",  f"{m['beat_bench']*100:.1f}%")
        if m["early_exit_rate"] > 0:
            row("Autocall Rate",  f"{m['early_exit_rate']*100:.1f}%")
        print("═" * W)

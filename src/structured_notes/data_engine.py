"""
data_engine.py
══════════════
DataEngine — Download và pre-process market data via Yahoo Finance.
"""

from __future__ import annotations

from typing import List

import pandas as pd
import yfinance as yf

from structured_notes.config import StrategyConfig


class DataEngine:
    """Download and pre-process market data via Yahoo Finance."""

    def __init__(self, config: StrategyConfig):
        self.config = config

    # ── helpers ───────────────────────────────────────────────────────────────
    def _dl(self, tickers: List[str]) -> pd.DataFrame:
        raw = yf.download(
            tickers,
            start       = self.config.start_date,
            end         = self.config.end_date,
            auto_adjust = True,
            progress    = False,
        )
        if raw.empty:
            raise ValueError("Yahoo Finance returned no data. Check tickers / dates.")
        return raw

    # ── single-asset (main + autocall + participation-rate) ───────────────────
    def fetch_single_asset(self) -> pd.DataFrame:
        """Returns DataFrame with columns: spot, vol, rate."""
        raw = self._dl(["SPY", "^VIX", "^TNX"])
        df = pd.DataFrame({
            "spot": raw["Close"]["SPY"],
            "vol":  raw["Close"]["^VIX"] / 100.0,
            "rate": raw["Close"]["^TNX"] / 100.0,
        }).dropna()
        print(f"[DataEngine] {len(df)} trading days  "
              f"({df.index[0].date()} → {df.index[-1].date()})")
        return df

    # ── multi-asset (worst-of) ────────────────────────────────────────────────
    def fetch_multi_asset(self) -> pd.DataFrame:
        """Returns DataFrame with columns: vol, rate, <ticker1>, <ticker2>, …"""
        tickers = self.config.worst_of_tickers + ["^VIX", "^TNX"]
        raw = self._dl(tickers)
        close = raw["Close"]
        df = pd.DataFrame({"vol":  close["^VIX"] / 100.0,
                           "rate": close["^TNX"] / 100.0})
        for t in self.config.worst_of_tickers:
            df[t] = close[t]
        df = df.dropna()
        # BacktestEngine expects a "spot" column → use first ticker as benchmark
        df["spot"] = df[self.config.worst_of_tickers[0]]
        print(f"[DataEngine] Multi-asset {self.config.worst_of_tickers}: "
              f"{len(df)} common days")
        return df

"""
pricer.py
══════════
OptionPricer — Vectorised Black-Scholes pricer for vanilla European options.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm
from typing import Tuple


class OptionPricer:
    """Vectorised Black-Scholes pricer for vanilla European options."""

    @staticmethod
    def _d1d2(S: float, K: float, T: float, r: float, sigma: float) -> Tuple[float, float]:
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return d1, d1 - sigma * np.sqrt(T)

    @classmethod
    def price(cls, S: float, K: float, T: float, r: float, sigma: float,
              kind: str = "call") -> float:
        """European option price (call / put)."""
        if T <= 0:
            return float(max(0.0, S - K) if kind == "call" else max(0.0, K - S))
        d1, d2 = cls._d1d2(S, K, T, r, sigma)
        if kind == "call":
            return float(S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))
        return float(K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1))

    @classmethod
    def delta(cls, S: float, K: float, T: float, r: float, sigma: float,
              kind: str = "call") -> float:
        if T <= 0:
            return 1.0 if (kind == "call" and S > K) else 0.0
        d1, _ = cls._d1d2(S, K, T, r, sigma)
        return float(norm.cdf(d1) if kind == "call" else -norm.cdf(-d1))

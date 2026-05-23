"""
strategies/base.py
══════════════════
BaseStrategy — Abstract interface for all structured note strategies.
"""

from __future__ import annotations

import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Tuple

from structured_notes.config import StrategyConfig, StrategyType
from structured_notes.pricer import OptionPricer


class BaseStrategy(ABC):
    """Abstract interface for all structured note strategies."""

    def __init__(self, config: StrategyConfig):
        self.config        = config
        self.pricer        = OptionPricer()
        self.strategy_type = StrategyType.STRUCTURED_NOTE

    def _bond_price(self, rate: float) -> float:
        """Present value of the zero-coupon bond anchor."""
        return self.config.initial_capital / np.exp(rate * self.config.duration_years)

    @abstractmethod
    def build_note(self, spot_start: float, vol: float, rate: float, **kwargs) -> Dict:
        """Construct the note; return a dict of all structural details."""

    @abstractmethod
    def compute_payoff(self, note: Dict, spot_end: float,
                       **kwargs) -> Tuple[float, float, float]:
        """Return (final_portfolio_value, put_payoff, call_payoff)."""

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}("
                f"${self.config.initial_capital:,.0f}, "
                f"{self.config.duration_years}yr)")

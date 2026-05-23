"""
visualizer.py
═════════════
Visualizer — Static factory methods for all charts and scenario tables.
"""

from __future__ import annotations

from typing import Dict

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np

from structured_notes.analyzer import PerformanceAnalyzer
from structured_notes.strategies.base import BaseStrategy

# ── Colour palette ─────────────────────────────────────────────────────────────
_P = {
    "blue":   "#2563EB",
    "green":  "#16A34A",
    "red":    "#DC2626",
    "amber":  "#D97706",
    "purple": "#7C3AED",
    "gray":   "#64748B",
    "light":  "#F1F5F9",
    "bg":     "#F8FAFC",
    "dark":   "#1E293B",
}


class Visualizer:
    """Static factory methods for all charts."""

    # ── 1. Payoff Diagram ──────────────────────────────────────────────────────
    @staticmethod
    def payoff_diagram(strategy: BaseStrategy, note: Dict, spot_start: float,
                       filename: str = "payoff_diagram.png") -> None:
        cap    = strategy.config.initial_capital
        spots  = np.linspace(spot_start * 0.45, spot_start * 1.55, 700)
        rets   = np.array([(strategy.compute_payoff(note=note, spot_end=float(s))[0]
                            / cap - 1) * 100 for s in spots])

        fig, ax = plt.subplots(figsize=(13, 6))
        fig.patch.set_facecolor(_P["bg"])
        ax.set_facecolor(_P["bg"])

        ax.fill_between(spots, rets, 0, where=rets >= 0,
                        alpha=0.13, color=_P["green"])
        ax.fill_between(spots, rets, 0, where=rets <  0,
                        alpha=0.13, color=_P["red"])
        ax.plot(spots, rets, lw=2.5, color=_P["blue"], label="Strategy Payoff", zorder=5)
        ax.axhline(0, lw=0.9, ls="--", color=_P["dark"], alpha=0.35)
        ax.axvline(spot_start, lw=1.3, ls=":", color=_P["amber"],
                   label=f"Spot now ({spot_start:.0f})", alpha=0.85)

        key_lines = [
            (note.get("put_strike"),              "Put floor",    _P["red"]),
            (note.get("call_l_strike",
                       note.get("call_strike")),  "Long Call",    _P["green"]),
            (note.get("call_s_strike"),            "Cap (Short)",  _P["amber"]),
        ]
        for k, lbl, col in key_lines:
            if k and k > 0:
                ax.axvline(k, lw=1.5, ls="--", color=col, alpha=0.65,
                           label=f"{lbl} ({k:.0f})")

        ax.set_xlabel("SPY Price at Maturity", fontsize=12)
        ax.set_ylabel("Return at Maturity (%)", fontsize=12)
        ax.set_title(f"{strategy.strategy_type.value}\nPayoff Profile",
                     fontsize=14, fontweight="bold", color=_P["dark"])
        ax.legend(fontsize=9, framealpha=0.9, loc="upper left")
        ax.grid(True, alpha=0.22)
        ax.spines[["top", "right"]].set_visible(False)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:+.1f}%"))
        plt.tight_layout()
        plt.savefig(filename, dpi=150, bbox_inches="tight")
        plt.show()
        print(f"[Chart] Saved → {filename}")

    # ── 2. Scenario Table ──────────────────────────────────────────────────────
    @staticmethod
    def scenario_table(strategy: BaseStrategy, note: Dict, spot_start: float) -> None:
        cap    = strategy.config.initial_capital
        moves  = [-0.30, -0.25, -0.20, -0.15, -0.10, -0.05,
                   0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
        W = 76
        print(f"\n{'═'*W}")
        print(f"  SCENARIO ANALYSIS  |  Capital ${cap:,.0f}  |  Spot {spot_start:.2f}")
        print(f"{'─'*W}")
        print(f"  {'Move':<8}  {'SPY End':<9}  {'Put P&L':>11}  "
              f"{'Call P&L':>11}  {'Portfolio':>12}  {'Return':>8}")
        print(f"{'─'*W}")
        for m in moves:
            s           = spot_start * (1 + m)
            val, pp, cp = strategy.compute_payoff(note=note, spot_end=float(s))
            ret         = (val / cap - 1) * 100
            flag        = " ★" if ret > 0 else (" ✗" if ret < -5 else "  ")
            print(f"  {m:>+5.0%}{flag}  {s:<9.1f}  {pp:>+11,.0f}  "
                  f"{cp:>+11,.0f}  ${val:>10,.0f}  {ret:>+7.2f}%")
        print(f"{'═'*W}")

    # ── 3. Backtest Dashboard ──────────────────────────────────────────────────
    @staticmethod
    def backtest_dashboard(analyzer: PerformanceAnalyzer,
                           title:    str = "Backtest Dashboard",
                           filename: str = "backtest_dashboard.png") -> None:
        m  = analyzer.compute_metrics()
        df = analyzer.df

        fig = plt.figure(figsize=(22, 15))
        fig.patch.set_facecolor(_P["bg"])
        gs  = gridspec.GridSpec(3, 3, figure=fig, hspace=0.52, wspace=0.38)

        def _ax(subplot, title_txt=""):
            a = fig.add_subplot(subplot)
            a.set_facecolor(_P["bg"])
            a.grid(True, alpha=0.20)
            a.spines[["top", "right"]].set_visible(False)
            if title_txt:
                a.set_title(title_txt, fontweight="bold", fontsize=11)
            return a

        # ── Panel 1 : Cumulative Return ───────────────────────────────────────
        ax1 = _ax(gs[0, :2], "Cumulative Return (Reinvested, per-note compounding)")
        x   = range(len(m["eq_curve"]))
        ax1.plot(x, (m["eq_curve"] - 1) * 100, lw=2.5, color=_P["blue"],
                 label="Strategy", zorder=5)
        ax1.plot(x, (m["bm_curve"] - 1) * 100, lw=1.8, color=_P["gray"],
                 ls="--", label="SPY Buy & Hold", alpha=0.8)
        ax1.fill_between(x, (m["eq_curve"] - 1) * 100, 0,
                         where=(m["eq_curve"] - 1) >= 0,
                         alpha=0.09, color=_P["blue"])
        ax1.set_ylabel("Cumulative Return (%)")
        ax1.set_xlabel("Note Cycle #")
        ax1.legend(fontsize=9)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.0f}%"))

        # ── Panel 2 : KPI Box ─────────────────────────────────────────────────
        ax2 = fig.add_subplot(gs[0, 2])
        ax2.axis("off")
        kpi_lines = [
            ("PERFORMANCE KPIs",                 ""),
            ("─" * 28,                           ""),
            ("Avg Return / Note",  f"{m['avg_return']*100:>+8.2f}%"),
            ("CAGR",               f"{m['cagr_s']*100:>+8.2f}%"),
            ("Benchmark CAGR",     f"{m['cagr_b']*100:>+8.2f}%"),
            ("─" * 28,            ""),
            ("Sharpe Ratio",       f"{m['sharpe']:>8.3f}"),
            ("Sortino Ratio",      f"{m['sortino']:>8.3f}"),
            ("Calmar Ratio",       f"{m['calmar']:>8.3f}"),
            ("─" * 28,            ""),
            ("Max Drawdown",       f"{m['max_drawdown']*100:>+8.2f}%"),
            ("Annualised Vol",     f"{m['vol_s']*100:>8.2f}%"),
            ("─" * 28,            ""),
            ("Win Rate",           f"{m['win_rate']*100:>8.1f}%"),
            ("Beat Benchmark",     f"{m['beat_bench']*100:>8.1f}%"),
            ("N Cycles",           f"{m['n']:>8d}"),
        ]
        if m["early_exit_rate"] > 0:
            kpi_lines.append(("Autocall Rate", f"{m['early_exit_rate']*100:>8.1f}%"))
        txt = "\n".join(f"{l:<20}{r}" for l, r in kpi_lines)
        ax2.text(0.04, 0.97, txt, transform=ax2.transAxes,
                 va="top", ha="left", fontsize=9.8, fontfamily="monospace",
                 bbox=dict(boxstyle="round,pad=0.7", facecolor="white",
                           edgecolor="#CBD5E1", alpha=0.96))

        # ── Panel 3 : Drawdown ────────────────────────────────────────────────
        ax3 = _ax(gs[1, :2], "Equity-Curve Drawdown")
        dd  = m["dd_series"]
        ax3.fill_between(range(len(dd)), dd * 100, 0,
                         color=_P["red"], alpha=0.40)
        ax3.plot(range(len(dd)), dd * 100, lw=1.4, color=_P["red"])
        ax3.set_ylabel("Drawdown (%)")
        ax3.set_xlabel("Note Cycle #")
        ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}%"))

        # ── Panel 4 : Return Distribution ────────────────────────────────────
        ax4 = _ax(gs[1, 2], "Return Distribution (per Note)")
        ax4.hist(df["benchmark_return"] * 100, bins=14,
                 alpha=0.40, color=_P["gray"], label="SPY", edgecolor="white")
        ax4.hist(df["strategy_return"] * 100, bins=14,
                 alpha=0.78, color=_P["blue"], label="Strategy", edgecolor="white")
        ax4.axvline(0, color=_P["dark"], lw=1, ls="--")
        ax4.set_xlabel("Return (%)")
        ax4.legend(fontsize=9)

        # ── Panel 5 : Strategy vs Benchmark scatter ───────────────────────────
        ax5 = _ax(gs[2, :1], "Strategy vs Benchmark (per-Cycle)")
        sr = df["strategy_return"] * 100
        br = df["benchmark_return"] * 100
        colors = [_P["green"] if s >= 0 else _P["red"] for s in sr]
        ax5.scatter(br, sr, c=colors, alpha=0.75, s=50, edgecolors="white", lw=0.5)
        lim = max(abs(br.max()), abs(br.min()), abs(sr.max()), abs(sr.min())) * 1.1
        ax5.plot([-lim, lim], [-lim, lim], ls="--", color=_P["gray"],
                 lw=1, label="Parity")
        ax5.axhline(0, lw=0.6, color=_P["dark"], alpha=0.3)
        ax5.axvline(0, lw=0.6, color=_P["dark"], alpha=0.3)
        ax5.set_xlabel("SPY Return (%)")
        ax5.set_ylabel("Strategy Return (%)")
        ax5.legend(fontsize=9)
        ax5.set_xlim(-lim, lim)
        ax5.set_ylim(-lim, lim)

        # ── Panel 6 : Per-cycle grouped bar ───────────────────────────────────
        ax6 = _ax(gs[2, 1:], "Per-Note Return vs SPY Benchmark")
        xn  = np.arange(len(df))
        w   = 0.4
        bar_colors = [_P["green"] if r >= 0 else _P["red"]
                      for r in df["strategy_return"]]
        ax6.bar(xn - w / 2, df["strategy_return"] * 100, width=w,
                color=bar_colors, alpha=0.88, label="Strategy")
        ax6.bar(xn + w / 2, df["benchmark_return"] * 100, width=w,
                color=_P["gray"],  alpha=0.50, label="SPY")
        ax6.axhline(0, color=_P["dark"], lw=0.8, ls="--")
        labels = [f"{d.year}-{str(d.month).zfill(2)}" for d in df["start_date"]]
        ax6.set_xticks(xn)
        ax6.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax6.set_ylabel("Return (%)")
        ax6.legend(fontsize=9)
        ax6.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.0f}%"))

        fig.suptitle(title, fontsize=16, fontweight="bold",
                     color=_P["dark"], y=1.01)
        plt.savefig(filename, dpi=150, bbox_inches="tight")
        plt.show()
        print(f"[Chart] Saved → {filename}")

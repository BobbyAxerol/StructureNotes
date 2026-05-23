"""
main.py
═══════
Entry point — orchestrate tất cả các chiến lược.

Chạy:
    uv run python main.py
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from structured_notes.backtest import BacktestEngine
from structured_notes.config import StrategyConfig
from structured_notes.data_engine import DataEngine
from structured_notes.strategies import (
    AutocallableNoteStrategy,
    ParticipationRateStrategy,
    StructuredNoteStrategy,
    WorstOfStrategy,
)
from structured_notes.visualizer import Visualizer


def main() -> None:

    config = StrategyConfig(
        initial_capital   = 125_000,
        duration_years    = 2.25,
        put_cushion       = 0.80,     # put strike = spot × 0.80  (-20 % cushion)
        call_cap_ratio    = 1.15,     # short call = spot × 1.15
        num_put_contracts = 2,

        step_months       = 12,
        start_date        = "2012-01-01",
        end_date          = "2026-01-01",
        risk_free_rate    = 0.04,

        enable_autocall             = False,
        autocall_observation_months = [6, 12, 18],
        autocall_barriers           = [1.05, 1.05, 1.05],
        autocall_coupon_rate        = 0.10,

        enable_worst_of             = False,
        worst_of_tickers            = ["SPY", "QQQ", "IWM"],

        enable_participation_rate   = False,
        participation_rate          = 0.80,
    )

    data_eng = DataEngine(config)
    df_main  = data_eng.fetch_single_asset()
    snap     = df_main.iloc[-1]   # latest snapshot for structure display

    print("\n" + "═" * 64)
    print("  MAIN STRATEGY : Capital-Protected Structured Note")
    print("═" * 64)

    strat_main = StructuredNoteStrategy(config)
    note_main  = strat_main.build_note(
        float(snap["spot"]), float(snap["vol"]), float(snap["rate"]))

    strat_main.describe(note_main, float(snap["spot"]))
    Visualizer.scenario_table(strat_main, note_main, float(snap["spot"]))
    Visualizer.payoff_diagram(strat_main, note_main, float(snap["spot"]))

    bt_main = BacktestEngine(df_main, strat_main, config)
    bt_main.run()
    an_main = bt_main.analyzer()
    an_main.print_report(an_main.compute_metrics())
    Visualizer.backtest_dashboard(
        an_main,
        title    = "Capital-Protected Structured Note — Backtest Dashboard",
        filename = "dashboard_main.png",
    )

    if config.enable_autocall:
        print("\n" + "═" * 64)
        print("  EXTENSION 1 : Autocallable Note")
        print("═" * 64)

        strat_ac = AutocallableNoteStrategy(config)
        note_ac  = strat_ac.build_note(
            float(snap["spot"]), float(snap["vol"]), float(snap["rate"]))
        strat_ac.describe(note_ac, float(snap["spot"]))
        Visualizer.payoff_diagram(
            strat_ac, note_ac, float(snap["spot"]),
            filename="payoff_autocall.png")

        bt_ac = BacktestEngine(df_main, strat_ac, config)
        bt_ac.run()
        an_ac = bt_ac.analyzer()
        an_ac.print_report(an_ac.compute_metrics())
        Visualizer.backtest_dashboard(
            an_ac,
            title    = "Autocallable Note — Backtest Dashboard",
            filename = "dashboard_autocall.png",
        )

    if config.enable_worst_of:
        print("\n" + "═" * 64)
        print("  EXTENSION 2 : Worst-of Multi-Asset Note")
        print("═" * 64)

        df_multi = data_eng.fetch_multi_asset()
        strat_wo = WorstOfStrategy(config)

        snap_wo  = df_multi.iloc[-1]
        spots_wo = {t: float(snap_wo[t]) for t in config.worst_of_tickers}
        note_wo  = strat_wo.build_note(
            float(snap_wo["spot"]), float(snap_wo["vol"]),
            float(snap_wo["rate"]), spots=spots_wo)

        print(f"\n  Asset basket   : {config.worst_of_tickers}")
        print(f"  Put strikes    : "
              + "  ".join(f"{t}={d['put_strike']:.1f}"
                           for t, d in note_wo["put_details"].items()))
        print(f"  Total subsidy  : ${note_wo['put_collected']:,.0f}")
        print(f"  Num spreads    : {note_wo['num_spreads']}")
        print(f"  Call L / S     : {note_wo['call_l_strike']:.1f} "
              f"/ {note_wo['call_s_strike']:.1f}")

        Visualizer.payoff_diagram(
            strat_wo, note_wo, float(snap_wo["spot"]),
            filename="payoff_worst_of.png")

        bt_wo = BacktestEngine(df_multi, strat_wo, config)
        bt_wo.run()
        an_wo = bt_wo.analyzer()
        an_wo.print_report(an_wo.compute_metrics())
        Visualizer.backtest_dashboard(
            an_wo,
            title    = "Worst-of Multi-Asset Note — Backtest Dashboard",
            filename = "dashboard_worst_of.png",
        )

    if config.enable_participation_rate:
        print("\n" + "═" * 64)
        print("  EXTENSION 3 : Participation Rate Note (Uncapped)")
        print("═" * 64)

        strat_pr = ParticipationRateStrategy(config)
        note_pr  = strat_pr.build_note(
            float(snap["spot"]), float(snap["vol"]), float(snap["rate"]))

        print(f"\n  Participation rate    : {note_pr['participation_rate']*100:.0f}%")
        print(f"  Effective coverage    : {note_pr['effective_participation']*100:.1f}%")
        print(f"  Call shares (ATM)     : {note_pr['num_call_shares']}")
        print(f"  Put strike / subsidy  : "
              f"{note_pr['put_strike']:.2f}  /  ${note_pr['put_collected']:,.0f}")

        Visualizer.scenario_table(strat_pr, note_pr, float(snap["spot"]))
        Visualizer.payoff_diagram(
            strat_pr, note_pr, float(snap["spot"]),
            filename="payoff_participation.png")

        bt_pr = BacktestEngine(df_main, strat_pr, config)
        bt_pr.run()
        an_pr = bt_pr.analyzer()
        an_pr.print_report(an_pr.compute_metrics())
        Visualizer.backtest_dashboard(
            an_pr,
            title    = "Participation Rate Note — Backtest Dashboard",
            filename = "dashboard_participation.png",
        )


if __name__ == "__main__":
    main()

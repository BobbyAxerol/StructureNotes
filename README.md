# Structured Notes Backtester

Backtester cho các chiến lược Structured Note bảo vệ vốn sử dụng Black-Scholes, dữ liệu Yahoo Finance và rolling-window backtest.

## Cấu trúc dự án

```
structured_notes/
├── pyproject.toml
├── README.md
├── .gitignore
├── main.py                          ← Entry point
└── src/structured_notes/
    ├── config.py                    ← StrategyConfig
    ├── pricer.py                    ← Black-Scholes OptionPricer
    ├── data_engine.py               ← DataEngine (Yahoo Finance)
    ├── models.py                    ← NoteRecord dataclass
    ├── backtest.py                  ← BacktestEngine
    ├── analyzer.py                  ← PerformanceAnalyzer
    ├── visualizer.py                ← Visualizer (charts)
    └── strategies/
        ├── base.py                  ← BaseStrategy (ABC)
        ├── structured_note.py       ← Capital-Protected Note
        ├── autocallable.py          ← Autocallable extension
        ├── worst_of.py              ← Worst-of Multi-Asset
        └── participation_rate.py    ← Participation Rate (Uncapped)
```

## Cài đặt (dùng uv)

```bash
# Cài uv nếu chưa có
curl -Ls https://astral.sh/uv/install.sh | sh

# Tạo venv và cài dependencies
uv sync

# Chạy backtest
uv run python main.py
```

## Các chiến lược

| Strategy | Flag | Mô tả |
|---|---|---|
| `StructuredNoteStrategy` | *(mặc định)* | Bond + Short Put + Bull Call Spread |
| `AutocallableNoteStrategy` | `enable_autocall=True` | Thoát sớm khi vượt barrier |
| `WorstOfStrategy` | `enable_worst_of=True` | Multi-asset, phụ thuộc asset kém nhất |
| `ParticipationRateStrategy` | `enable_participation_rate=True` | Uncapped, không short call |

## Cấu hình

Chỉnh `StrategyConfig` trong `main.py`:

```python
config = StrategyConfig(
    initial_capital   = 125_000,
    duration_years    = 2.25,
    put_cushion       = 0.80,   # Put strike = spot × 0.80
    call_cap_ratio    = 1.15,   # Short call = spot × 1.15
    start_date        = "2012-01-01",
    end_date          = "2026-01-01",
    enable_autocall   = False,
    enable_worst_of   = False,
    enable_participation_rate = False,
)
```

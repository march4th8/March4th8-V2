# WICK by Sharpe

**A personal trading assistant that translates charts into plain English.**

Wick sits in a browser tab next to your thinkorswim (or Webull) chart. You type a ticker. It reads the price data and tells you exactly what happened — trend direction, key support and resistance levels, moving averages, momentum, and volume — in plain English, with the reasoning explained so you understand *why*, not just *what*.

It never predicts the future. It never tells you to buy or sell. It describes the past accurately and teaches you to read charts yourself.

---

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red?style=flat-square)
![SQLite](https://img.shields.io/badge/Storage-SQLite%20local-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## The Problem It Solves

Most beginner traders open a chart and see noise. They can identify that a line went up or down, but they can't quickly answer:

- Is this stock actually in an uptrend or just bouncing?
- Where has price historically reversed?
- Is momentum stretched or is there room to run?
- Are buyers or sellers in control based on volume?

Wick answers all of that in seconds, with plain-English explanations and the reasoning behind each call. The goal is to train your eyes until you don't need the tool anymore.

---

## Features

### Phase 1 — Chart Translator
Pull daily OHLCV data for any ticker and get a structured plain-English analysis:

- **Trend** — identifies uptrend, downtrend, weak trend, or sideways by analyzing the sequence of swing highs and lows
- **Support & Resistance** — clusters recent swing high/low levels into 2–3 key price zones with touch counts
- **Moving Averages** — 50-day and 200-day SMAs with golden cross / death cross detection
- **Momentum (RSI 14)** — value, label (oversold / neutral / overbought), and plain-English explanation
- **Volume** — rising or falling trend, buyer or seller conviction based on up-day vs down-day volume
- **Plain-English Summary** — 3–4 sentences stitching all signals together
- **Teaching Lines** — every call includes a *why* clause so you learn the reasoning, not just the verdict

### Phase 2 — Position Size & Risk Calculator
Enter your account size, entry price, stop-loss, and max risk percentage. Wick calculates the exact number of shares to buy so that a loss at your stop equals precisely your chosen risk. Shows dollar risk, position value, and reward-to-risk ratio if a target is provided.

### Phase 3 — Pre-Trade Checklist
Four rules checked before every trade:
1. Is there a clear trend?
2. Is a stop-loss defined?
3. Is the risk within your max percentage? *(auto-calculated)*
4. Is the reward at least 2x the risk? *(auto-calculated)*

If any rule fails, you see a clear warning. The tool does not block you — it makes sure you *see* when you are about to break your own rules.

### Phase 4 — Trade Journal & Analytics
A local SQLite journal that tracks every trade and builds your performance history:

- Log trades with entry, stop, target, shares, reason/setup tag, and checklist status
- Close open trades to auto-calculate P&L and mark WIN / LOSS / BREAKEVEN
- **Statistics:** win rate, average win, average loss, total P&L, expectancy per trade, discipline score
- **Best & Worst Setups:** ranked by average P&L per reason tag — shows you which setups actually make money
- **Cumulative P&L chart** — visual equity curve of your closed trades

---

## Dashboard

Run `streamlit run app.py` for a full browser dashboard with five tabs:

| Tab | Description |
|---|---|
| How to Use | Step-by-step guide to the workflow and every feature |
| Chart Translator | Live Plotly chart (candles, MAs, S/R levels, Volume, RSI) + metric cards + full text analysis |
| Position Calculator | Form-based calculator with instant results |
| Pre-Trade Checklist | Visual pass/fail cards per rule, auto-calculated from trade numbers |
| Trade Journal | Log, close, history table, P&L bar chart, statistics |

The dashboard forces dark mode and uses a trading-terminal color scheme — designed to sit comfortably beside thinkorswim on a second monitor.

---

## Installation

**Requirements:** Python 3.10 or higher

```bash
# 1. Clone the repo
git clone https://github.com/YOURUSERNAME/wick.git
cd wick

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # Mac / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the dashboard
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## CLI Usage

Every feature is also available from the terminal without opening the browser:

```bash
# Phase 1 — Chart analysis
python cli.py AAPL              # 3-month default
python cli.py TSLA 6m           # 6-month window
python cli.py SPY 1y            # 1-year window
# Available windows: 1m, 3m, 6m, 1y

# Phase 2 — Position size calculator (interactive)
python cli.py calc

# Phase 2 — Position size calculator (flags)
python cli.py calc --account 10000 --entry 150 --stop 145 --target 165 --risk 2

# Phase 3 — Pre-trade checklist (interactive)
python cli.py check

# Phase 3 — Pre-trade checklist (flags)
python cli.py check --account 10000 --entry 150 --stop 145 --target 165 --risk 2

# Phase 4 — Trade journal
python cli.py log               # log a new trade (interactive)
python cli.py trades            # view all trades
python cli.py stats             # view statistics
python cli.py close 3 152.50   # close trade #3 at exit price 152.50
```

### Example CLI output — Chart Translator

```
============================================================
  WICK -- AAPL   (as of 2026-06-08)
============================================================

------------------------------------------------------------
  TREND
------------------------------------------------------------
  WEAK UPTREND over the past 3 months.
  WHY: I called it weak uptrend because rally peaks are rising
  but the pullback lows are not consistently higher -- buyers
  are gaining ground but unevenly.

------------------------------------------------------------
  SUPPORT & RESISTANCE
------------------------------------------------------------
  Current price: $301.54
  Resistance: $303.20 (tagged 1x)
  Support:    $245.51 (tagged 3x), $264.83 (tagged 1x)

------------------------------------------------------------
  MOVING AVERAGES
------------------------------------------------------------
  50-day MA:  $282.06  ->  price is ABOVE it
  200-day MA: $265.14  ->  price is ABOVE it
  Cross status: GOLDEN CROSS territory (50-day above 200-day)

------------------------------------------------------------
  MOMENTUM -- RSI (14-period)
------------------------------------------------------------
  RSI = 53.4  ->  NEUTRAL

------------------------------------------------------------
  VOLUME
------------------------------------------------------------
  Volume trend: RISING over the analysis window.
  Conviction:   Up-day and down-day volume are roughly equal.

============================================================
  Description of past price action only.
  Not a prediction or financial advice.
============================================================
```

---

## Project Structure

```
wick/
├── app.py               # Streamlit dashboard — all 4 phases on one screen
├── cli.py               # Terminal entry point for all phases
│
├── data_source.py       # Market data layer (yfinance wrapper)
│                        # Swappable: replace this file to switch data providers
│
├── analyzer.py          # Phase 1: trend, S/R, MAs, RSI, volume, readout builder
├── risk_calculator.py   # Phase 2: position size and R:R calculator
├── checklist.py         # Phase 3: pre-trade rule checker
├── journal.py           # Phase 4: SQLite CRUD, stats, formatting
│
├── requirements.txt     # Python dependencies
├── .streamlit/
│   └── config.toml      # Dark theme + brand colors
└── .gitignore           # Excludes *.db (your trade data stays local)
```

---

## Swappable Data Source

All market data flows through a single module: `data_source.py`. It exposes one function:

```python
def fetch_ohlcv(ticker: str, lookback_days: int = 90) -> pd.DataFrame:
    ...
```

The current implementation uses `yfinance` (free, no API key required). To switch providers — for example to Polygon.io or Alpha Vantage — rewrite only this file. The analyzer, calculator, checklist, journal, and dashboard all call `fetch_ohlcv()` and are completely unaffected.

**Why this matters:** yfinance is excellent for personal use. For commercial distribution, a licensed data provider is required. The swap is designed to take under two hours.

```
Current:   data_source.py -> yfinance    -> Yahoo Finance (free, personal use)
Upgrade:   data_source.py -> Polygon.io  -> Licensed commercial data feed
```

---

## The Workflow

This tool is designed to run alongside your trading platform, not replace it:

1. Open thinkorswim (or Webull) with your live chart
2. Open Wick by Sharpe at `http://localhost:8501` in a browser tab beside it
3. Type a ticker and click Analyze
4. Read the output — then verify every point against your live chart with your own eyes
5. If you're considering a trade: Position Calculator → Pre-Trade Checklist → Trade Journal

**The goal:** after consistent use, you won't need the chart translator anymore. You'll read the chart directly. The tool trains your eyes, then gets out of the way.

---

## Hard Rules

These rules are enforced throughout the application and cannot be turned off:

1. **No predictions.** Wick describes past price action only. It never forecasts future price movement.
2. **No buy or sell recommendations.** All trade decisions are the user's alone.
3. **Every market readout includes a disclaimer** stating it is educational, not financial advice.
4. **All data is stored locally.** No accounts, no cloud sync, no data leaves your machine.
5. **One swappable data module.** The data source is isolated so it can be upgraded without touching analysis logic.

---

## Roadmap

| Phase | Status | Description |
|---|---|---|
| Phase 1 — Chart Translator | Complete | Trend, S/R, MAs, RSI, Volume, plain-English analysis |
| Phase 2 — Position Calculator | Complete | Share sizing, dollar risk, reward:risk ratio |
| Phase 3 — Pre-Trade Checklist | Complete | 4-rule discipline checker with auto-calculation |
| Phase 4 — Trade Journal | Complete | SQLite journal, stats, equity curve |
| Streamlit Dashboard | Complete | All phases on one screen, dark trading UI |
| Phase 5 — Watchlist & Alerts | Planned | Daily digest of tickers that broke levels or had unusual volume |
| Standalone .exe | Planned | PyInstaller build for distribution without Python |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `yfinance` | >=0.2.40 | Market data (swappable) |
| `pandas` | >=2.0.0 | Data processing |
| `numpy` | >=1.26.0 | Numerical calculations |
| `streamlit` | >=1.35.0 | Web dashboard |
| `plotly` | >=5.20.0 | Interactive charts |

---

## License

MIT License — free to use, modify, and distribute with attribution.

---

## Disclaimer

**Wick by Sharpe is an educational tool.** All outputs describe historical price action only. Nothing in this application constitutes financial advice, a recommendation to buy or sell any security, or a prediction of future price movement. Trading involves substantial risk of loss. Always conduct your own research and consult a licensed financial advisor before making investment decisions.

"""
cli.py -- Phase 1-4 entry point.

PHASE 1 -- Chart translator:
    python cli.py AAPL
    python cli.py TSLA 6m

PHASE 2 -- Position-size calculator:
    python cli.py calc
    python cli.py calc --account 10000 --entry 150 --stop 145 --target 165 --risk 2

PHASE 3 -- Pre-trade checklist:
    python cli.py check
    python cli.py check --account 10000 --entry 150 --stop 145 --target 165 --risk 2

PHASE 4 -- Trade journal:
    python cli.py log               log a trade (interactive)
    python cli.py trades            show all trades
    python cli.py stats             show statistics
    python cli.py close <id> <exit> close an open trade
"""

import sys
from data_source import fetch_ohlcv
from analyzer import build_readout
from risk_calculator import calculate_position, format_result
from checklist import run_checklist, format_checklist
from journal import (
    init_db, log_trade, close_trade, get_all_trades, get_stats,
    format_stats, format_trades_table,
)

LOOKBACK_MAP = {"1m": 21, "3m": 63, "6m": 126, "1y": 252}


# ── Input helpers ─────────────────────────────────────────

def _prompt_float(prompt: str, default: float = None) -> float:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            return float(raw)
        except ValueError:
            print("  Please enter a number (e.g. 10000 or 1.5).")


def _prompt_optional_float(prompt: str) -> float | None:
    raw = input(f"{prompt} [Enter to skip]: ").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _prompt_str(prompt: str, default: str = None) -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"{prompt}{suffix}: ").strip()
    return raw if raw else (default or "")


def _prompt_optional_str(prompt: str) -> str | None:
    raw = input(f"{prompt} [Enter to skip]: ").strip()
    return raw or None


def _prompt_yn(prompt: str) -> bool:
    while True:
        raw = input(f"{prompt} (y/n): ").strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  Please type y or n.")


def _prompt_choice(prompt: str, choices: list[str], default: str = None) -> str:
    display = "/".join(f"[{c}]" if c == default else c for c in choices)
    while True:
        raw = input(f"{prompt} ({display}): ").strip().upper()
        if raw == "" and default:
            return default
        if raw in [c.upper() for c in choices]:
            return raw
        print(f"  Choose one of: {', '.join(choices)}")


def _parse_flags(argv: list) -> dict:
    result = {}
    for i, arg in enumerate(argv):
        if arg.startswith("--") and i + 1 < len(argv):
            try:
                result[arg[2:]] = float(argv[i + 1])
            except ValueError:
                result[arg[2:]] = argv[i + 1]
    return result


# ── Phase 1 ──────────────────────────────────────────────

def run_phase1(ticker: str, window_arg: str):
    window = LOOKBACK_MAP.get(window_arg, 63)
    print(f"\nFetching data for {ticker}...")
    try:
        df = fetch_ohlcv(ticker, lookback_days=window + 250)
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    print(build_readout(ticker, df, window=window))


# ── Phase 2 ──────────────────────────────────────────────

def run_phase2_interactive():
    print("\n" + "=" * 60)
    print("  WICK -- POSITION SIZE CALCULATOR")
    print("=" * 60)
    account = _prompt_float("  Account size ($)")
    entry   = _prompt_float("  Entry price ($)")
    stop    = _prompt_float("  Stop-loss price ($)")
    target  = _prompt_optional_float("  Profit target ($)")
    risk    = _prompt_float("  Max risk % of account", default=2.0)
    print(format_result(calculate_position(account, entry, stop, risk_pct=risk, target=target)))


def run_phase2_flags(argv: list):
    f = _parse_flags(argv)
    account, entry, stop = f.get("account"), f.get("entry"), f.get("stop")
    missing = [f"--{k}" for k, v in [("account", account), ("entry", entry), ("stop", stop)] if v is None]
    if missing:
        print(f"Error: missing {', '.join(missing)}")
        sys.exit(1)
    print(format_result(calculate_position(
        float(account), float(entry), float(stop),
        risk_pct=float(f.get("risk", 2.0)),
        target=float(f["target"]) if "target" in f else None,
    )))


# ── Phase 3 ──────────────────────────────────────────────

def run_phase3_interactive():
    print("\n" + "=" * 60)
    print("  WICK -- PRE-TRADE CHECKLIST")
    print("=" * 60)
    trend_ok = _prompt_yn("  1. Is there a clear trend (not choppy sideways)?")
    stop_set = _prompt_yn("  2. Do you have a specific stop-loss price set?")

    print("\n  Enter numbers for auto-check of rules 3 & 4, or leave blank to answer manually.\n")
    account = _prompt_optional_float("  Account size ($)")

    if account is not None:
        entry  = _prompt_float("  Entry price ($)")
        stop   = _prompt_float("  Stop-loss price ($)")
        target = _prompt_optional_float("  Profit target ($)")
        risk   = _prompt_float("  Max risk %", default=2.0)
        result = run_checklist(trend_ok, stop_set, account, entry, stop, target, risk)
    else:
        risk_ok   = _prompt_yn("  3. Is your risk <= 2% of your account?")
        reward_ok = _prompt_yn("  4. Is your reward >= 2x your risk?")
        result = run_checklist(trend_ok, stop_set)
        result.items[2].passed = risk_ok
        result.items[2].detail = "You confirmed this manually."
        result.items[3].passed = reward_ok
        result.items[3].detail = "You confirmed this manually."
        result.fail_count = sum(1 for i in result.items if not i.passed)
        result.all_passed = result.fail_count == 0

    print(format_checklist(result))


def run_phase3_flags(argv: list):
    f = _parse_flags(argv)
    account, entry, stop = f.get("account"), f.get("entry"), f.get("stop")
    missing = [f"--{k}" for k, v in [("account", account), ("entry", entry), ("stop", stop)] if v is None]
    if missing:
        print(f"Error: missing {', '.join(missing)}")
        sys.exit(1)
    trend_ok = bool(float(f.get("trend", 1)))
    stop_set = bool(float(f.get("stopset", 1)))
    result = run_checklist(
        trend_ok, stop_set,
        float(account), float(entry), float(stop),
        float(f["target"]) if "target" in f else None,
        float(f.get("risk", 2.0)),
    )
    print(format_checklist(result))


# ── Phase 4 ──────────────────────────────────────────────

def run_log():
    print("\n" + "=" * 60)
    print("  WICK -- LOG A TRADE")
    print("=" * 60)
    print("  Fill in the details. Press Enter to skip optional fields.\n")

    ticker    = _prompt_str("  Ticker").upper()
    direction = _prompt_choice("  Direction", ["LONG", "SHORT"], default="LONG")
    entry     = _prompt_float("  Entry price ($)")
    stop      = _prompt_float("  Stop-loss price ($)")
    target    = _prompt_optional_float("  Target price ($)")
    shares    = _prompt_optional_float("  Shares")
    account   = _prompt_optional_float("  Account size ($)")
    risk_pct  = _prompt_float("  Risk %", default=2.0)
    reason    = _prompt_optional_str("  Setup / reason tag (e.g. 'breakout', 'pullback')")
    checklist = _prompt_yn("  Did you run through the pre-trade checklist and pass all rules?")
    notes     = _prompt_optional_str("  Notes")

    print("\n  Is this an open trade, or do you already have an exit?")
    result_choice = _prompt_choice("  Result", ["OPEN", "WIN", "LOSS", "BREAKEVEN"], default="OPEN")

    exit_price = None
    if result_choice != "OPEN":
        exit_price = _prompt_float("  Exit price ($)")

    trade_id = log_trade(
        ticker=ticker,
        direction=direction,
        entry=entry,
        stop=stop,
        target=target,
        exit_price=exit_price,
        shares=int(shares) if shares else None,
        account_size=account,
        risk_pct=risk_pct,
        reason=reason,
        result=result_choice,
        checklist_passed=checklist,
        notes=notes,
    )

    print(f"\n  Trade logged with ID #{trade_id}.")
    if result_choice == "OPEN":
        print(f"  When you close it: python cli.py close {trade_id} <exit_price>")
    print()


def run_close(args: list):
    if len(args) < 2:
        print("Usage: python cli.py close <trade_id> <exit_price>")
        sys.exit(1)
    try:
        trade_id   = int(args[0])
        exit_price = float(args[1])
    except ValueError:
        print("Error: trade_id must be an integer, exit_price must be a number.")
        sys.exit(1)

    trade = close_trade(trade_id, exit_price)
    if trade is None:
        print(f"Error: no trade with ID #{trade_id}.")
        sys.exit(1)

    sign = "+" if (trade.pnl or 0) >= 0 else ""
    print(f"\n  Trade #{trade_id} closed: {trade.result}  P&L = ${sign}{trade.pnl:,.2f}\n")


def run_trades():
    trades = get_all_trades()
    print(format_trades_table(trades))


def run_stats():
    stats = get_stats()
    print(format_stats(stats))


# ── Router ────────────────────────────────────────────────

def main():
    init_db()
    args = sys.argv[1:]

    if not args:
        print("Usage:")
        print("  python cli.py <TICKER> [1m|3m|6m|1y]     -- Phase 1: chart translator")
        print("  python cli.py calc                         -- Phase 2: position-size calculator")
        print("  python cli.py check                        -- Phase 3: pre-trade checklist")
        print("  python cli.py log                          -- Phase 4: log a trade")
        print("  python cli.py trades                       -- Phase 4: show all trades")
        print("  python cli.py stats                        -- Phase 4: show statistics")
        print("  python cli.py close <id> <exit_price>      -- Phase 4: close an open trade")
        sys.exit(1)

    cmd = args[0].lower()
    rest = args[1:]

    if cmd == "calc":
        run_phase2_flags(rest) if any(a.startswith("--") for a in rest) else run_phase2_interactive()
    elif cmd == "check":
        run_phase3_flags(rest) if any(a.startswith("--") for a in rest) else run_phase3_interactive()
    elif cmd == "log":
        run_log()
    elif cmd == "close":
        run_close(rest)
    elif cmd == "trades":
        run_trades()
    elif cmd == "stats":
        run_stats()
    else:
        ticker = args[0].upper()
        window_arg = args[1].lower() if len(args) > 1 else "3m"
        run_phase1(ticker, window_arg)


if __name__ == "__main__":
    main()

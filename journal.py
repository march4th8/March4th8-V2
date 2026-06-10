"""
journal.py -- Phase 4: SQLite trade journal + analytics.

All data stays local. DB file: wick_journal.db (same directory as this script).
"""

import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from datetime import date as dt_date

DB_PATH = Path(__file__).parent / "wick_journal.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT    NOT NULL,
    ticker          TEXT    NOT NULL,
    direction       TEXT    NOT NULL,
    entry           REAL    NOT NULL,
    stop            REAL    NOT NULL,
    target          REAL,
    exit_price      REAL,
    shares          INTEGER,
    account_size    REAL,
    risk_pct        REAL    DEFAULT 2.0,
    reason          TEXT,
    result          TEXT    DEFAULT 'OPEN',
    pnl             REAL,
    checklist_passed INTEGER DEFAULT 0,
    notes           TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
)
"""


@dataclass
class TradeRecord:
    id: Optional[int]
    date: str
    ticker: str
    direction: str          # LONG / SHORT
    entry: float
    stop: float
    target: Optional[float]
    exit_price: Optional[float]
    shares: Optional[int]
    account_size: Optional[float]
    risk_pct: float
    reason: Optional[str]
    result: str             # OPEN / WIN / LOSS / BREAKEVEN
    pnl: Optional[float]
    checklist_passed: bool
    notes: Optional[str]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(SCHEMA)
        conn.commit()


def log_trade(
    ticker: str,
    direction: str,
    entry: float,
    stop: float,
    target: Optional[float] = None,
    exit_price: Optional[float] = None,
    shares: Optional[int] = None,
    account_size: Optional[float] = None,
    risk_pct: float = 2.0,
    reason: Optional[str] = None,
    result: str = "OPEN",
    checklist_passed: bool = False,
    notes: Optional[str] = None,
    trade_date: Optional[str] = None,
) -> int:
    """Insert a new trade. Returns the new row id."""
    date_str = trade_date or str(dt_date.today())

    pnl = None
    if exit_price is not None and shares is not None and result != "OPEN":
        if direction == "LONG":
            pnl = round((exit_price - entry) * shares, 2)
        else:
            pnl = round((entry - exit_price) * shares, 2)

    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO trades
              (date, ticker, direction, entry, stop, target, exit_price,
               shares, account_size, risk_pct, reason, result, pnl,
               checklist_passed, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                date_str, ticker.upper(), direction.upper(),
                entry, stop, target, exit_price,
                shares, account_size, risk_pct,
                reason, result.upper(),
                pnl,
                1 if checklist_passed else 0,
                notes,
            ),
        )
        conn.commit()
        return cur.lastrowid


def close_trade(trade_id: int, exit_price: float) -> Optional[TradeRecord]:
    """
    Mark an open trade as closed. Calculates P&L and sets result
    to WIN / LOSS / BREAKEVEN automatically.
    Returns the updated trade, or None if id not found.
    """
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM trades WHERE id = ?", (trade_id,)
        ).fetchone()
        if row is None:
            return None

        direction = row["direction"]
        entry = row["entry"]
        shares = row["shares"] or 1

        if direction == "LONG":
            pnl = round((exit_price - entry) * shares, 2)
        else:
            pnl = round((entry - exit_price) * shares, 2)

        if pnl > 0:
            result = "WIN"
        elif pnl < 0:
            result = "LOSS"
        else:
            result = "BREAKEVEN"

        conn.execute(
            "UPDATE trades SET exit_price=?, result=?, pnl=? WHERE id=?",
            (exit_price, result, pnl, trade_id),
        )
        conn.commit()

    return get_trade(trade_id)


def get_trade(trade_id: int) -> Optional[TradeRecord]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM trades WHERE id = ?", (trade_id,)
        ).fetchone()
    return _row_to_record(row) if row else None


def get_all_trades(limit: int = 500) -> list[TradeRecord]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM trades ORDER BY date DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_record(r) for r in rows]


def delete_trade(trade_id: int) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
        conn.commit()
    return cur.rowcount > 0


def get_stats() -> dict:
    """
    Returns a dict with:
      total, open_count, closed_count, wins, losses, breakevens,
      win_rate, avg_win, avg_loss, total_pnl, expect_per_trade,
      discipline_score, best_reasons, worst_reasons
    """
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM trades").fetchall()

    if not rows:
        return _empty_stats()

    all_trades = [_row_to_record(r) for r in rows]
    closed = [t for t in all_trades if t.result != "OPEN" and t.pnl is not None]
    wins   = [t for t in closed if t.result == "WIN"]
    losses = [t for t in closed if t.result == "LOSS"]
    open_t = [t for t in all_trades if t.result == "OPEN"]

    win_rate = (len(wins) / len(closed) * 100) if closed else 0.0
    avg_win  = (sum(t.pnl for t in wins) / len(wins)) if wins else 0.0
    avg_loss = (sum(t.pnl for t in losses) / len(losses)) if losses else 0.0
    total_pnl = sum(t.pnl for t in closed)

    # Expectancy per trade = (win_rate * avg_win) + ((1-win_rate) * avg_loss)
    if closed:
        wr = win_rate / 100
        expect = (wr * avg_win) + ((1 - wr) * avg_loss)
    else:
        expect = 0.0

    # Discipline: % of ALL trades where checklist was run and passed
    discipline = (
        sum(1 for t in all_trades if t.checklist_passed) / len(all_trades) * 100
        if all_trades else 0.0
    )

    # Best / worst setups by reason
    reason_stats = {}
    for t in closed:
        tag = t.reason or "untagged"
        if tag not in reason_stats:
            reason_stats[tag] = {"count": 0, "total_pnl": 0.0, "wins": 0}
        reason_stats[tag]["count"] += 1
        reason_stats[tag]["total_pnl"] += t.pnl
        if t.result == "WIN":
            reason_stats[tag]["wins"] += 1

    for tag, s in reason_stats.items():
        s["avg_pnl"] = s["total_pnl"] / s["count"]
        s["win_rate"] = s["wins"] / s["count"] * 100

    sorted_reasons = sorted(reason_stats.items(), key=lambda x: x[1]["avg_pnl"], reverse=True)
    best_reasons  = sorted_reasons[:3]
    worst_reasons = sorted_reasons[-3:][::-1]

    return {
        "total":           len(all_trades),
        "open_count":      len(open_t),
        "closed_count":    len(closed),
        "wins":            len(wins),
        "losses":          len(losses),
        "breakevens":      len([t for t in closed if t.result == "BREAKEVEN"]),
        "win_rate":        round(win_rate, 1),
        "avg_win":         round(avg_win, 2),
        "avg_loss":        round(avg_loss, 2),
        "total_pnl":       round(total_pnl, 2),
        "expect_per_trade": round(expect, 2),
        "discipline_score": round(discipline, 1),
        "best_reasons":    best_reasons,
        "worst_reasons":   worst_reasons,
        "all_trades":      all_trades,
        "closed_trades":   closed,
    }


def format_stats(stats: dict) -> str:
    if stats["total"] == 0:
        return "\n  No trades logged yet. Use 'python cli.py log' to add your first trade.\n"

    sep = "-" * 60
    lines = []
    lines.append(f"\n{'=' * 60}")
    lines.append("  WICK -- TRADE JOURNAL STATISTICS")
    lines.append(f"{'=' * 60}")

    lines.append(f"\n{sep}")
    lines.append("  SUMMARY")
    lines.append(sep)
    lines.append(f"  Total trades:      {stats['total']}  ({stats['open_count']} open, {stats['closed_count']} closed)")
    lines.append(f"  Win / Loss:        {stats['wins']}W / {stats['losses']}L / {stats['breakevens']}BE")
    lines.append(f"  Win rate:          {stats['win_rate']}%")
    lines.append(f"  Avg win:          ${stats['avg_win']:,.2f}")
    lines.append(f"  Avg loss:         ${stats['avg_loss']:,.2f}")
    lines.append(f"  Total realized P&L: ${stats['total_pnl']:,.2f}")
    lines.append(f"  Expectancy/trade: ${stats['expect_per_trade']:,.2f}  (what you make on avg per trade taken)")
    lines.append(f"  Discipline score:  {stats['discipline_score']}%  (trades where checklist was completed)")

    if stats["best_reasons"]:
        lines.append(f"\n{sep}")
        lines.append("  BEST SETUPS (by avg P&L)")
        lines.append(sep)
        for tag, s in stats["best_reasons"]:
            lines.append(f"  {tag!r:30s}  avg ${s['avg_pnl']:+,.2f}  ({s['count']} trades, {s['win_rate']:.0f}% win rate)")

    if stats["worst_reasons"] and stats["worst_reasons"] != stats["best_reasons"]:
        lines.append(f"\n{sep}")
        lines.append("  WORST SETUPS (by avg P&L)")
        lines.append(sep)
        for tag, s in stats["worst_reasons"]:
            lines.append(f"  {tag!r:30s}  avg ${s['avg_pnl']:+,.2f}  ({s['count']} trades, {s['win_rate']:.0f}% win rate)")

    lines.append(f"\n{'=' * 60}")
    lines.append("  Description of past price action only. Not a prediction or financial advice.")
    lines.append(f"{'=' * 60}\n")
    return "\n".join(lines)


def format_trades_table(trades: list[TradeRecord]) -> str:
    if not trades:
        return "\n  No trades logged yet.\n"

    header = f"  {'ID':>4}  {'Date':10}  {'Tkr':5}  {'Dir':5}  {'Entry':>8}  {'Stop':>8}  {'Exit':>8}  {'Shares':>6}  {'P&L':>9}  {'Result':10}  Reason"
    sep = "  " + "-" * (len(header) - 2)
    lines = [f"\n{sep}", header, sep]

    for t in trades:
        pnl_str  = f"${t.pnl:+,.2f}" if t.pnl is not None else "     --"
        exit_str = f"{t.exit_price:.2f}" if t.exit_price else "    --"
        reason   = (t.reason or "")[:20]
        shares   = str(t.shares) if t.shares else "--"
        lines.append(
            f"  {t.id:>4}  {t.date:10}  {t.ticker:5}  {t.direction:5}  "
            f"{t.entry:>8.2f}  {t.stop:>8.2f}  {exit_str:>8}  "
            f"{shares:>6}  {pnl_str:>9}  {t.result:10}  {reason}"
        )

    lines.append(sep + "\n")
    return "\n".join(lines)


def _row_to_record(row: sqlite3.Row) -> TradeRecord:
    return TradeRecord(
        id=row["id"],
        date=row["date"],
        ticker=row["ticker"],
        direction=row["direction"],
        entry=row["entry"],
        stop=row["stop"],
        target=row["target"],
        exit_price=row["exit_price"],
        shares=row["shares"],
        account_size=row["account_size"],
        risk_pct=row["risk_pct"],
        reason=row["reason"],
        result=row["result"],
        pnl=row["pnl"],
        checklist_passed=bool(row["checklist_passed"]),
        notes=row["notes"],
    )


def _empty_stats() -> dict:
    return {
        "total": 0, "open_count": 0, "closed_count": 0,
        "wins": 0, "losses": 0, "breakevens": 0,
        "win_rate": 0.0, "avg_win": 0.0, "avg_loss": 0.0,
        "total_pnl": 0.0, "expect_per_trade": 0.0,
        "discipline_score": 0.0,
        "best_reasons": [], "worst_reasons": [],
        "all_trades": [], "closed_trades": [],
    }

"""
risk_calculator.py -- Phase 2: position-size and risk calculator.

All math, no I/O. Call calculate_position() from cli.py or the future
Streamlit dashboard.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PositionResult:
    account_size: float
    risk_pct: float
    entry: float
    stop: float
    target: Optional[float]

    dollar_risk_allowed: float      # account_size * risk_pct / 100
    risk_per_share: float           # abs(entry - stop)
    shares: int                     # floor(dollar_risk_allowed / risk_per_share)
    actual_dollar_risk: float       # shares * risk_per_share (slightly <= allowed due to flooring)
    total_position_value: float     # shares * entry

    reward_per_share: Optional[float]   # abs(target - entry) if target given
    dollar_reward: Optional[float]      # shares * reward_per_share
    reward_risk_ratio: Optional[float]  # reward_per_share / risk_per_share
    rr_ok: Optional[bool]               # True if ratio >= 2.0

    direction: str                  # "LONG" or "SHORT"
    valid: bool                     # False if inputs are nonsensical
    error: Optional[str]            # human-readable problem if not valid


def calculate_position(
    account_size: float,
    entry: float,
    stop: float,
    risk_pct: float = 2.0,
    target: Optional[float] = None,
) -> PositionResult:
    """
    Core position-size math.

    Long trade:  stop must be below entry.
    Short trade: stop must be above entry.
    Direction is inferred automatically.
    """
    # Basic sanity checks
    if account_size <= 0:
        return _err(account_size, risk_pct, entry, stop, target, "Account size must be greater than zero.")
    if entry <= 0:
        return _err(account_size, risk_pct, entry, stop, target, "Entry price must be greater than zero.")
    if stop <= 0:
        return _err(account_size, risk_pct, entry, stop, target, "Stop-loss price must be greater than zero.")
    if entry == stop:
        return _err(account_size, risk_pct, entry, stop, target, "Entry and stop-loss cannot be the same price.")
    if not (0 < risk_pct <= 100):
        return _err(account_size, risk_pct, entry, stop, target, "Risk % must be between 0 and 100.")

    direction = "LONG" if stop < entry else "SHORT"

    dollar_risk_allowed = account_size * (risk_pct / 100)
    risk_per_share = abs(entry - stop)
    shares = int(dollar_risk_allowed / risk_per_share)

    if shares < 1:
        return _err(
            account_size, risk_pct, entry, stop, target,
            f"Risk budget of ${dollar_risk_allowed:.2f} is too small to buy even 1 share "
            f"with a ${risk_per_share:.2f}/share stop distance. "
            f"Widen the stop, increase account size, or raise risk %."
        )

    actual_dollar_risk = shares * risk_per_share
    total_position_value = shares * entry

    # Target / reward calculations
    reward_per_share = reward = rr_ratio = rr_ok = None
    if target is not None:
        if direction == "LONG" and target <= entry:
            return _err(account_size, risk_pct, entry, stop, target,
                        "Target must be above entry for a long trade.")
        if direction == "SHORT" and target >= entry:
            return _err(account_size, risk_pct, entry, stop, target,
                        "Target must be below entry for a short trade.")
        reward_per_share = abs(target - entry)
        reward = shares * reward_per_share
        rr_ratio = round(reward_per_share / risk_per_share, 2)
        rr_ok = rr_ratio >= 2.0

    return PositionResult(
        account_size=account_size,
        risk_pct=risk_pct,
        entry=entry,
        stop=stop,
        target=target,
        dollar_risk_allowed=round(dollar_risk_allowed, 2),
        risk_per_share=round(risk_per_share, 2),
        shares=shares,
        actual_dollar_risk=round(actual_dollar_risk, 2),
        total_position_value=round(total_position_value, 2),
        reward_per_share=round(reward_per_share, 2) if reward_per_share else None,
        dollar_reward=round(reward, 2) if reward else None,
        reward_risk_ratio=rr_ratio,
        rr_ok=rr_ok,
        direction=direction,
        valid=True,
        error=None,
    )


def format_result(r: PositionResult) -> str:
    """Plain-English readout for the CLI or Streamlit."""
    sep = "-" * 60
    lines = []

    lines.append(f"\n{'=' * 60}")
    lines.append(f"  WICK -- POSITION SIZE CALCULATOR")
    lines.append(f"{'=' * 60}")

    if not r.valid:
        lines.append(f"\n  ERROR: {r.error}")
        lines.append(f"{'=' * 60}\n")
        return "\n".join(lines)

    lines.append(f"\n{sep}")
    lines.append("  INPUTS")
    lines.append(sep)
    lines.append(f"  Account size:  ${r.account_size:,.2f}")
    lines.append(f"  Max risk:       {r.risk_pct}%  =  ${r.dollar_risk_allowed:,.2f}")
    lines.append(f"  Direction:      {r.direction}")
    lines.append(f"  Entry:         ${r.entry:,.2f}")
    lines.append(f"  Stop-loss:     ${r.stop:,.2f}")
    if r.target:
        lines.append(f"  Target:        ${r.target:,.2f}")

    lines.append(f"\n{sep}")
    lines.append("  RESULT")
    lines.append(sep)
    lines.append(f"  Risk per share:       ${r.risk_per_share:,.2f}  (entry - stop)")
    lines.append(f"  Shares to buy:         {r.shares}")
    lines.append(f"  Actual dollar risk:   ${r.actual_dollar_risk:,.2f}  ({r.risk_pct}% of account)")
    lines.append(f"  Total position value: ${r.total_position_value:,.2f}")

    if r.target is not None:
        lines.append(f"\n{sep}")
        lines.append("  REWARD / RISK")
        lines.append(sep)
        lines.append(f"  Reward per share: ${r.reward_per_share:,.2f}")
        lines.append(f"  Dollar reward:    ${r.dollar_reward:,.2f}")
        rr_str = f"{r.reward_risk_ratio:.1f}:1"
        ok_marker = "OK" if r.rr_ok else "BELOW 2:1 -- consider skipping"
        lines.append(f"  Reward:Risk ratio: {rr_str}  [{ok_marker}]")
        lines.append(
            "  WHY: A 2:1 reward-to-risk minimum means you only need to be right 34% "
            "of the time to break even -- it gives your losses room to lose and your "
            "wins room to win."
        )

    # Plain-English one-liner summary
    lines.append(f"\n{sep}")
    lines.append("  ONE-LINE SUMMARY")
    lines.append(sep)
    summary = (
        f"  Risk {r.risk_pct}% of ${r.account_size:,.0f} = ${r.dollar_risk_allowed:,.2f}. "
        f"Entry ${r.entry}, stop ${r.stop} -> risk ${r.risk_per_share}/share -> "
        f"buy {r.shares} shares."
    )
    if r.target and r.reward_risk_ratio:
        ok_icon = "[OK]" if r.rr_ok else "[BELOW 2:1]"
        summary += f" Target ${r.target} -> reward:risk = {r.reward_risk_ratio:.1f}:1 {ok_icon}"
    lines.append(summary)

    lines.append(f"\n{'=' * 60}")
    lines.append("  Description of past price action only. Not a prediction or financial advice.")
    lines.append(f"{'=' * 60}\n")

    return "\n".join(lines)


def _err(account_size, risk_pct, entry, stop, target, msg) -> PositionResult:
    return PositionResult(
        account_size=account_size, risk_pct=risk_pct,
        entry=entry, stop=stop, target=target,
        dollar_risk_allowed=0, risk_per_share=0, shares=0,
        actual_dollar_risk=0, total_position_value=0,
        reward_per_share=None, dollar_reward=None,
        reward_risk_ratio=None, rr_ok=None,
        direction="LONG", valid=False, error=msg,
    )

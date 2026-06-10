"""
checklist.py -- Phase 3: pre-trade discipline checklist.

Checks 4 rules before a trade. Rules 1-2 are manual yes/no answers.
Rules 3-4 auto-calculate from Phase 2 inputs when provided.
Nothing is blocked -- the tool flags, you decide.
"""

from dataclasses import dataclass, field
from typing import Optional
from risk_calculator import calculate_position, PositionResult


@dataclass
class CheckItem:
    rule: str           # short label
    description: str    # what the rule means
    passed: bool
    auto: bool          # True = calculated, False = user answered
    detail: str = ""    # extra context line (e.g. computed R:R value)


@dataclass
class ChecklistResult:
    items: list = field(default_factory=list)
    position: Optional[PositionResult] = None   # Phase 2 result if inputs were given
    all_passed: bool = False
    fail_count: int = 0


def run_checklist(
    trend_ok: bool,
    stop_set: bool,
    account: Optional[float] = None,
    entry: Optional[float] = None,
    stop: Optional[float] = None,
    target: Optional[float] = None,
    risk_pct: float = 2.0,
) -> ChecklistResult:
    """
    Evaluates all 4 rules and returns a ChecklistResult.

    Rules 3 and 4 auto-calculate if account/entry/stop/target are given.
    If not given, they cannot be auto-checked and are skipped (not failed).
    """
    items = []
    position = None

    # Rule 1: Clear trend
    items.append(CheckItem(
        rule="Clear trend",
        description="There is a clear uptrend or downtrend -- not choppy sideways action.",
        passed=trend_ok,
        auto=False,
        detail="You confirmed this manually." if trend_ok else "No clear trend identified.",
    ))

    # Rule 2: Stop-loss set
    items.append(CheckItem(
        rule="Stop-loss set",
        description="A specific stop-loss price is defined before entering the trade.",
        passed=stop_set,
        auto=False,
        detail="Stop-loss is defined." if stop_set else "No stop-loss defined -- this trade has no exit plan.",
    ))

    # Rules 3 & 4: auto-check from Phase 2 if inputs available
    can_auto = all(v is not None for v in [account, entry, stop])

    if can_auto:
        position = calculate_position(account, entry, stop, risk_pct=risk_pct, target=target)

        if position.valid:
            # Rule 3: Risk <= max %
            rule3_pass = position.actual_dollar_risk <= position.dollar_risk_allowed
            items.append(CheckItem(
                rule=f"Risk <= {risk_pct}% of account",
                description=f"Dollar risk on this trade must not exceed {risk_pct}% of your account.",
                passed=rule3_pass,
                auto=True,
                detail=(
                    f"${position.actual_dollar_risk:,.2f} risk on {position.shares} shares "
                    f"(limit: ${position.dollar_risk_allowed:,.2f})."
                ),
            ))

            # Rule 4: Reward >= 2x risk
            if target is not None and position.reward_risk_ratio is not None:
                rule4_pass = position.rr_ok
                items.append(CheckItem(
                    rule="Reward >= 2x risk",
                    description="The potential reward must be at least twice the potential loss.",
                    passed=rule4_pass,
                    auto=True,
                    detail=f"Reward:Risk = {position.reward_risk_ratio:.1f}:1 (minimum 2.0:1).",
                ))
            else:
                # No target given -- can't auto-check, skip gracefully
                items.append(CheckItem(
                    rule="Reward >= 2x risk",
                    description="The potential reward must be at least twice the potential loss.",
                    passed=True,   # cannot fail what we cannot measure
                    auto=True,
                    detail="No target provided -- reward:risk not calculated. Set a target to verify.",
                ))
        else:
            # Phase 2 returned an error -- flag it
            items.append(CheckItem(
                rule=f"Risk <= {risk_pct}% of account",
                description="Dollar risk on this trade must not exceed max %.",
                passed=False,
                auto=True,
                detail=f"Could not calculate: {position.error}",
            ))
            items.append(CheckItem(
                rule="Reward >= 2x risk",
                description="Reward must be at least twice the risk.",
                passed=False,
                auto=True,
                detail="Could not calculate (see risk error above).",
            ))
    else:
        # No numbers provided -- ask manually
        items.append(CheckItem(
            rule=f"Risk <= {risk_pct}% of account",
            description=f"Dollar risk on this trade must not exceed {risk_pct}% of your account.",
            passed=True,   # user said yes in interactive mode (checked outside)
            auto=False,
            detail="You confirmed this manually.",
        ))
        items.append(CheckItem(
            rule="Reward >= 2x risk",
            description="The potential reward must be at least twice the potential loss.",
            passed=True,
            auto=False,
            detail="You confirmed this manually.",
        ))

    fail_count = sum(1 for i in items if not i.passed)
    all_passed = fail_count == 0

    return ChecklistResult(
        items=items,
        position=position,
        all_passed=all_passed,
        fail_count=fail_count,
    )


def format_checklist(r: ChecklistResult) -> str:
    sep = "-" * 60
    lines = []

    lines.append(f"\n{'=' * 60}")
    lines.append("  WICK -- PRE-TRADE CHECKLIST")
    lines.append(f"{'=' * 60}")

    for i, item in enumerate(r.items, 1):
        status = "[PASS]" if item.passed else "[FAIL]"
        auto_tag = " (auto)" if item.auto else ""
        lines.append(f"\n  {status}  Rule {i}: {item.rule}{auto_tag}")
        lines.append(f"         {item.description}")
        if item.detail:
            lines.append(f"         -> {item.detail}")

    lines.append(f"\n{sep}")
    if r.all_passed:
        lines.append("  [ALL RULES SATISFIED] -- Proceed with discipline.")
    else:
        fails = [item.rule for item in r.items if not item.passed]
        lines.append(f"  [!] This trade breaks your rules -- reconsider.")
        lines.append(f"      Failed: {', '.join(fails)}")

    # If Phase 2 was run, show the one-liner
    if r.position and r.position.valid:
        lines.append(f"\n{sep}")
        lines.append("  POSITION SIZE (from Phase 2)")
        lines.append(sep)
        p = r.position
        summary = (
            f"  Buy {p.shares} shares @ ${p.entry} | "
            f"stop ${p.stop} | risk ${p.actual_dollar_risk:,.2f}"
        )
        if p.target and p.reward_risk_ratio:
            summary += f" | target ${p.target} | R:R {p.reward_risk_ratio:.1f}:1"
        lines.append(summary)

    lines.append(f"\n{'=' * 60}")
    lines.append("  Description of past price action only. Not a prediction or financial advice.")
    lines.append(f"{'=' * 60}\n")

    return "\n".join(lines)

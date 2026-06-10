"""
analyzer.py -- Phase 1 chart translation logic.

Each function receives the full OHLCV DataFrame (all history needed for MAs),
plus a `window` int = number of *trading* days to analyze for trend/S&R/volume.
"""

import pandas as pd
import numpy as np


# ----------------------------------------------
# Helpers
# ----------------------------------------------

def _swing_highs(series: pd.Series, order: int = 5) -> list:
    """Local maxima: a bar is a swing high if it's the highest in +/-order bars."""
    highs = []
    vals = series.values
    for i in range(order, len(vals) - order):
        window = vals[i - order: i + order + 1]
        if vals[i] == max(window):
            highs.append((series.index[i], vals[i]))
    return highs


def _swing_lows(series: pd.Series, order: int = 5) -> list:
    """Local minima: a bar is a swing low if it's the lowest in +/-order bars."""
    lows = []
    vals = series.values
    for i in range(order, len(vals) - order):
        window = vals[i - order: i + order + 1]
        if vals[i] == min(window):
            lows.append((series.index[i], vals[i]))
    return lows


def _rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 1)


def _cluster_levels(prices: list, tolerance_pct: float = 0.015) -> list:
    """
    Group nearby price levels into clusters.
    Returns list of {'price': float, 'touches': int} sorted by touches desc.
    """
    if not prices:
        return []
    prices_sorted = sorted(prices)
    clusters = []
    used = [False] * len(prices_sorted)
    for i, p in enumerate(prices_sorted):
        if used[i]:
            continue
        group = [p]
        used[i] = True
        for j in range(i + 1, len(prices_sorted)):
            if not used[j] and abs(prices_sorted[j] - p) / p <= tolerance_pct:
                group.append(prices_sorted[j])
                used[j] = True
        clusters.append({"price": round(np.mean(group), 2), "touches": len(group)})
    return sorted(clusters, key=lambda x: x["touches"], reverse=True)


# ----------------------------------------------
# Phase 1 analysis functions
# ----------------------------------------------

def analyze_trend(df: pd.DataFrame, window: int) -> dict:
    """
    Determines trend by comparing the sequence of swing highs and lows
    over the analysis window.
    """
    recent = df.tail(window)
    highs = _swing_highs(recent["High"], order=4)
    lows = _swing_lows(recent["Low"], order=4)

    if len(highs) < 2 or len(lows) < 2:
        direction = "SIDEWAYS"
        reasoning = "not enough swing points to establish a clear sequence of highs and lows"
    else:
        h_vals = [h[1] for h in highs]
        l_vals = [l[1] for l in lows]

        hh = all(h_vals[i] < h_vals[i + 1] for i in range(len(h_vals) - 1))
        hl = all(l_vals[i] < l_vals[i + 1] for i in range(len(l_vals) - 1))
        lh = all(h_vals[i] > h_vals[i + 1] for i in range(len(h_vals) - 1))
        ll = all(l_vals[i] > l_vals[i + 1] for i in range(len(l_vals) - 1))

        if hh and hl:
            direction = "UPTREND"
            reasoning = "each pullback has bottomed higher than the last, and each rally has reached a higher peak"
        elif lh and ll:
            direction = "DOWNTREND"
            reasoning = "each bounce has topped lower than the last, and each sell-off has dropped to a lower low"
        elif hh:
            direction = "WEAK UPTREND"
            reasoning = "rally peaks are rising but the pullback lows are not consistently higher -- buyers are gaining ground but unevenly"
        elif ll:
            direction = "WEAK DOWNTREND"
            reasoning = "sell-off lows are falling but the bounce highs are not consistently lower -- sellers are gaining ground but unevenly"
        else:
            direction = "SIDEWAYS"
            reasoning = "highs and lows are not making a consistent sequence in either direction -- price is ranging"

    lookback_label = f"{window // 21} month{'s' if window // 21 != 1 else ''}"
    return {
        "direction": direction,
        "reasoning": reasoning,
        "lookback_label": lookback_label,
        "swing_highs": highs,
        "swing_lows": lows,
    }


def analyze_support_resistance(df: pd.DataFrame, window: int) -> dict:
    """
    Identifies 2-3 key support and resistance levels using recent swing highs/lows.
    """
    recent = df.tail(window)
    current_price = float(df["Close"].iloc[-1])

    highs = _swing_highs(recent["High"], order=3)
    lows = _swing_lows(recent["Low"], order=3)

    high_prices = [h[1] for h in highs]
    low_prices = [l[1] for l in lows]

    high_clusters = _cluster_levels(high_prices)
    low_clusters = _cluster_levels(low_prices)

    resistance = [c for c in high_clusters if c["price"] > current_price * 1.005][:3]
    support = [c for c in low_clusters if c["price"] < current_price * 0.995][:3]

    nearest_resistance = resistance[0] if resistance else None
    nearest_support = support[0] if support else None

    return {
        "current_price": round(current_price, 2),
        "resistance": resistance,
        "support": support,
        "nearest_resistance": nearest_resistance,
        "nearest_support": nearest_support,
    }


def analyze_moving_averages(df: pd.DataFrame) -> dict:
    """Computes 50-day and 200-day simple moving averages."""
    close = df["Close"]
    current = float(close.iloc[-1])

    ma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
    ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None

    above_50 = (current > ma50) if ma50 else None
    above_200 = (current > ma200) if ma200 else None
    golden_cross = (ma50 > ma200) if (ma50 and ma200) else None

    return {
        "current": round(current, 2),
        "ma50": round(ma50, 2) if ma50 else None,
        "ma200": round(ma200, 2) if ma200 else None,
        "above_50": above_50,
        "above_200": above_200,
        "golden_cross": golden_cross,
    }


def analyze_momentum(df: pd.DataFrame) -> dict:
    """RSI 14-period."""
    rsi_val = _rsi(df["Close"], 14)

    if rsi_val < 30:
        label = "OVERSOLD"
        explanation = "the stock has fallen sharply and may be due for at least a short-term bounce"
    elif rsi_val > 70:
        label = "OVERBOUGHT"
        explanation = "it has run hot recently and may need to cool off or consolidate before the next move"
    else:
        label = "NEUTRAL"
        explanation = "momentum is neither stretched to the upside nor beaten down -- it is in the middle ground"

    return {"rsi": rsi_val, "label": label, "explanation": explanation}


def analyze_volume(df: pd.DataFrame, window: int) -> dict:
    """Is volume rising or falling? Is it heavier on up-days or down-days?"""
    recent = df.tail(window).copy()
    recent["up_day"] = recent["Close"] > recent["Open"]

    half = window // 2
    first_half_vol = recent["Volume"].iloc[:half].mean()
    second_half_vol = recent["Volume"].iloc[half:].mean()
    vol_trend = "RISING" if second_half_vol > first_half_vol * 1.05 else (
        "FALLING" if second_half_vol < first_half_vol * 0.95 else "FLAT"
    )

    up_vol = recent.loc[recent["up_day"], "Volume"].mean()
    down_vol = recent.loc[~recent["up_day"], "Volume"].mean()

    if pd.isna(up_vol):
        up_vol = 0.0
    if pd.isna(down_vol):
        down_vol = 0.0

    if up_vol > down_vol * 1.1:
        conviction = "BUYER"
        conviction_text = "volume is heavier on up-days than down-days -- buyers are showing conviction"
    elif down_vol > up_vol * 1.1:
        conviction = "SELLER"
        conviction_text = "volume is heavier on down-days than up-days -- sellers are showing conviction"
    else:
        conviction = "NEUTRAL"
        conviction_text = "up-day and down-day volume are roughly equal -- no clear directional conviction"

    return {
        "trend": vol_trend,
        "conviction": conviction,
        "conviction_text": conviction_text,
        "avg_up_vol": int(up_vol),
        "avg_down_vol": int(down_vol),
    }


# ----------------------------------------------
# Master readout builder
# ----------------------------------------------

def build_readout(ticker: str, df: pd.DataFrame, window: int = 63) -> str:
    """
    Assembles the full plain-English Phase 1 readout.
    window defaults to ~3 months of trading days (63).
    """
    ticker = ticker.upper()
    trend = analyze_trend(df, window)
    sr = analyze_support_resistance(df, window)
    ma = analyze_moving_averages(df)
    mom = analyze_momentum(df)
    vol = analyze_volume(df, window)

    lines = []
    sep = "-" * 60

    lines.append(f"\n{'=' * 60}")
    lines.append(f"  WICK -- {ticker}   (as of {df.index[-1].strftime('%Y-%m-%d')})")
    lines.append(f"{'=' * 60}")

    # 1. TREND
    lines.append(f"\n{sep}")
    lines.append("  TREND")
    lines.append(sep)
    lines.append(f"  {trend['direction']} over the past {trend['lookback_label']}.")
    lines.append(f"  WHY: I called it {trend['direction'].lower()} because {trend['reasoning']}.")

    # 2. SUPPORT & RESISTANCE
    lines.append(f"\n{sep}")
    lines.append("  SUPPORT & RESISTANCE")
    lines.append(sep)
    lines.append(f"  Current price: ${sr['current_price']}")

    if sr["resistance"]:
        res_parts = [f"${r['price']} (tagged {r['touches']}x)" for r in sr["resistance"]]
        lines.append(f"  Resistance: {', '.join(res_parts)}")
    else:
        lines.append("  Resistance: no clear levels above current price in this window")

    if sr["support"]:
        sup_parts = [f"${s['price']} (tagged {s['touches']}x)" for s in sr["support"]]
        lines.append(f"  Support:    {', '.join(sup_parts)}")
    else:
        lines.append("  Support: no clear levels below current price in this window")

    lines.append(
        "  WHY: I found these levels by clustering the swing highs (peaks where price "
        "reversed down) and swing lows (troughs where price reversed up) -- price has "
        "memory at these spots."
    )

    # 3. MOVING AVERAGES
    lines.append(f"\n{sep}")
    lines.append("  MOVING AVERAGES")
    lines.append(sep)

    if ma["ma50"] and ma["ma200"]:
        cross_label = (
            "GOLDEN CROSS territory (50-day above 200-day -- broadly bullish structure)"
            if ma["golden_cross"] else
            "DEATH CROSS territory (50-day below 200-day -- broadly bearish structure)"
        )
        lines.append(f"  50-day MA:  ${ma['ma50']}  ->  price is {'ABOVE' if ma['above_50'] else 'BELOW'} it")
        lines.append(f"  200-day MA: ${ma['ma200']}  ->  price is {'ABOVE' if ma['above_200'] else 'BELOW'} it")
        lines.append(f"  Cross status: {cross_label}")
        lines.append(
            "  WHY: Moving averages smooth out daily noise. When price is above its "
            "50-day average, the near-term trend is generally up. The 200-day average "
            "is the institutional benchmark -- above it = long-term health."
        )
    elif ma["ma50"]:
        lines.append(f"  50-day MA: ${ma['ma50']}  ->  price is {'ABOVE' if ma['above_50'] else 'BELOW'} it")
        lines.append("  200-day MA: not enough history to compute.")
    else:
        lines.append("  Not enough history to compute moving averages.")

    # 4. MOMENTUM (RSI)
    lines.append(f"\n{sep}")
    lines.append("  MOMENTUM -- RSI (14-period)")
    lines.append(sep)
    lines.append(f"  RSI = {mom['rsi']}  ->  {mom['label']}")
    lines.append(
        f"  WHY: RSI measures how fast price has moved relative to its recent range. "
        f"A reading of {mom['rsi']} means {mom['explanation']}. "
        f"Below 30 = oversold. 30-70 = neutral. Above 70 = overbought."
    )

    # 5. VOLUME
    lines.append(f"\n{sep}")
    lines.append("  VOLUME")
    lines.append(sep)
    lines.append(f"  Volume trend: {vol['trend']} over the analysis window.")
    lines.append(f"  Conviction:   {vol['conviction_text'].capitalize()}.")
    lines.append(
        "  WHY: Volume is the 'votes' behind a price move. Rising price on rising "
        "volume = real buying pressure. Rising price on falling volume = caution, "
        "the move may lack follow-through."
    )

    # 6. PLAIN-ENGLISH SUMMARY
    lines.append(f"\n{sep}")
    lines.append("  PLAIN-ENGLISH SUMMARY")
    lines.append(sep)
    summary = _build_summary(ticker, trend, sr, ma, mom, vol)
    for sentence in summary:
        lines.append(f"  {sentence}")

    # DISCLAIMER
    lines.append(f"\n{'=' * 60}")
    lines.append(
        "  Description of past price action only."
        " Not a prediction or financial advice."
    )
    lines.append(f"{'=' * 60}\n")

    return "\n".join(lines)


def _build_summary(ticker, trend, sr, ma, mom, vol) -> list:
    sentences = []

    direction_plain = {
        "UPTREND": "in an uptrend",
        "DOWNTREND": "in a downtrend",
        "WEAK UPTREND": "in a weak uptrend",
        "WEAK DOWNTREND": "in a weak downtrend",
        "SIDEWAYS": "moving sideways",
    }.get(trend["direction"], trend["direction"].lower())
    sentences.append(
        f"{ticker} is {direction_plain} over the past {trend['lookback_label']}, "
        f"meaning {trend['reasoning']}."
    )

    if ma["ma50"] and ma["ma200"]:
        sentences.append(
            f"Price is {'above' if ma['above_50'] else 'below'} its 50-day average "
            f"and {'above' if ma['above_200'] else 'below'} the 200-day -- "
            f"{'the broader structure is bullish' if ma['golden_cross'] else 'the broader structure is bearish'}."
        )

    rsi_plain = f"RSI at {mom['rsi']} ({mom['label'].lower()})"
    vol_plain = f"volume is {vol['trend'].lower()} and {vol['conviction'].lower()} conviction"
    sentences.append(f"{rsi_plain}, with {vol_plain}.")

    near_res = sr.get("nearest_resistance")
    near_sup = sr.get("nearest_support")
    if near_res and near_sup:
        sentences.append(
            f"Key levels to watch: resistance near ${near_res['price']} "
            f"and support near ${near_sup['price']}."
        )
    elif near_res:
        sentences.append(f"Key resistance to watch: ${near_res['price']}.")
    elif near_sup:
        sentences.append(f"Key support to watch: ${near_sup['price']}.")

    return sentences

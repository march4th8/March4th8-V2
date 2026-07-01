"""
app.py -- Streamlit dashboard wrapping Phases 1-4.
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date

from data_source import fetch_ohlcv
from analyzer import (
    build_readout,
    analyze_trend,
    analyze_support_resistance,
    analyze_moving_averages,
    analyze_momentum,
    analyze_volume,
)
from risk_calculator import calculate_position, format_result
from checklist import run_checklist, format_checklist
from journal import (
    init_db, log_trade, close_trade, get_all_trades, get_stats, get_trade,
)

# -- App config --------------------------------------------

st.set_page_config(
    page_title="Wick by Sharpe",
    page_icon="W",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()

# -- Global style ------------------------------------------

st.markdown("""
<style>

/* ── Layout ─────────────────────────────── */
.block-container { padding-top: 0.75rem; padding-bottom: 2rem; }

/* ── Metric cards ───────────────────────── */
[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 1rem 1.25rem;
}
[data-testid="metric-container"]:hover { border-color: #00bfa5; transition: border-color 0.2s; }
[data-testid="stMetricLabel"] p {
    font-size: 0.7rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6e7681 !important;
    font-weight: 600;
}
[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    font-weight: 700 !important;
}

/* ── Tabs ────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background-color: #161b22;
    border-radius: 8px;
    padding: 4px 6px;
    gap: 2px;
    border: 1px solid #21262d;
}
.stTabs [data-baseweb="tab"] {
    font-size: 0.875rem;
    font-weight: 600;
    color: #8b949e;
    border-radius: 6px;
    padding: 6px 14px;
    letter-spacing: 0.01em;
}
.stTabs [aria-selected="true"] {
    color: #00bfa5 !important;
    background-color: #0e1117 !important;
}

/* ── Primary buttons ─────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00bfa5 0%, #00897b 100%) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    border-radius: 7px !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1de9b6 0%, #00bfa5 100%) !important;
}

/* ── Forms ───────────────────────────────── */
[data-testid="stForm"] {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 1.25rem !important;
}

/* ── Expanders ───────────────────────────── */
[data-testid="stExpander"] {
    background: #161b22;
    border: 1px solid #21262d !important;
    border-radius: 8px;
}

/* ── Checklist rule cards ────────────────── */
.check-pass {
    background: #0d2118;
    border: 1px solid #1b4332;
    border-left: 3px solid #00bfa5;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin: 0.35rem 0;
}
.check-fail {
    background: #1f0d0d;
    border: 1px solid #431b1b;
    border-left: 3px solid #ef5350;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin: 0.35rem 0;
}

/* ── Disclaimer ──────────────────────────── */
.disclaimer {
    font-size: 0.7rem;
    color: #484f58;
    border-top: 1px solid #21262d;
    margin-top: 2rem;
    padding-top: 0.75rem;
    text-align: center;
    letter-spacing: 0.03em;
}

</style>
""", unsafe_allow_html=True)

# -- Branded header ----------------------------------------
st.markdown("""
<div style="padding: 0.25rem 0 0.5rem 0; margin-bottom: 0.25rem;">
    <span style="font-size:2rem;font-weight:800;color:#e6edf3;letter-spacing:-0.03em;line-height:1">WICK</span>
    <span style="font-size:1rem;font-weight:600;color:#00bfa5;letter-spacing:0.06em;margin-left:0.5rem">by Sharpe</span>
    <p style="font-size:0.78rem;color:#484f58;margin:0.2rem 0 0 0;letter-spacing:0.02em">
        Personal Trading Assistant &nbsp;&middot;&nbsp; Describes the past. Explains the reasoning. Never predicts.
    </p>
</div>
""", unsafe_allow_html=True)

tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "How to Use",
    "Chart Translator",
    "Position Calculator",
    "Pre-Trade Checklist",
    "Trade Journal",
])


# ==========================================================
# ======================================================
# TAB 0 -- How to Use
# ======================================================

with tab0:
    st.subheader("What is Wick by Sharpe?")
    st.markdown("""
Wick by Sharpe is a **chart translator** that sits in a browser tab next to your thinkorswim (or Webull) chart.

You type a ticker. It reads the chart data and explains in plain English what actually happened —
trend direction, key price levels, moving averages, momentum, and volume.
It never predicts the future or tells you to buy or sell. It describes the past and explains *why*,
so you can train your eyes to read charts yourself.
""")

    st.divider()

    # -- Workflow --
    st.subheader("The Workflow (do this every time)")
    st.markdown("""
1. **Open thinkorswim** with your live chart on one side of the screen.
2. **Open Wick by Sharpe** (`http://localhost:8501`) on the other side.
3. Go to **Chart Translator**, type the ticker, hit Analyze.
4. Read the output. Then look at your live chart and **verify each point** with your own eyes.
   - Is the trend line correct?
   - Do those S/R levels line up with obvious bounce/rejection zones on the chart?
   - Does the RSI match the RSI indicator in thinkorswim?
5. If you're considering a trade, go through the tabs in order:
   **Position Calculator** → **Pre-Trade Checklist** → **Trade Journal**.

The goal: after a few weeks of doing this, you won't need the tool anymore — you'll just *see* it.
""")

    st.divider()

    # -- Tab-by-tab guide --
    st.subheader("Tab Guide")

    with st.expander("Chart Translator  (start here)", expanded=True):
        st.markdown("""
**What it does:** Pulls 3 months of daily price data and translates the chart into plain English.

**How to use it:**
1. Type a ticker in the **Ticker** box (e.g. `AAPL`, `TSLA`, `SPY`).
2. Choose a **Lookback** window:
   - `1m` = 1 month — good for short-term setups
   - `3m` = 3 months (default) — best starting point
   - `6m` = 6 months — see the bigger picture
   - `1y` = 1 year — long-term structure
3. Click **Analyze**.

**Reading the chart:**
- **Green candles** = price closed higher than it opened that day. **Red candles** = closed lower.
- **Blue line** = 50-day moving average. **Orange line** = 200-day moving average.
- **Green dashed lines** = support levels (price bounced up from here). **Red dashed lines** = resistance (price got rejected here).
- **Bottom panel (Volume):** green bar = up day, red bar = down day.
- **Bottom panel (RSI):** above 70 = overbought (hot). Below 30 = oversold (beaten down). Middle = neutral.

**The metric cards** (Price / 50-day MA / 200-day MA / RSI / Trend) give you the key numbers at a glance — compare these directly to the indicators on your thinkorswim chart to verify accuracy.

**"Full analysis readout"** — click to expand for the complete plain-English breakdown with teaching notes explaining *why* each call was made.
""")

    with st.expander("Position Calculator  (how many shares to buy)"):
        st.markdown("""
**What it does:** Calculates the exact number of shares so that if the trade hits your stop-loss,
you lose exactly your chosen % of your account — no more.

**How to use it:**
1. **Account size** — your total trading account in dollars.
2. **Entry price** — the price you plan to buy at.
3. **Stop-loss** — the price where you exit if you're wrong. *Must be below entry for a long trade.*
4. **Profit target** — where you plan to take profit (optional, but needed for R:R ratio).
5. **Max risk %** — default is 2%. This means on any single trade you risk at most 2% of your account.

**Reading the result:**
- **Shares** — buy exactly this many.
- **Dollar Risk** — if your stop gets hit, this is your max loss.
- **Position Value** — total cost to enter the trade (shares x entry price).
- **Reward:Risk** — should be at least **2.0:1**. If it shows "Below 2:1", the trade is not worth taking by the rules.

**Example:** $10,000 account, 2% risk, entry $150, stop $145, target $165
→ risk $200, buy 40 shares, R:R = 3:1 (good).
""")

    with st.expander("Pre-Trade Checklist  (discipline enforcer)"):
        st.markdown("""
**What it does:** Runs you through 4 rules before every trade. It does not block you — it forces you to *see* when you're about to break your own rules.

**The 4 rules:**
1. **Clear trend** — Is the stock in a clear up or downtrend? If it's choppy sideways, skip the trade.
2. **Stop-loss set** — Do you have a specific exit price if you're wrong?
3. **Risk <= 2%** — Are you risking 2% of your account or less? (Auto-calculated if you fill in numbers.)
4. **Reward >= 2x risk** — Is the potential profit at least twice the potential loss? (Auto-calculated.)

**How to use it:**
- Check the first two boxes manually (your judgment call).
- Fill in the numbers (account / entry / stop / target) to have rules 3 and 4 checked automatically.
- If any rule fails, you'll see a red warning. You can still take the trade — but you'll know you're breaking your rules.

**Pro tip:** Run the Position Calculator first, then come here — the same numbers apply to both.
""")

    with st.expander("Trade Journal  (your feedback loop)"):
        st.markdown("""
**What it does:** Keeps a permanent record of every trade so you can see the truth about your own trading patterns over time.

**The 4 sub-tabs inside Trade Journal:**

**Log Trade** — record a trade when you enter it.
- Fill in ticker, direction (long/short), entry, stop, target, shares, reason/setup tag, and whether you ran the checklist.
- If you already know the exit (you're logging a closed trade), set the result and exit price.
- If it's still open, leave Result as **OPEN** — close it later.

**Close Trade** — when an open trade finishes.
- Pick the open trade from the dropdown.
- Enter your exit price.
- Wick calculates P&L and marks it WIN / LOSS / BREAKEVEN automatically.

**History** — a full table of all your trades plus a P&L bar chart.

**Statistics** — the numbers that matter:
- **Win Rate** — what % of your closed trades were winners.
- **Avg Win / Avg Loss** — are your wins bigger than your losses? They should be.
- **Total P&L** — your total realized profit/loss in dollars.
- **Expectancy** — the average dollar amount you make per trade. Positive = your system works. Negative = it doesn't.
- **Discipline Score** — the % of trades where you ran and passed the pre-trade checklist. Low score = you're trading on impulse.
- **Best / Worst Setups** — which reason tags (e.g. "breakout", "MA bounce") made you the most vs least money. This tells you which setups to focus on and which to avoid.
""")

    st.divider()

    # -- Quick reference --
    st.subheader("Quick Reference — CLI commands (optional)")
    st.markdown("""
If you prefer the terminal over the browser, everything works from the command line too:
```
python cli.py AAPL 3m          # Chart analysis
python cli.py calc              # Position calculator (interactive prompts)
python cli.py check             # Pre-trade checklist (interactive prompts)
python cli.py log               # Log a trade
python cli.py trades            # Show all trades
python cli.py stats             # Show statistics
python cli.py close 3 148.50   # Close trade #3 at exit price 148.50
```
""")

    st.markdown('<p class="disclaimer">Description of past price action only. Not a prediction or financial advice.</p>', unsafe_allow_html=True)


# TAB 1 -- Chart Translator
# ==========================================================

def _compute_rsi_series(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _build_chart(df: pd.DataFrame, window: int, ticker: str) -> go.Figure:
    """
    Builds a 3-panel plotly chart: candlesticks + MAs + S/R, volume, RSI.
    df is the full history; we display only the last `window` bars.
    """
    df = df.copy()
    df["MA50"]  = df["Close"].rolling(50).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    df["RSI"]   = _compute_rsi_series(df["Close"])
    df["up_day"] = df["Close"] >= df["Open"]

    display = df.tail(window)

    # S/R levels from analyzer
    sr = analyze_support_resistance(df, window)

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6, 0.18, 0.22],
    )

    # -- Candlesticks --
    fig.add_trace(go.Candlestick(
        x=display.index,
        open=display["Open"],
        high=display["High"],
        low=display["Low"],
        close=display["Close"],
        name="Price",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
        increasing_fillcolor="#26a69a",
        decreasing_fillcolor="#ef5350",
        line=dict(width=1),
    ), row=1, col=1)

    # -- MAs --
    if display["MA50"].notna().any():
        fig.add_trace(go.Scatter(
            x=display.index, y=display["MA50"],
            name="50-day MA", line=dict(color="#2196F3", width=1.5),
        ), row=1, col=1)

    if display["MA200"].notna().any():
        fig.add_trace(go.Scatter(
            x=display.index, y=display["MA200"],
            name="200-day MA", line=dict(color="#FF9800", width=1.5),
        ), row=1, col=1)

    # -- Support levels (green dashed) --
    for sup in sr["support"][:2]:
        fig.add_hline(
            y=sup["price"], line_dash="dash", line_color="#26a69a",
            line_width=1, opacity=0.7, row=1, col=1,
            annotation_text=f"S ${sup['price']}",
            annotation_position="right",
            annotation_font_color="#26a69a",
        )

    # -- Resistance levels (red dashed) --
    for res in sr["resistance"][:2]:
        fig.add_hline(
            y=res["price"], line_dash="dash", line_color="#ef5350",
            line_width=1, opacity=0.7, row=1, col=1,
            annotation_text=f"R ${res['price']}",
            annotation_position="right",
            annotation_font_color="#ef5350",
        )

    # -- Volume bars --
    vol_colors = [
        "#26a69a" if up else "#ef5350"
        for up in display["up_day"]
    ]
    fig.add_trace(go.Bar(
        x=display.index, y=display["Volume"],
        name="Volume", marker_color=vol_colors, showlegend=False,
    ), row=2, col=1)

    # -- RSI --
    fig.add_trace(go.Scatter(
        x=display.index, y=display["RSI"],
        name="RSI (14)", line=dict(color="#9c27b0", width=1.5),
    ), row=3, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="#ef5350",
                  line_width=1, opacity=0.5, row=3, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="#26a69a",
                  line_width=1, opacity=0.5, row=3, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="gray", opacity=0.04,
                  layer="below", row=3, col=1)

    # -- Layout --
    fig.update_layout(
        title=dict(text=f"{ticker}  --  last {window // 21}mo", font=dict(size=16)),
        height=700,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        margin=dict(l=60, r=80, t=60, b=20),
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#fafafa"),
    )
    fig.update_yaxes(showgrid=True, gridcolor="#1e2130", tickprefix="$", row=1, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="#1e2130", row=2, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="#1e2130",
                     range=[0, 100], tickvals=[30, 50, 70], row=3, col=1)
    fig.update_xaxes(showgrid=False, rangeslider_visible=False)

    return fig


with tab1:
    col_in, col_gap = st.columns([3, 1])
    with col_in:
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            ticker_input = st.text_input("Ticker", value="AAPL", key="t1_ticker").strip().upper()
        with c2:
            window_choice = st.selectbox(
                "Lookback", ["1m", "3m", "6m", "1y"], index=1, key="t1_window"
            )
        with c3:
            st.write("")
            st.write("")
            analyze_btn = st.button("Analyze", type="primary", key="t1_analyze")

    if analyze_btn:
        window_map = {"1m": 21, "3m": 63, "6m": 126, "1y": 252}
        window = window_map[window_choice]

        with st.spinner(f"Fetching data for {ticker_input}..."):
            try:
                df = fetch_ohlcv(ticker_input, lookback_days=window + 250)
                st.session_state["_t1_df"]     = df
                st.session_state["_t1_window"] = window
                st.session_state["_t1_sym"]    = ticker_input
                st.session_state["_t1_error"]  = None
            except ValueError as e:
                st.session_state["_t1_error"] = str(e)
                st.session_state["_t1_df"]    = None

    if st.session_state.get("_t1_error"):
        st.error(st.session_state["_t1_error"])

    elif st.session_state.get("_t1_df") is not None:
        df     = st.session_state["_t1_df"]
        window = st.session_state["_t1_window"]
        sym    = st.session_state["_t1_sym"]

        # Chart
        fig = _build_chart(df, window, sym)
        st.plotly_chart(fig, use_container_width=True)

        # Analysis panels
        trend = analyze_trend(df, window)
        sr    = analyze_support_resistance(df, window)
        ma    = analyze_moving_averages(df)
        mom   = analyze_momentum(df)
        vol   = analyze_volume(df, window)

        # Metric row
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Price",  f"${sr['current_price']}")
        m2.metric("50-day MA", f"${ma['ma50']}" if ma["ma50"] else "N/A",
                  delta="above" if ma.get("above_50") else "below",
                  delta_color="normal" if ma.get("above_50") else "inverse")
        m3.metric("200-day MA", f"${ma['ma200']}" if ma["ma200"] else "N/A",
                  delta="above" if ma.get("above_200") else "below",
                  delta_color="normal" if ma.get("above_200") else "inverse")
        m4.metric("RSI (14)", f"{mom['rsi']}",
                  delta=mom["label"],
                  delta_color="off")
        m5.metric("Trend", trend["direction"])

        # Full text readout (collapsed by default)
        with st.expander("Full analysis readout (plain English)", expanded=False):
            readout = build_readout(sym, df, window)
            st.code(readout, language=None)

        st.markdown('<p class="disclaimer">Description of past price action only. Not a prediction or financial advice.</p>', unsafe_allow_html=True)

    else:
        st.info("Enter a ticker and click Analyze.")


# ==========================================================
# TAB 2 -- Position Calculator
# ==========================================================

with tab2:
    st.subheader("Position Size & Risk Calculator")
    st.caption("How many shares to buy so a loss at your stop equals exactly your max risk %.")

    with st.form("calc_form"):
        c1, c2 = st.columns(2)
        with c1:
            p2_account = st.number_input("Account size ($)", min_value=0.0, value=10000.0, step=100.0)
            p2_entry   = st.number_input("Entry price ($)",  min_value=0.01, value=150.0,  step=0.01)
            p2_stop    = st.number_input("Stop-loss price ($)", min_value=0.01, value=145.0, step=0.01)
        with c2:
            p2_target  = st.number_input("Profit target ($) [0 = skip]", min_value=0.0, value=0.0, step=0.01)
            p2_risk    = st.number_input("Max risk % of account", min_value=0.1, max_value=100.0, value=2.0, step=0.1)
        submitted = st.form_submit_button("Calculate", type="primary")

    if submitted:
        target = p2_target if p2_target > 0 else None
        result = calculate_position(p2_account, p2_entry, p2_stop, risk_pct=p2_risk, target=target)
        st.session_state["p2_result"] = result

    if st.session_state.get("p2_result"):
        r = st.session_state["p2_result"]
        if not r.valid:
            st.error(f"Error: {r.error}")
        else:
            st.success(f"**Buy {r.shares} shares** -- risking ${r.actual_dollar_risk:,.2f} ({p2_risk}% of account)")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Shares",         r.shares)
            m2.metric("Dollar Risk",    f"${r.actual_dollar_risk:,.2f}")
            m3.metric("Position Value", f"${r.total_position_value:,.2f}")
            if r.reward_risk_ratio:
                color = "normal" if r.rr_ok else "inverse"
                m4.metric("Reward:Risk", f"{r.reward_risk_ratio:.1f}:1",
                          delta="OK" if r.rr_ok else "Below 2:1", delta_color=color)
            else:
                m4.metric("Reward:Risk", "--")

            with st.expander("Full breakdown"):
                st.code(format_result(r), language=None)

    st.markdown('<p class="disclaimer">Description of past price action only. Not a prediction or financial advice.</p>', unsafe_allow_html=True)


# ==========================================================
# TAB 3 -- Pre-Trade Checklist
# ==========================================================

with tab3:
    st.subheader("Pre-Trade Checklist")
    st.caption("Run this before every trade. It does not block you -- it makes you see what you're doing.")

    with st.form("checklist_form"):
        st.markdown("**Manual questions**")
        p3_trend = st.checkbox("There is a clear trend (uptrend or downtrend, not choppy sideways)")
        p3_stop  = st.checkbox("I have a specific stop-loss price defined before entering")

        st.markdown("**Auto-check (fill in to calculate rules 3 & 4 automatically)**")
        c1, c2, c3 = st.columns(3)
        with c1:
            p3_account = st.number_input("Account ($) [0 = skip]", min_value=0.0, value=0.0, step=100.0, key="p3_acc")
            p3_entry   = st.number_input("Entry ($)",   min_value=0.0, value=0.0, step=0.01,  key="p3_ent")
        with c2:
            p3_stop_px = st.number_input("Stop ($)",    min_value=0.0, value=0.0, step=0.01,  key="p3_stp")
            p3_target  = st.number_input("Target ($) [0 = skip]", min_value=0.0, value=0.0, step=0.01, key="p3_tgt")
        with c3:
            p3_risk    = st.number_input("Max risk %",  min_value=0.1, value=2.0, step=0.1,   key="p3_rsk")

        p3_submit = st.form_submit_button("Run Checklist", type="primary")

    if p3_submit:
        can_auto = p3_account > 0 and p3_entry > 0 and p3_stop_px > 0
        target = p3_target if p3_target > 0 else None
        result = run_checklist(
            p3_trend, p3_stop,
            p3_account if can_auto else None,
            p3_entry   if can_auto else None,
            p3_stop_px if can_auto else None,
            target     if can_auto else None,
            p3_risk,
        )
        st.session_state["p3_result"] = result

    if st.session_state.get("p3_result"):
        r = st.session_state["p3_result"]
        if r.all_passed:
            st.success("All rules satisfied -- proceed with discipline.")
        else:
            fails = [item.rule for item in r.items if not item.passed]
            st.error(f"This trade breaks your rules -- reconsider.  Failed: {', '.join(fails)}")

        for item in r.items:
            card = "check-pass" if item.passed else "check-fail"
            badge = "PASS" if item.passed else "FAIL"
            bcol  = "#00bfa5" if item.passed else "#ef5350"
            auto  = "<span style='font-size:0.7rem;color:#484f58;margin-left:6px'>(auto)</span>" if item.auto else ""
            st.markdown(
                f'<div class="{card}">'
                f'<span style="color:{bcol};font-weight:700;font-size:0.78rem;letter-spacing:0.06em">{badge}</span>'
                f'&nbsp;&nbsp;<strong style="color:#e6edf3;font-size:0.9rem">{item.rule}</strong>{auto}<br>'
                f'<span style="color:#6e7681;font-size:0.8rem">{item.description}</span><br>'
                f'<span style="color:#484f58;font-size:0.78rem">&#8627; {item.detail}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        if r.position and r.position.valid:
            p = r.position
            st.info(
                f"Position: **{p.shares} shares** @ ${p.entry} | "
                f"stop ${p.stop} | risk ${p.actual_dollar_risk:,.2f}"
                + (f" | target ${p.target} | R:R {p.reward_risk_ratio:.1f}:1" if p.target else "")
            )

    st.markdown('<p class="disclaimer">Description of past price action only. Not a prediction or financial advice.</p>', unsafe_allow_html=True)


# ==========================================================
# TAB 4 -- Trade Journal
# ==========================================================

with tab4:
    j_tab_log, j_tab_close, j_tab_history, j_tab_stats = st.tabs([
        "Log Trade", "Close Trade", "History", "Statistics"
    ])

    # -- Log a Trade --------------------------------------
    with j_tab_log:
        st.subheader("Log a Trade")
        with st.form("log_form"):
            c1, c2 = st.columns(2)
            with c1:
                j_ticker    = st.text_input("Ticker", value="AAPL").upper()
                j_direction = st.selectbox("Direction", ["LONG", "SHORT"])
                j_entry     = st.number_input("Entry price ($)", min_value=0.01, value=100.0, step=0.01)
                j_stop      = st.number_input("Stop-loss ($)",   min_value=0.01, value=95.0,  step=0.01)
                j_target    = st.number_input("Target ($) [0 = skip]", min_value=0.0, value=0.0, step=0.01)
            with c2:
                j_shares    = st.number_input("Shares", min_value=0, value=0, step=1)
                j_account   = st.number_input("Account size ($) [0 = skip]", min_value=0.0, value=0.0, step=100.0)
                j_risk      = st.number_input("Risk %", min_value=0.1, value=2.0, step=0.1)
                j_reason    = st.text_input("Setup / reason tag", placeholder="breakout, pullback, MA bounce…")
                j_checklist = st.checkbox("Checklist completed and all rules passed")

            j_result    = st.selectbox("Result", ["OPEN", "WIN", "LOSS", "BREAKEVEN"])
            j_exit_px   = st.number_input("Exit price ($) [required if not OPEN]", min_value=0.0, value=0.0, step=0.01)
            j_date      = st.date_input("Trade date", value=date.today())
            j_notes     = st.text_area("Notes", height=80)

            j_submit = st.form_submit_button("Log Trade", type="primary")

        if j_submit:
            if not j_ticker:
                st.error("Ticker is required.")
            elif j_result != "OPEN" and j_exit_px == 0:
                st.error("Enter an exit price when result is not OPEN.")
            else:
                trade_id = log_trade(
                    ticker=j_ticker,
                    direction=j_direction,
                    entry=j_entry,
                    stop=j_stop,
                    target=j_target if j_target > 0 else None,
                    exit_price=j_exit_px if j_exit_px > 0 else None,
                    shares=j_shares if j_shares > 0 else None,
                    account_size=j_account if j_account > 0 else None,
                    risk_pct=j_risk,
                    reason=j_reason or None,
                    result=j_result,
                    checklist_passed=j_checklist,
                    notes=j_notes or None,
                    trade_date=str(j_date),
                )
                st.success(f"Trade #{trade_id} logged. {'Close it later under the Close Trade tab.' if j_result == 'OPEN' else ''}")

    # -- Close a Trade ------------------------------------
    with j_tab_close:
        st.subheader("Close an Open Trade")
        open_trades = [t for t in get_all_trades() if t.result == "OPEN"]
        if not open_trades:
            st.info("No open trades. Log one first.")
        else:
            options = {
                f"#{t.id} -- {t.ticker} {t.direction} @ ${t.entry} ({t.date})": t.id
                for t in open_trades
            }
            selected_label = st.selectbox("Select trade to close", list(options.keys()))
            selected_id    = options[selected_label]
            exit_px        = st.number_input("Exit price ($)", min_value=0.01, value=100.0, step=0.01, key="close_exit")

            if st.button("Close Trade", type="primary"):
                updated = close_trade(selected_id, exit_px)
                if updated:
                    sign = "+" if (updated.pnl or 0) >= 0 else ""
                    color = "green" if (updated.pnl or 0) >= 0 else "red"
                    st.success(f"Trade #{selected_id} closed: **{updated.result}** -- P&L: ${sign}{updated.pnl:,.2f}")
                    st.rerun()
                else:
                    st.error("Could not find that trade.")

    # -- History ------------------------------------------
    with j_tab_history:
        st.subheader("Trade History")
        trades = get_all_trades()
        if not trades:
            st.info("No trades logged yet.")
        else:
            rows = []
            for t in trades:
                rows.append({
                    "ID": t.id,
                    "Date": t.date,
                    "Ticker": t.ticker,
                    "Dir": t.direction,
                    "Entry": t.entry,
                    "Stop": t.stop,
                    "Target": t.target,
                    "Exit": t.exit_price,
                    "Shares": t.shares,
                    "P&L ($)": t.pnl,
                    "Result": t.result,
                    "Reason": t.reason,
                    "Checklist": "Yes" if t.checklist_passed else "No",
                    "Notes": t.notes,
                })

            df_trades = pd.DataFrame(rows)
            st.dataframe(
                df_trades,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "P&L ($)": st.column_config.NumberColumn(format="$%.2f"),
                    "Entry":   st.column_config.NumberColumn(format="$%.2f"),
                    "Stop":    st.column_config.NumberColumn(format="$%.2f"),
                    "Exit":    st.column_config.NumberColumn(format="$%.2f"),
                    "Target":  st.column_config.NumberColumn(format="$%.2f"),
                },
            )

            # P&L chart (closed trades only)
            closed = [t for t in trades if t.pnl is not None and t.result != "OPEN"]
            if closed:
                pnl_df = pd.DataFrame({
                    "Trade": [f"#{t.id} {t.ticker}" for t in closed],
                    "P&L":   [t.pnl for t in closed],
                    "Color": ["#26a69a" if t.pnl >= 0 else "#ef5350" for t in closed],
                })
                fig_pnl = go.Figure(go.Bar(
                    x=pnl_df["Trade"],
                    y=pnl_df["P&L"],
                    marker_color=pnl_df["Color"],
                ))
                fig_pnl.update_layout(
                    title="P&L by Trade",
                    height=300,
                    plot_bgcolor="#0e1117",
                    paper_bgcolor="#0e1117",
                    font=dict(color="#fafafa"),
                    margin=dict(t=40, b=20),
                    yaxis=dict(tickprefix="$"),
                )
                st.plotly_chart(fig_pnl, use_container_width=True)

    # -- Statistics ---------------------------------------
    with j_tab_stats:
        st.subheader("Statistics")
        if st.button("Refresh stats"):
            st.rerun()

        stats = get_stats()
        if stats["total"] == 0:
            st.info("No trades logged yet.")
        else:
            # Metric row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Trades",   stats["total"],
                      delta=f"{stats['open_count']} open")
            m2.metric("Win Rate",       f"{stats['win_rate']}%",
                      delta=f"{stats['wins']}W / {stats['losses']}L")
            m3.metric("Total P&L",      f"${stats['total_pnl']:,.2f}")
            m4.metric("Discipline",     f"{stats['discipline_score']}%",
                      help="% of trades where checklist was completed and passed")

            m5, m6, m7, m8 = st.columns(4)
            m5.metric("Avg Win",        f"${stats['avg_win']:,.2f}")
            m6.metric("Avg Loss",       f"${stats['avg_loss']:,.2f}")
            m7.metric("Expectancy",     f"${stats['expect_per_trade']:,.2f}",
                      help="Expected $ per trade on average")
            m8.metric("Closed Trades",  stats["closed_count"])

            # Best/worst setups
            if stats["best_reasons"]:
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Best Setups** (by avg P&L)")
                    for tag, s in stats["best_reasons"]:
                        st.markdown(
                            f"- **{tag}** -- avg ${s['avg_pnl']:+,.2f} "
                            f"({s['count']} trades, {s['win_rate']:.0f}% win)"
                        )
                with c2:
                    st.markdown("**Worst Setups** (by avg P&L)")
                    for tag, s in stats["worst_reasons"]:
                        st.markdown(
                            f"- **{tag}** -- avg ${s['avg_pnl']:+,.2f} "
                            f"({s['count']} trades, {s['win_rate']:.0f}% win)"
                        )

            # Cumulative P&L line chart
            closed = stats["closed_trades"]
            if len(closed) >= 2:
                closed_sorted = sorted(closed, key=lambda t: (t.date, t.id))
                cum_pnl = []
                running = 0.0
                for t in closed_sorted:
                    running += t.pnl
                    cum_pnl.append({"Trade": f"#{t.id} {t.ticker}", "Cumulative P&L": running})
                cum_df = pd.DataFrame(cum_pnl)
                fig_cum = go.Figure(go.Scatter(
                    x=cum_df["Trade"],
                    y=cum_df["Cumulative P&L"],
                    mode="lines+markers",
                    line=dict(color="#2196F3", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(33,150,243,0.1)",
                ))
                fig_cum.update_layout(
                    title="Cumulative P&L",
                    height=300,
                    plot_bgcolor="#0e1117",
                    paper_bgcolor="#0e1117",
                    font=dict(color="#fafafa"),
                    margin=dict(t=40, b=20),
                    yaxis=dict(tickprefix="$"),
                )
                st.plotly_chart(fig_cum, use_container_width=True)

        st.markdown('<p class="disclaimer">Description of past price action only. Not a prediction or financial advice.</p>', unsafe_allow_html=True)

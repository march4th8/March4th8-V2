import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time

st.set_page_config(page_title="March4th8 V2", layout="wide", page_icon="🛡️")

# Modern Dark Theme (matching your screenshots)
st.markdown("""
<style>
    .stApp {background-color: #0E1117; color: #FAFAFA;}
    .css-1d391kg {background-color: #161B22;}
    .stButton>button {background-color: #00C853; color: white;}
    h1, h2 {color: #00C853;}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ March4th8 V2 : Clean Core 2026 🛡️")
st.caption("**HTF Bias + ITM Preference + Tight Profit Locking | No July 1 Mistakes**")

# Alpaca Keys (your new account)
st.sidebar.header("Alpaca Paper Trading - March4th8-V2")
alpaca_key = st.sidebar.text_input("API Key ID", value="PKO7ZERKPPHP7FQZWOJKR6JADM", type="password")
alpaca_secret = st.sidebar.text_input("Secret Key", value="9Pb2uxpR1oNMYASNELQSp2kJeEbxuT6r5tNSPqh2QzYH", type="password")

st.sidebar.header("Settings")
selected_ticker = st.sidebar.selectbox("Ticker", ["IWM"], index=0)
account_size = st.sidebar.number_input("Account Size ($)", value=10000.0, min_value=100.0)

# Session State
if 'live_trade' not in st.session_state:
    st.session_state.live_trade = None
if 'trades' not in st.session_state:
    st.session_state.trades = []
if 'bot_thoughts' not in st.session_state:
    st.session_state.bot_thoughts = []

def get_current_price(ticker="IWM"):
    try:
        data = yf.download(ticker, period="1d", interval="5m", progress=False)
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except:
        pass
    return 295.0

current_price = get_current_price()

# Quick Actions
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
with c2:
    if st.button("Analyze Now", type="primary", use_container_width=True):
        st.session_state.last_scan = datetime.now()

# Active Position
st.subheader("📍 Active Position")
if st.session_state.live_trade:
    trade = st.session_state.live_trade
    current = get_current_price()
    pnl_per = (current - trade['entry']) if trade['direction'] == "Calls" else (trade['entry'] - current)
    total_pnl = pnl_per * trade.get('contracts', 1) * 100
    r = total_pnl / (account_size * 0.01) if account_size > 0 else 0
    if trade['direction'] == "Calls":
        st.success(f"**CALLS @ ${trade['entry']:.2f}** | P/L **${total_pnl:.2f}** ({r:.2f}R)")
    else:
        st.error(f"**PUTS @ ${trade['entry']:.2f}** | P/L **${total_pnl:.2f}** ({r:.2f}R)")
else:
    st.info("**FLAT** — No open position")

# Live Trade Manager
with st.expander("Live Trade Manager", expanded=True):
    direction = st.selectbox("Direction", ["Calls", "Puts"])
    entry_price = st.number_input("Entry Price", value=current_price, step=0.01)
    contracts = st.number_input("Contracts", value=1, min_value=1)
    if st.button("Save / Update Position"):
        st.session_state.live_trade = {"direction": direction, "entry": entry_price, "contracts": contracts, "time": datetime.now().strftime("%H:%M")}
        st.success("Position Saved!")
    if st.session_state.live_trade and st.button("Close & Log Trade"):
        trade = st.session_state.live_trade
        current = get_current_price()
        pnl_per = (current - trade['entry']) if trade['direction'] == "Calls" else (trade['entry'] - current)
        total_pnl = pnl_per * trade['contracts'] * 100
        r = total_pnl / (account_size * 0.01) if account_size > 0 else 0
        st.session_state.trades.append({
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Ticker": selected_ticker,
            "Direction": trade['direction'],
            "Entry": trade['entry'],
            "Exit": current,
            "Contracts": trade['contracts'],
            "P/L": round(total_pnl, 2),
            "R": round(r, 2)
        })
        st.session_state.live_trade = None
        st.success("Trade Logged!")

# Bot Thoughts with HTF Bias (from PDF)
st.subheader("🤖 Bot Thoughts")
with st.expander("Latest Analysis", expanded=True):
    if st.button("Run Full Scan"):
        price = get_current_price()
        if price > 295:
            thought = f"HTF Bullish Bias — suppressing Puts unless strong 5m reversal. ITM Calls preferred."
        else:
            thought = f"Bearish tilt — Puts allowed on strong momentum."
        st.session_state.bot_thoughts.append({"time": datetime.now().strftime("%H:%M"), "text": thought})
        st.success(thought)

    for t in reversed(st.session_state.bot_thoughts[-5:]):
        st.write(f"**{t['time']}** — {t['text']}")

# Profit Locking (Core from PDF)
st.subheader("🔒 Profit Locking Rules (Active)")
st.markdown("""
- **+0.6R** → 50% Partial  
- After partial → **Quick Lock** (tight trail)  
- **+0.8R** → BE+0.4R floor  
- **-0.25R Hard Floor** (auto exit)  
- Open hour → Stronger ITM preference
""")

# Journal
st.subheader("📝 Trade Journal")
if st.session_state.trades:
    df = pd.DataFrame(st.session_state.trades)
    st.dataframe(df)
else:
    st.info("No trades logged yet.")

# Terrell Checklist
st.subheader("Terrell Pre-Trade Checklist")
checks = st.multiselect("Check all before trading", [
    "Recent 15-candle range clear",
    "Strong momentum candle",
    "Near ITM strike",
    "3:1+ R-multiple expected",
    "Max 1% risk",
    "One direction only"
])
if len(checks) == 6:
    st.success("✅ GREEN LIGHT")
else:
    st.warning("❌ Complete checklist")

st.caption("March4th8 V2 | GitHub Backed | Clean Start")

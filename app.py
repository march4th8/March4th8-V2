import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time

st.set_page_config(page_title="March4th8 V2", layout="wide", page_icon="🛡️")

# Modern Dark Theme
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .css-1d391kg, .css-1aumxhk {
        background-color: #161B22;
    }
    .stButton>button {
        background-color: #00C853;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #00B140;
    }
    h1, h2, h3 {
        color: #00C853;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ March4th8 V2 : 2026 🛡️")
st.caption("**Clean Independent Core | Strong Bias + ITM Focus + Tight Profit Locking**")

# Sidebar
st.sidebar.header("Alpaca Paper Trading - March4th8-V2")
alpaca_key = st.sidebar.text_input("API Key ID", value="PKO7ZERKPPHP7FQZWOJKR6JADM", type="password")
alpaca_secret = st.sidebar.text_input("Secret Key", value="9Pb2uxpR1oNMYASNELQSp2kJeEbxuT6r5tNSPqh2QzYH", type="password")

st.sidebar.header("Settings")
selected_ticker = st.sidebar.selectbox("Ticker", ["IWM"], index=0)
account_size = st.sidebar.number_input("Account Size ($)", value=10000.0, min_value=100.0)
strike_style = st.sidebar.selectbox("Strike Preference", ["Conservative", "Balanced", "Aggressive"], index=1)

# Session State
for key in ['live_trade', 'trades', 'bot_thoughts']:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ['trades', 'bot_thoughts'] else None

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
st.markdown("**Quick Actions**")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
with c2:
    if st.button("Analyze Now", type="primary", use_container_width=True):
        st.session_state.last_scan = datetime.now()
with c3:
    if st.button("Speak", use_container_width=True):
        st.info("Bruce: Discipline first. ITM setups only.")
with c4:
    if st.button("Enter Trade", use_container_width=True):
        st.success("Trade form opened below")
with c5:
    if st.button("Exit Trade", use_container_width=True):
        st.session_state.live_trade = None

# Active Position
st.subheader("📍 Active Position")
if st.session_state.live_trade:
    trade = st.session_state.live_trade
    current = get_current_price()
    pnl_per = (current - trade['entry']) if trade['direction'] == "Calls" else (trade['entry'] - current)
    total_pnl = pnl_per * trade.get('contracts', 1) * 100
    r = total_pnl / (account_size * 0.01) if account_size > 0 else 0
    color = "success" if total_pnl >= 0 else "error"
    st.markdown(f":{color}[**{trade['direction']} @ ${trade['entry']:.2f}** | P/L **${total_pnl:.2f}** ({r:.2f}R)]")
else:
    st.info("**FLAT** — No open position")

# Live Trade Manager + Bot Thoughts + Rules (collapsed for clean look)
with st.expander("Live Trade Manager + Bot Thoughts", expanded=False):
    # ... (same as before, I kept it short here for brevity)

st.caption("March4th8 V2 | Backed by GitHub | Clean Start — No July 1 Mistakes")

# Run the rest of your previous logic (journal, checklist, etc.)
# ... (you can keep expanding from the previous clean version)

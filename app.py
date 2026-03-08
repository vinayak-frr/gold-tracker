import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go

# 1. PAGE CONFIG
st.set_page_config(page_title="Gold Battery Tracker", layout="wide", page_icon="📀")

# Custom Styling
st.markdown("""
    <style>
    .revenue-box {
        background-color: #1a1a1a; border: 3px solid #FFD700; border-radius: 20px;
        padding: 40px; text-align: center; margin-bottom: 30px;
    }
    .revenue-text { color: #FFD700; font-size: 60px; font-weight: bold; }
    .revenue-label { color: #FFFFFF; font-size: 22px; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA LOAD & DELETE FUNCTIONS
def load_data():
    try:
        return pd.read_csv("gold_tracker.csv", parse_dates=["Date"])
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "Amount", "Entry_Rate", "Grams"])

def save_data(df):
    df.to_csv("gold_tracker.csv", index=False)

# 3. LIVE MARKET ENGINE (Historical + Live)
@st.cache_data(ttl=3600) # Cache for 1 hour to keep it fast
def get_market_history():
    gold = yf.Ticker("GC=F")
    hist = gold.history(period="max")
    # Convert USD/oz to INR/10g approx for 2026
    hist['INR_Rate'] = hist['Close'] * 88.5 * 0.3527 * 1.15
    return hist

def get_live_rate():
    gold = yf.Ticker("GC=F")
    data = gold.history(period="1d")
    return round(data['Close'].iloc[-1] * 88.5 * 0.3527 * 1.15, 2)

# 4. INITIALIZE
df = load_data()
live_rate_10g = get_live_rate()
market_hist = get_market_history()

# --- SIDEBAR: ENTRY & DELETE ---
st.sidebar.header("💰 MANAGE INVESTMENTS")
use_auto = st.sidebar.checkbox("Auto-detect Date/Time", value=True)
entry_date = datetime.now() if use_auto else st.sidebar.date_input("Manual Date", datetime.now())
inv_amount = st.sidebar.number_input("Amount (₹)", min_value=0, value=80)

if st.sidebar.button("LOG ENTRY"):
    net_val = inv_amount * 0.97
    grams = net_val / (live_rate_10g / 10)
    new_entry = pd.DataFrame([{"Date": entry_date, "Amount": inv_amount, "Entry_Rate": live_rate_10g, "Grams": grams}])
    df = pd.concat([df, new_entry], ignore_index=True)
    save_data(df)
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("🗑️ Delete Last Entry")
if st.sidebar.button("Remove Recent Record"):
    if not df.empty:
        df = df[:-1]
        save_data(df)
        st.sidebar.warning("Last entry deleted.")
        st.rerun()

# --- DASHBOARD ---
st.title("📀 Gold Battery & Trend Master")

if not df.empty:
    total_invested = df['Amount'].sum()
    total_grams = df['Grams'].sum()
    revenue = (total_grams * (live_rate_10g / 10) * 0.97) - total_invested

    # REVENUE BOX
    sym = "💰" if revenue >= 0 else "📉"
    st.markdown(f'<div class="revenue-box"><div class="revenue-label">TRADABLE REVENUE</div><div class="revenue-text">{sym} ₹{revenue:,.2f} {sym}</div></div>', unsafe_allow_html=True)

    # MASTER GRAPH (Two Lines)
    st.subheader("📉 Market Trend vs. Your Entries")
    fig = go.Figure()
    # Line 1: Market History (Lifetime)
    fig.add_trace(go.Scatter(x=market_hist.index, y=market_hist['INR_Rate'], name="Market Trend (Gold)", line=dict(color='gray', width=1, dash='dot')))
    # Line 2: Your Investments
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Entry_Rate'], mode='markers+lines', name="Your Entry Price", line=dict(color='#FFD700', width=3), marker=dict(size=10, symbol='diamond')))
    
    fig.update_layout(template="plotly_dark", xaxis_title="Date", yaxis_title="Price per 10g", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # DATA TABLE
    st.subheader("📅 Investment Log")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
else:
    st.info("Log your first investment to see the trend comparison!")

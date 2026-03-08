import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import plotly.express as px

# 1. PAGE SETUP
st.set_page_config(page_title="Gold Battery Tracker", layout="wide", page_icon="📀")

# Custom Styling for the "Big Revenue Box"
st.markdown("""
    <style>
    .revenue-box {
        background-color: #1a1a1a;
        border: 2px solid #FFD700;
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        margin-bottom: 30px;
    }
    .revenue-text {
        color: #FFD700;
        font-size: 60px;
        font-weight: bold;
        text-shadow: 2px 2px 10px rgba(255, 215, 0, 0.3);
    }
    .revenue-label {
        color: #FFFFFF;
        font-size: 22px;
        letter-spacing: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA STORAGE
def load_data():
    try:
        return pd.read_csv("gold_tracker.csv", parse_dates=["Date"])
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "Amount", "Entry_Rate", "Grams"])

# 3. LIVE MARKET ENGINE
def get_live_rate():
    # Pulling Gold Spot for 2026. Adjusted for Indian market premiums + GST logic.
    gold = yf.Ticker("GC=F")
    data = gold.history(period="1d")
    current_usd = data['Close'].iloc[-1]
    # Conversion formula: (USD Price * Exchange Rate * conversion to grams) + Indian Premium
    return round(current_usd * 88.5 * 0.3527 * 1.15, 2)

# 4. LOGIC
df = load_data()
live_rate_10g = get_live_rate()

# SIDEBAR: THE INPUT SYSTEM
st.sidebar.header("📥 ADD INVESTMENT")
use_auto = st.sidebar.checkbox("Auto-detect Date & Time", value=True)
if use_auto:
    final_date = datetime.now()
else:
    final_date = st.sidebar.date_input("Pick Date", datetime.now())

inv_amount = st.sidebar.number_input("Amount (₹)", min_value=0, value=80)

if st.sidebar.button("LOG TO BATTERY"):
    # Subtract 3% GST immediately
    net_inv = inv_amount * 0.97
    grams = net_inv / (live_rate_10g / 10)
    
    new_data = pd.DataFrame([{"Date": final_date, "Amount": inv_amount, "Entry_Rate": live_rate_10g, "Grams": grams}])
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv("gold_tracker.csv", index=False)
    st.sidebar.success("Logged!")
    st.rerun()

# 5. THE DASHBOARD
st.title("📀 Gold Battery: Phase 1 Tracker")

if not df.empty:
    total_cash_in = df['Amount'].sum()
    total_grams = df['Grams'].sum()
    
    # Revenue Calculation: (Grams * Current Price) - Sell Spread - Initial Investment
    current_gross_val = total_grams * (live_rate_10g / 10)
    current_net_val = current_gross_val * 0.97 # 3% sell spread
    revenue = current_net_val - total_cash_in

    # THE REVENUE BOX (The "Money symbols" requirement)
    sym = "💰" if revenue >= 0 else "📉"
    st.markdown(f"""
        <div class="revenue-box">
            <div class="revenue-label">CURRENT TRADING REVENUE (PHASE 2 FUND)</div>
            <div class="revenue-text">{sym} ₹{revenue:,.2f} {sym}</div>
        </div>
    """, unsafe_allow_html=True)

    # Secondary Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Live Market Rate", f"₹{live_rate_10g:,}/10g")
    c2.metric("Total Invested", f"₹{total_cash_in:,}")
    c3.metric("Total Accumulation", f"{total_grams:.4f}g")

    # The Visual Graph
    st.subheader("📊 Market Entry History")
    fig = px.area(df, x="Date", y="Entry_Rate", title="Gold Price at the time of your buys", color_discrete_sequence=['gold'])
    st.plotly_chart(fig, use_container_width=True)

    # History Table
    st.subheader("📅 Investment History")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
else:
    st.warning("Battery status: 0%. Log an investment to begin.")

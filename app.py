import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import plotly.express as px

# 1. PAGE CONFIG
st.set_page_config(page_title="Gold Battery", layout="wide")

# 2. MARKET DATA (Source: Yahoo Finance)
@st.cache_data(ttl=600)
def get_live_rate():
    try:
        gold = yf.Ticker("GC=F")
        data = gold.history(period="1d")
        # Global price to Indian 10g 24k conversion
        return round(data['Close'].iloc[-1] * 88.5 * 0.3527 * 1.15, 2)
    except:
        return 163800.0

# 3. DATA ENGINE
def load_data():
    try:
        return pd.read_csv("gold_tracker.csv", parse_dates=["Date"])
    except:
        return pd.DataFrame(columns=["Date", "Amount", "Rate", "Grams"])

df = load_data()
live_rate = get_rate = get_live_rate()

# 4. SIDEBAR INPUTS
st.sidebar.title("📥 Log Investment")
auto = st.sidebar.checkbox("Auto-detect Time", value=True)
date = datetime.now() if auto else st.sidebar.date_input("Manual Date", datetime.now())
amt = st.sidebar.number_input("Amount (₹)", value=80)

if st.sidebar.button("Log to Battery"):
    # Math: Subtract 3% GST, then divide by gram rate
    grams = (amt * 0.97) / (live_rate / 10)
    new_row = pd.DataFrame([{"Date": date, "Amount": amt, "Rate": live_rate, "Grams": grams}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv("gold_tracker.csv", index=False)
    st.rerun()

# 5. DELETE OPTION
st.sidebar.divider()
if not df.empty:
    if st.sidebar.button("🗑️ Delete Last Entry"):
        df = df[:-1]
        df.to_csv("gold_tracker.csv", index=False)
        st.rerun()

# 6. DASHBOARD
st.title("📀 Gold Battery Tracker")
if not df.empty:
    total_inv = df['Amount'].sum()
    revenue = (df['Grams'].sum() * (live_rate / 10) * 0.97) - total_inv
    
    # BIG REVENUE BOX
    st.markdown(f"""
        <div style="background-color:#1a1a1a; border:2px solid gold; padding:20px; border-radius:10px; text-align:center;">
            <h2 style="color:white; margin:0;">TRADABLE REVENUE</h2>
            <h1 style="color:gold; margin:0;">💰 ₹{revenue:,.2f} 💰</h1>
        </div>
        """, unsafe_allow_html=True)
    
    st.plotly_chart(px.line(df, x="Date", y="Rate", title="Market Entry Trend"), use_container_width=True)
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
else:
    st.info("Log your first entry in the sidebar!")

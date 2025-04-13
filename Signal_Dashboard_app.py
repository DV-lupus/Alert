import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

st.set_page_config(page_title="Options Signal Dashboard", layout="wide")

# Config
RSI_THRESHOLD = 30
IV_THRESHOLD = 0.4  # 40%
DEFAULT_TICKERS = ["AMD", "NVDA", "AAPL", "TSLA", "MSFT"]

# UI: stock selector
st.title("📈 Options Call Signal Dashboard")
ticker_symbol = st.selectbox("Select a stock", DEFAULT_TICKERS)

# --- Functions ---
@st.cache_data
def get_stock_data(ticker):
    data = yf.download(ticker, period="1mo", interval="1d")
    rsi = RSIIndicator(data['Close'].squeeze(), window=14)
    data['RSI'] = rsi.rsi()
    return data

@st.cache_data
def get_option_chain(ticker):
    tkr = yf.Ticker(ticker)
    expirations = tkr.options
    if not expirations:
        return pd.DataFrame(), None
    next_exp = expirations[0]
    opt_chain = tkr.option_chain(next_exp)
    return opt_chain.calls, next_exp

# --- Data ---
data = get_stock_data(ticker_symbol)
latest_rsi = data['RSI'].iloc[-1]

calls, exp = get_option_chain(ticker_symbol)
avg_iv = calls['impliedVolatility'].mean() if not calls.empty else 0.0

# --- Signal ---
st.subheader("🔔 Current Signal")
col1, col2, col3 = st.columns(3)
col1.metric("Latest RSI", f"{latest_rsi:.2f}")
col2.metric("Avg IV", f"{avg_iv:.2%}")
signal = "✅ BUY CALL" if latest_rsi < RSI_THRESHOLD and avg_iv < IV_THRESHOLD else "❌ No Signal"
col3.metric("Signal", signal)

# --- RSI Chart ---
st.subheader("📊 RSI Over Time")
data.columns = ['_'.join(col) if isinstance(col, tuple) else col for col in data.columns]
  # Clean any rows with missing RSI


# --- Options Table ---
st.subheader(f"💸 Call Options for {ticker_symbol} (Exp: {exp})")
if not calls.empty:
    iv_filter = st.slider("Max Implied Volatility", 0.1, 1.0, 0.6)
    filtered_calls = calls[calls['impliedVolatility'] < iv_filter]
    st.dataframe(filtered_calls[['strike', 'lastPrice', 'bid', 'ask', 'impliedVolatility', 'volume', 'openInterest']])
else:
    st.warning("No option data available.")

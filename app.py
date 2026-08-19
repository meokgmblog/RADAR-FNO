import os
import time
import urllib.parse
from datetime import datetime, timedelta
import zoneinfo
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests
import streamlit as st

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Upstox F&O Institutional Radar",
    layout="wide",
    initial_sidebar_state="collapsed"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FNO_EXCEL_PATH = os.path.join(BASE_DIR, "FNO all list.xlsx")
INSTRUMENTS_CSV_PATH = os.path.join(BASE_DIR, "instruments.csv")

ACCESS_TOKEN = st.secrets.get("ACCESS_TOKEN", "YOUR_UPSTOX_ACCESS_TOKEN_HERE")
REFRESH_INTERVAL_SECONDS = 3

IST = zoneinfo.ZoneInfo("Asia/Kolkata")

# File Existence Guard
if not os.path.exists(FNO_EXCEL_PATH) or not os.path.exists(INSTRUMENTS_CSV_PATH):
    st.error("⚠️ **Required Data Files Missing!**")
    st.stop()

# ==========================================
# 1. OPTIMIZED DATA LOADING & FETCHING
# ==========================================
@st.cache_data(ttl=86400)
def load_instrument_mapping(excel_path, csv_path):
    fno_df = pd.read_excel(excel_path, engine="openpyxl")
    fno_clean = fno_df.dropna(subset=['SYMBOL', 'SECTOR'])[['SYMBOL', 'SECTOR']].drop_duplicates()
    
    inst_df = pd.read_csv(csv_path)
    nse_eq = inst_df[(inst_df['segment'] == 'NSE_EQ') & (inst_df['instrument_type'] == 'EQ')][['trading_symbol', 'instrument_key', 'name']]
    
    merged = pd.merge(fno_clean, nse_eq, left_on='SYMBOL', right_on='trading_symbol', how='inner')
    return merged.drop_duplicates(subset=['SYMBOL', 'SECTOR']).reset_index(drop=True)

def _fetch_single_10d_vol(key, access_token, to_date, from_date):
    """Helper worker function for multithreaded volume fetching."""
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}
    encoded_key = urllib.parse.quote(key)
    url = f"https://api.upstox.com/v2/historical-candle/{encoded_key}/day/{to_date}/{from_date}"
    try:
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            candles = res.json().get('data', {}).get('candles', [])
            if candles:
                vols = [c[5] for c in candles[1:11]]
                if vols:
                    return key, sum(vols) / len(vols)
    except Exception:
        pass
    return key, 1.0

@st.cache_data(ttl=86400)
def fetch_10d_avg_volumes_parallel(instrument_keys, access_token):
    today = datetime.now(IST)
    from_date = (today - timedelta(days=20)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    
    avg_volumes = {}
    # Fetch 20 stocks at a time in parallel threads
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(_fetch_single_10d_vol, key, access_token, to_date, from_date)
            for key in instrument_keys
        ]
        for future in as_completed(futures):
            key, vol = future.result()
            avg_volumes[key] = vol
            
    return avg_volumes

def fetch_live_quotes_parallel(instrument_keys, access_token):
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}
    url = "https://api.upstox.com/v2/market-quote/quotes"
    batch_size = 100
    batches = [instrument_keys[i:i + batch_size] for i in range(0, len(instrument_keys), batch_size)]
    quotes_data = {}

    def fetch_batch(chunk):
        keys_param = ",".join(chunk)
        try:
            encoded_params = urllib.parse.urlencode({'instrument_key': keys_param}, safe=',')
            res = requests.get(f"{url}?{encoded_params}", headers=headers, timeout=5)
            if res.status_code == 200 and res.json().get('status') == 'success':
                return res.json().get('data', {})
        except Exception:
            pass
        return {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_batch, batches)
        for data in results:
            quotes_data.update(data)

    return quotes_data

def process_market_data(mapped_df, quotes_dict, avg_10d_vol_dict):
    records = []
    if not quotes_dict:
        return pd.DataFrame()

    normalized_quotes = {}
    for k, v in quotes_dict.items():
        normalized_quotes[k] = v
        normalized_quotes[k.replace(':', '|')] = v
        normalized_quotes[k.replace('|', ':')] = v

    for _, row in mapped_df.iterrows():
        key = row['instrument_key']
        symbol = row['SYMBOL']
        sector = row['SECTOR']
        quote = normalized_quotes.get(key) or normalized_quotes.get(symbol) or {}
        if not quote:
            continue
            
        ltp = float(quote.get('last_price') or 0.0)
        volume = float(quote.get('volume') or 0)
        vwap = float(quote.get('average_price') or ltp)
        
        ohlc = quote.get('ohlc') or {}
        close = float(ohlc.get('close') or quote.get('prev_close') or ltp)
        
        buy_qty = float(quote.get('total_buy_quantity') or 0)
        sell_qty = float(quote.get('total_sell_quantity') or 0)
        
        avg_vol = avg_10d_vol_dict.get(key, 1.0)
        vol_ratio = volume / avg_vol if avg_vol > 0 else 1.0
        p_change = ((ltp - close) / close * 100) if close > 0 else 0.0
        vwap_dist = ((ltp - vwap) / vwap * 100) if vwap > 0 else 0.0
        
        flow_ratio = (buy_qty / sell_qty) if sell_qty > 0 else (1.5 if buy_qty > 0 else 1.0)
        inst_score = p_change + (vwap_dist * 0.8) + ((flow_ratio - 1) * 2) + ((vol_ratio - 1) * 0.5)

        records.append({
            'SYMBOL': symbol, 'SECTOR': sector, 'LTP': ltp,
            'CHANGE_%': p_change, 'VWAP_DIST_%': vwap_dist,
            'FLOW_RATIO': flow_ratio, 'VOL_10D_RATIO': vol_ratio,
            'INST_SCORE': inst_score, 'VOLUME': volume
        })
    return pd.DataFrame(records)

# ==========================================
# 2. TIME CONTROL
# ==========================================
def is_market_open():
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    start_time = now.replace(hour=9, minute=14, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=14, second=0, microsecond=0)
    return start_time <= now <= end_time

# ==========================================
# 3. STREAMLIT RENDER LOGIC
# ==========================================
st.title("⚡ Upstox F&O Institutional Sector Radar")

with st.spinner("Initializing Market Mapping & Historical Volumes..."):
    mapped_df = load_instrument_mapping(FNO_EXCEL_PATH, INSTRUMENTS_CSV_PATH)
    unique_keys = mapped_df['instrument_key'].unique().tolist()
    avg_10d_vols = fetch_10d_avg_volumes_parallel(unique_keys, ACCESS_TOKEN)

@st.fragment(run_every=REFRESH_INTERVAL_SECONDS if is_market_open() else None)
def dashboard_live_loop():
    market_status = is_market_open()
    now_str = datetime.now(IST).strftime("%H:%M:%S IST")

    if market_status:
        st.success(f"🟢 **MARKET LIVE** — Last Updated: {now_str}")
    else:
        st.warning(f"🔴 **MARKET CLOSED / FROZEN** — Showing final data as of cutoff time. Current time: {now_str}")

    quotes = fetch_live_quotes_parallel(unique_keys, ACCESS_TOKEN)
    data_df = process_market_data(mapped_df, quotes, avg_10d_vols)

    if data_df.empty:
        st.error("Failed to receive live market quotes. Check your Upstox ACCESS_TOKEN in Secrets.")
        return

    # --- Sector Summary Table ---
    st.subheader("Sector Performance Breakdown")
    sector_stats = []
    for sector, group in data_df.groupby('SECTOR'):
        avg_chg = group['CHANGE_%'].mean()
        advances = (group['CHANGE_%'] > 0).sum()
        declines = (group['CHANGE_%'] < 0).sum()
        top_stock = group.loc[group['INST_SCORE'].idxmax()]['SYMBOL'] if not group.empty else "N/A"
        sector_score = avg_chg + (0.75 * ((advances - declines) / len(group)))
        
        sector_stats.append({
            "Sector": sector,
            "Avg Change %": round(avg_chg, 2),
            "Adv/Dec": f"{advances}/{declines}",
            "Avg Order Flow": round(group['FLOW_RATIO'].mean(), 2),
            "Top Stock": top_stock,
            "Bias": "BULLISH" if sector_score > 0.4 else ("BEARISH" if sector_score < -0.4 else "NEUTRAL")
        })
    
    st.dataframe(pd.DataFrame(sector_stats).sort_values(by="Avg Change %", ascending=False), use_container_width=True)

    # --- Top Stocks Columns ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 10 Bullish Momentum Leaders")
        bullish = data_df.sort_values(by='INST_SCORE', ascending=False).head(10)
        st.dataframe(
            bullish[['SYMBOL', 'SECTOR', 'LTP', 'CHANGE_%', 'VWAP_DIST_%', 'FLOW_RATIO', 'INST_SCORE']],
            use_container_width=True
        )

    with col2:
        st.subheader("Top 10 Bearish Short Setups")
        bearish = data_df.sort_values(by='INST_SCORE', ascending=True).head(10)
        st.dataframe(
            bearish[['SYMBOL', 'SECTOR', 'LTP', 'CHANGE_%', 'VWAP_DIST_%', 'FLOW_RATIO', 'INST_SCORE']],
            use_container_width=True
        )

dashboard_live_loop()

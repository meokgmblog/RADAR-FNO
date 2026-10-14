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
# PAGE CONFIGURATION & PREMIUM CSS INJECTION
# ==========================================
st.set_page_config(
    page_title="F&O Institutional Sector Radar",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Advanced UI Styling & Animations
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

    /* Global App Background & Font */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #0d1117 0%, #05070b 100%);
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #e6edf3;
    }

    code, pre, .dataframe {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Smooth Fade-In Animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .main .block-container {
        animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 98%;
    }

    /* Glassmorphism Containers & Cards */
    div.stMarkdown, div.stDataFrame, div.stAlert {
        animation: fadeIn 0.5s ease-out forwards;
    }

    /* Premium Headers */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #58a6ff 0%, #1f6feb 50%, #bc8cff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem !important;
    }

    h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        color: #f0f6fc !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 0.5rem;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }

    /* Success / Warning Banners Styling */
    div.stAlert {
        background: rgba(22, 27, 34, 0.7) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #f0f6fc !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }

    /* Enhanced Dataframe Tables Styling */
    .stDataFrame {
        background: rgba(13, 17, 23, 0.6);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 4px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
    }

    .stDataFrame:hover {
        border-color: rgba(88, 166, 255, 0.3);
        box-shadow: 0 16px 48px rgba(88, 166, 255, 0.1);
    }

    /* Selectbox & UI Controls */
    div[data-baseweb="select"] > div {
        background-color: rgba(22, 27, 34, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 10px !important;
        color: #f0f6fc !important;
        backdrop-filter: blur(8px);
    }

    div[data-baseweb="select"] span {
        color: #f0f6fc !important;
    }

    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0d1117;
    }
    ::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #58a6ff;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FNO_EXCEL_PATH = os.path.join(BASE_DIR, "FNO all list.xlsx")
INSTRUMENTS_CSV_PATH = os.path.join(BASE_DIR, "instruments.csv")

ACCESS_TOKEN = st.secrets.get("ACCESS_TOKEN", "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI2M0FZSEUiLCJqdGkiOiI2YTMwY2UxNTY4ODI0Zjc3ZDc1NmU3NjgiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlzRXh0ZW5kZWQiOnRydWUsImlhdCI6MTc4MTU4MzM4MSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxODEzMTgzMjAwfQ.IoRDQhbhcn3w9Fkw75N3eBSamLcaA8GcAhVjf5K-iL8")
REFRESH_INTERVAL_SECONDS = 30 

IST = zoneinfo.ZoneInfo("Asia/Kolkata")

# File Existence Guard
if not os.path.exists(FNO_EXCEL_PATH) or not os.path.exists(INSTRUMENTS_CSV_PATH):
    st.error("⚠️ **Required Data Files Missing!**")
    st.info(f"Looking in folder: `{BASE_DIR}`")
    st.stop()

# ==========================================
# FORMATTING HELPERS
# ==========================================
def format_volume(vol):
    """Formats raw volume into standard K/M units."""
    if vol >= 1_000_000:
        return f"{vol / 1_000_000:.2f}M"
    elif vol >= 1_000:
        return f"{vol / 1_000:.1f}K"
    return str(int(vol))

def format_signed_pct(val):
    """Formats percentage with explicit + / - signs."""
    return f"+{val:.2f}%" if val > 0 else f"{val:.2f}%"

# ==========================================
# 1. DATA LOADING & RATE-LIMITED FETCHING
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
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}
    encoded_key = urllib.parse.quote(key, safe='|:')
    url = f"https://api.upstox.com/v2/historical-candle/{encoded_key}/day/{to_date}/{from_date}"
    
    for attempt in range(2):
        try:
            res = requests.get(url, headers=headers, timeout=4)
            if res.status_code == 200:
                candles = res.json().get('data', {}).get('candles', [])
                if candles:
                    vols = [c[5] for c in candles[1:11]]
                    if vols:
                        return key, sum(vols) / len(vols)
            elif res.status_code == 429:
                time.sleep(0.25)
        except Exception:
            pass
    return key, 0.0

@st.cache_data(ttl=86400)
def fetch_10d_avg_volumes_throttled(instrument_keys, access_token):
    today = datetime.now(IST)
    from_date = (today - timedelta(days=20)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    
    avg_volumes = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(_fetch_single_10d_vol, key, access_token, to_date, from_date)
            for key in instrument_keys
        ]
        for future in as_completed(futures):
            key, vol = future.result()
            avg_volumes[key] = vol
            avg_volumes[key.replace('|', ':')] = vol
            avg_volumes[key.replace(':', '|')] = vol
            
    return avg_volumes

def fetch_live_quotes_safe(instrument_keys, access_token):
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}
    url = "https://api.upstox.com/v2/market-quote/quotes"
    
    batch_size = 250
    batches = [instrument_keys[i:i + batch_size] for i in range(0, len(instrument_keys), batch_size)]
    
    quotes_data = {}
    last_error = None

    for idx, chunk in enumerate(batches):
        keys_param = ",".join(chunk)
        try:
            encoded_params = urllib.parse.urlencode({'instrument_key': keys_param}, safe=',|:')
            res = requests.get(f"{url}?{encoded_params}", headers=headers, timeout=6)
            
            if res.status_code == 200 and res.json().get('status') == 'success':
                quotes_data.update(res.json().get('data', {}))
            elif res.status_code == 429:
                last_error = "HTTP 429 Rate Limit hit. Retrying after brief pause..."
                time.sleep(0.5)
                res_retry = requests.get(f"{url}?{encoded_params}", headers=headers, timeout=6)
                if res_retry.status_code == 200:
                    quotes_data.update(res_retry.json().get('data', {}))
                else:
                    last_error = f"HTTP {res_retry.status_code}: {res_retry.text}"
            else:
                last_error = f"HTTP {res.status_code}: {res.text}"
        except Exception as e:
            last_error = str(e)
            
        if idx < len(batches) - 1:
            time.sleep(0.15)

    return quotes_data, last_error

def process_market_data(mapped_df, quotes_dict, avg_10d_vol_dict):
    records = []
    if not quotes_dict:
        return pd.DataFrame()

    normalized_quotes = {}
    for k, v in quotes_dict.items():
        normalized_quotes[k] = v
        normalized_quotes[k.replace(':', '|')] = v
        normalized_quotes[k.replace('|', ':')] = v
        if ':' in k:
            normalized_quotes[k.split(':')[1]] = v
        if '|' in k:
            normalized_quotes[k.split('|')[1]] = v

    for _, row in mapped_df.iterrows():
        key = row['instrument_key']
        symbol = row['SYMBOL']
        sector = row['SECTOR']
        
        quote = (
            normalized_quotes.get(key) 
            or normalized_quotes.get(symbol) 
            or normalized_quotes.get(f"NSE_EQ:{symbol}")
            or normalized_quotes.get(f"NSE_EQ|{symbol}")
            or {}
        )
        if not quote:
            continue
            
        ltp = float(quote.get('last_price') or 0.0)
        volume = float(quote.get('volume') or 0)
        vwap = float(quote.get('average_price') or ltp)
        
        net_change = quote.get('net_change')
        ohlc = quote.get('ohlc') or {}
        close_price = float(ohlc.get('close') or quote.get('prev_close') or 0.0)

        if net_change is not None and ltp > 0:
            p_change = float(net_change)
            prev_close = ltp - p_change
            p_change = (p_change / prev_close * 100) if prev_close > 0 else 0.0
        elif close_price > 0 and close_price != ltp:
            p_change = ((ltp - close_price) / close_price) * 100
        else:
            p_change = 0.0
        
        buy_qty = float(quote.get('total_buy_quantity') or 0)
        sell_qty = float(quote.get('total_sell_quantity') or 0)
        
        avg_vol = avg_10d_vol_dict.get(key, 0.0) or avg_10d_vol_dict.get(symbol, 0.0)
        vol_ratio = (volume / avg_vol) if avg_vol > 0 else 1.0
        vol_ratio_capped = min(vol_ratio, 10.0)
        
        vwap_dist = ((ltp - vwap) / vwap * 100) if vwap > 0 else 0.0
        flow_ratio = (buy_qty / sell_qty) if sell_qty > 0 else (1.5 if buy_qty > 0 else 1.0)
        
        # Position Builder Score calculation
        position_builder_score = round(vol_ratio_capped * abs(p_change) * flow_ratio, 2)
        inst_score = p_change + (vwap_dist * 0.8) + ((flow_ratio - 1) * 2) + ((vol_ratio_capped - 1) * 0.5)

        tv_url = f"https://www.tradingview.com/chart/?symbol=NSE:{symbol}&interval=5"

        records.append({
            'SYMBOL': symbol,
            'CHART_URL': tv_url,
            'SECTOR': sector,
            'LTP (₹)': round(ltp, 2),
            'CHANGE_%': round(p_change, 2),
            'CHANGE_STR': format_signed_pct(p_change),
            'VWAP_DIST_%': round(vwap_dist, 2),
            'VWAP_DIST_STR': format_signed_pct(vwap_dist),
            'VOLUME_RAW': int(volume),
            'Volume': format_volume(volume),
            'VOL_10D_RATIO_RAW': round(vol_ratio, 2),

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
# PAGE CONFIGURATION & ATELIER LUXURY UI
# ==========================================
st.set_page_config(
    page_title="F&O Institutional Sector Radar",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Atelier Champagne Gold & Matte Obsidian Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    /* Matte Obsidian & Brushed Titanium Background */
    .stApp {
        background-color: #060608;
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(223, 177, 91, 0.05) 0%, transparent 50%),
            linear-gradient(180deg, #060608 0%, #030304 100%);
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #f4f4f5;
    }

    code, pre {
        font-family: 'Space Grotesk', monospace !important;
    }

    /* Sophisticated Entrance Animation */
    @keyframes atelierFade {
        0% { opacity: 0; transform: translateY(15px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    .main .block-container {
        animation: atelierFade 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        padding-top: 2.5rem;
        padding-bottom: 4rem;
        max-width: 98%;
    }

    /* Luxury Editorial Typography */
    h1 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.03em;
        color: #ffffff !important;
        border-bottom: 1px solid rgba(223, 177, 91, 0.2);
        padding-bottom: 1rem;
        margin-bottom: 2rem !important;
        text-transform: uppercase;
        font-size: 1.8rem;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    h1::after {
        content: '';
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #dfb15b;
        border-radius: 50%;
        box-shadow: 0 0 12px #dfb15b;
    }

    h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
        color: #f4f4f5 !important;
        border-left: 3px solid #dfb15b;
        padding-left: 12px;
        margin-top: 2.5rem !important;
        margin-bottom: 1.25rem !important;
        font-size: 1.25rem;
    }

    /* Atelier Status Banners */
    div.stAlert {
        background: rgba(14, 14, 18, 0.9) !important;
        border: 1px solid rgba(223, 177, 91, 0.25) !important;
        border-radius: 8px !important;
        color: #f4f4f5 !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }

    /* Atelier Luxury Table Container */
    .atelier-table-wrapper {
        background: #0e0e12;
        border: 1px solid rgba(223, 177, 91, 0.15);
        border-radius: 12px;
        padding: 2px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8), 0 0 20px rgba(223, 177, 91, 0.03);
        margin-bottom: 2rem;
        overflow-x: auto;
        animation: atelierFade 0.5s ease-out forwards;
    }

    /* Specific scrollable container for 10 rows */
    .atelier-table-scroll-container {
        max-height: 480px;
        overflow-y: auto;
    }

    .atelier-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Space Grotesk', monospace;
        font-size: 0.82rem;
        text-align: left;
        white-space: nowrap;
    }

    .atelier-table th {
        background: #141419;
        color: #dfb15b;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.1em;
        padding: 14px 16px;
        border-bottom: 1px solid rgba(223, 177, 91, 0.2);
        position: sticky;
        top: 0;
        z-index: 10;
    }

    .atelier-table td {
        padding: 12px 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        color: #d4d4d8;
        transition: background 0.2s ease;
    }

    .atelier-table tbody tr:hover td {
        background: rgba(223, 177, 91, 0.04);
        color: #ffffff;
    }

    /* Typography Color Highlights */
    .atelier-positive {
        color: #34d399 !important;
        font-weight: 600;
    }

    .atelier-negative {
        color: #f87171 !important;
        font-weight: 600;
    }

    .atelier-warning {
        color: #facc15 !important;
        font-weight: 600;
    }

    .atelier-badge-bullish {
        background: rgba(52, 211, 153, 0.1);
        color: #34d399;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 700;
        border: 1px solid rgba(52, 211, 153, 0.25);
    }

    .atelier-badge-bearish {
        background: rgba(248, 113, 113, 0.1);
        color: #f87171;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 700;
        border: 1px solid rgba(248, 113, 113, 0.25);
    }

    .atelier-badge-neutral {
        background: rgba(161, 161, 170, 0.1);
        color: #a1a1aa;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 700;
        border: 1px solid rgba(161, 161, 170, 0.25);
    }

    .atelier-symbol-link {
        color: #dfb15b;
        text-decoration: none;
        font-weight: 600;
        transition: color 0.2s;
    }

    .atelier-symbol-link:hover {
        color: #fcd34d;
        text-decoration: underline;
    }

    /* Atelier Selectbox */
    div[data-baseweb="select"] > div {
        background-color: #0e0e12 !important;
        border: 1px solid rgba(223, 177, 91, 0.3) !important;
        border-radius: 8px !important;
        color: #f4f4f5 !important;
    }

    div[data-baseweb="select"] span {
        color: #f4f4f5 !important;
    }

    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #060608;
    }
    ::-webkit-scrollbar-thumb {
        background: #27272a;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #dfb15b;
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
    if vol >= 1_000_000:
        return f"{vol / 1_000_000:.2f}M"
    elif vol >= 1_000:
        return f"{vol / 1_000:.1f}K"
    return str(int(vol))

def format_signed_pct(val):
    return f"+{val:.2f}%" if val > 0 else f"{val:.2f}%"

def render_atelier_table(df, columns_to_show, enable_scroll=False, color_vol_ratios=False):
    """Renders the Atelier luxury gold-trimmed table with optional scrolling and volume coloring."""
    if df.empty:
        st.info("No data available to display.")
        return

    wrapper_class = "atelier-table-wrapper atelier-table-scroll-container" if enable_scroll else "atelier-table-wrapper"
    html = f'<div class="{wrapper_class}"><table class="atelier-table"><thead><tr>'
    
    display_cols = [c for c in columns_to_show if c in df.columns]
    header_names = {
        'CHART_URL': 'Symbol',
        'SECTOR': 'Sector',
        'LTP (₹)': 'LTP (₹)',
        'Change %': 'Change %',
        'VWAP Dist %': 'VWAP Dist %',
        'Volume': 'Volume',
        'Vol / 1D Vol': 'Vol / 1D Vol',
        'Vol / 5D Vol': 'Vol / 5D Vol',
        'Vol / 10D Vol': 'Vol / 10D Vol',
        'Vol / 20D Vol': 'Vol / 20D Vol',
        'Order Flow': 'Order Flow',
        'Position Builder Score': 'Pos Builder Score',
        'Inst. Score': 'Inst. Score',
        'Avg Change %': 'Avg Change %',
        'Adv/Dec': 'Adv/Dec',
        'Breadth Ratio': 'Breadth Ratio',
        'Avg Order Flow': 'Avg Order Flow',
        'Top Stock': 'Top Stock',
        'Sector Momentum': 'Sector Momentum'
    }

    for col in display_cols:
        html += f"<th>{header_names.get(col, col)}</th>"
    html += "</tr></thead><tbody>"

    vol_ratio_cols = ['Vol / 1D Vol', 'Vol / 5D Vol', 'Vol / 10D Vol', 'Vol / 20D Vol']

    for _, row in df.iterrows():
        html += "<tr>"
        for col in display_cols:
            val = row[col]
            str_val = str(val)
            
            if col == 'CHART_URL':
                symbol_name = row.get('SYMBOL', str_val)
                url = str_val
                cell_content = f'<a href="{url}" target="_blank" class="atelier-symbol-link">{symbol_name} ↗</a>'
            elif color_vol_ratios and col in vol_ratio_cols:
                clean_val = str_val.replace('x', '').strip()
                try:
                    f_val = float(clean_val)
                    if f_val > 1.2:
                        cls = "atelier-positive"
                    elif f_val < 0.8:
                        cls = "atelier-negative"
                    else:
                        cls = "atelier-warning"
                    cell_content = f'<span class="{cls}">{str_val}</span>'
                except:
                    cell_content = str_val
            elif any(k in col.lower() for k in ['change', 'dist']):
                clean_val = str_val.replace('%', '').replace('+', '').strip()
                try:
                    f_val = float(clean_val)
                    cls = "atelier-positive" if f_val > 0 else ("atelier-negative" if f_val < 0 else "")
                    cell_content = f'<span class="{cls}">{str_val}</span>'
                except:
                    cell_content = str_val
            elif col == 'Sector Momentum':
                if str_val == 'BULLISH':
                    cell_content = f'<span class="atelier-badge-bullish">{str_val}</span>'
                elif str_val == 'BEARISH':
                    cell_content = f'<span class="atelier-badge-bearish">{str_val}</span>'
                else:
                    cell_content = f'<span class="atelier-badge-neutral">{str_val}</span>'
            else:
                cell_content = str_val

            html += f"<td>{cell_content}</td>"
        html += "</tr>"
    html += "</tbody></table></div>"
    
    st.markdown(html, unsafe_allow_html=True)

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

def _fetch_single_historical_vols(key, access_token, to_date, from_date):
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token}'}
    encoded_key = urllib.parse.quote(key, safe='|:')
    url = f"https://api.upstox.com/v2/historical-candle/{encoded_key}/day/{to_date}/{from_date}"
    
    for attempt in range(2):
        try:
            res = requests.get(url, headers=headers, timeout=4)
            if res.status_code == 200:
                candles = res.json().get('data', {}).get('candles', [])
                if len(candles) > 1:
                    # candles are usually in descending order: index 0 is current/latest incomplete day, index 1 is previous complete day (1D)
                    history_vols = [c[5] for c in candles[1:]] # exclude index 0 if today, or include past days
                    vol_1d = history_vols[0] if len(history_vols) > 0 else 0.0
                    vol_5d = sum(history_vols[:5]) / len(history_vols[:5]) if len(history_vols) >= 5 else (sum(history_vols) / len(history_vols) if history_vols else 0.0)
                    vol_10d = sum(history_vols[:10]) / len(history_vols[:10]) if len(history_vols) >= 10 else (sum(history_vols) / len(history_vols) if history_vols else 0.0)
                    vol_20d = sum(history_vols[:20]) / len(history_vols[:20]) if len(history_vols) >= 20 else (sum(history_vols) / len(history_vols) if history_vols else 0.0)
                    return key, {'1d': vol_1d, '5d': vol_5d, '10d': vol_10d, '20d': vol_20d}
            elif res.status_code == 429:
                time.sleep(0.25)
        except Exception:
            pass
    return key, {'1d': 0.0, '5d': 0.0, '10d': 0.0, '20d': 0.0}

@st.cache_data(ttl=86400)
def fetch_historical_avg_volumes_throttled(instrument_keys, access_token):
    today = datetime.now(IST)
    from_date = (today - timedelta(days=35)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    
    avg_volumes = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(_fetch_single_historical_vols, key, access_token, to_date, from_date)
            for key in instrument_keys
        ]
        for future in as_completed(futures):
            key, v_dict = future.result()
            avg_volumes[key] = v_dict
            avg_volumes[key.replace('|', ':')] = v_dict
            avg_volumes[key.replace(':', '|')] = v_dict
            
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

def process_market_data(mapped_df, quotes_dict, historical_vol_dict):
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
        
        v_dict = historical_vol_dict.get(key, {}) or historical_vol_dict.get(symbol, {})
        vol_1d_avg = v_dict.get('1d', 0.0)
        vol_5d_avg = v_dict.get('5d', 0.0)
        vol_10d_avg = v_dict.get('10d', 0.0)
        vol_20d_avg = v_dict.get('20d', 0.0)

        vol_ratio_1d = (volume / vol_1d_avg) if vol_1d_avg > 0 else 1.0
        vol_ratio_5d = (volume / vol_5d_avg) if vol_5d_avg > 0 else 1.0
        vol_ratio_10d = (volume / vol_10d_avg) if vol_10d_avg > 0 else 1.0
        vol_ratio_20d = (volume / vol_20d_avg) if vol_20d_avg > 0 else 1.0

        vol_ratio_capped = min(vol_ratio_10d, 10.0)
        
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
            'Vol / 1D Vol': f"{vol_ratio_1d:.2f}x",
            'Vol / 5D Vol': f"{vol_ratio_5d:.2f}x",
            'Vol / 10D Vol': f"{vol_ratio_10d:.2f}x",
            'Vol / 20D Vol': f"{vol_ratio_20d:.2f}x",
            'FLOW_RATIO_RAW': round(flow_ratio, 2),
            'Order Flow': f"{flow_ratio:.2f}x",
            'POS_BUILDER_SCORE': position_builder_score,
            'INST_SCORE': round(inst_score, 2),
        })
        
    df = pd.DataFrame(records)
    if not df.empty and 'POS_BUILDER_SCORE' not in df.columns:
        df['POS_BUILDER_SCORE'] = 0.0
    return df

# ==========================================
# 2. TIME CONTROL
# ==========================================
def is_market_open():
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    start_time = now.replace(hour=9, minute=14, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=13, second=0, microsecond=0)
    return start_time <= now <= end_time

# ==========================================
# 3. STREAMLIT RENDER LOGIC
# ==========================================
st.title("F&O Institutional Sector Radar")

with st.spinner("Initializing Market Mapping & Historical Volumes..."):
    mapped_df = load_instrument_mapping(FNO_EXCEL_PATH, INSTRUMENTS_CSV_PATH)
    unique_keys = mapped_df['instrument_key'].unique().tolist()
    historical_vols = fetch_historical_avg_volumes_throttled(unique_keys, ACCESS_TOKEN)

@st.fragment(run_every=REFRESH_INTERVAL_SECONDS if is_market_open() else None)
def dashboard_live_loop():
    market_status = is_market_open()
    now = datetime.now(IST)
    now_str = now.strftime("%H:%M:%S IST")
    today_str = now.strftime("%Y-%m-%d")

    # Reset cache if a new trading day starts
    if 'frozen_date' in st.session_state and st.session_state['frozen_date'] != today_str:
        st.session_state.pop('frozen_df', None)
        st.session_state.pop('frozen_time', None)
        st.session_state.pop('frozen_date', None)

    if market_status:
        st.success(f"🟢 **MARKET LIVE** — Last Updated: {now_str}")
        quotes, api_error = fetch_live_quotes_safe(unique_keys, ACCESS_TOKEN)
        data_df = process_market_data(mapped_df, quotes, historical_vols)
        
        if not data_df.empty:
            st.session_state['frozen_df'] = data_df
            st.session_state['frozen_time'] = now_str
            st.session_state['frozen_date'] = today_str
    else:
        if 'frozen_df' in st.session_state and not st.session_state['frozen_df'].empty:
            data_df = st.session_state['frozen_df']
            frozen_at = st.session_state.get('frozen_time', '3:13:00 IST')
            st.warning(f"🔴 **MARKET CLOSED — FROZEN AT 3:13 PM IST** (Data locked at: {frozen_at})")
            api_error = None
        else:
            st.warning(f"🔴 **MARKET CLOSED** — Fetching final 3:13 PM market snapshot. Current time: {now_str}")
            quotes, api_error = fetch_live_quotes_safe(unique_keys, ACCESS_TOKEN)
            data_df = process_market_data(mapped_df, quotes, historical_vols)
            if not data_df.empty:
                st.session_state['frozen_df'] = data_df
                st.session_state['frozen_time'] = now_str
                st.session_state['frozen_date'] = today_str

    if data_df.empty:
        st.error("⚠️ **Unable to load live quotes from Upstox API.**")
        if 'api_error' in locals() and api_error:
            st.code(f"Upstox Response Error Log:\n{api_error}", language="text")
        return

    if 'POS_BUILDER_SCORE' not in data_df.columns:
        data_df['POS_BUILDER_SCORE'] = 0.0

    # --- Sector Summary Table ---
    st.subheader("Sector Performance Breakdown")
    sector_stats = []
    for sector, group in data_df.groupby('SECTOR'):
        avg_chg = group['CHANGE_%'].mean()
        advances = (group['CHANGE_%'] > 0).sum()
        declines = (group['CHANGE_%'] < 0).sum()
        total_stocks = len(group)
        breadth_ratio = (advances - declines) / total_stocks if total_stocks > 0 else 0.0
        top_stock = group.loc[group['INST_SCORE'].idxmax()]['SYMBOL'] if not group.empty else "N/A"
        sector_score = avg_chg + (0.75 * breadth_ratio)
        
        sector_stats.append({
            "Sector": sector,
            "Avg Change %": format_signed_pct(avg_chg),
            "Adv/Dec": f"{advances}/{declines}",
            "Breadth Ratio": f"{breadth_ratio:+.2f}",
            "Avg Order Flow": f"{group['FLOW_RATIO_RAW'].mean():.2f}x",
            "Top Stock": top_stock,
            "Sector Momentum": "BULLISH" if sector_score > 0.3 else ("BEARISH" if sector_score < -0.3 else "NEUTRAL"),
            "_SORT_CHG": avg_chg
        })
    
    sector_df = pd.DataFrame(sector_stats).sort_values(by="_SORT_CHG", ascending=False).drop(columns=['_SORT_CHG'])
    render_atelier_table(sector_df, ['Sector', 'Avg Change %', 'Adv/Dec', 'Breadth Ratio', 'Avg Order Flow', 'Top Stock', 'Sector Momentum'])

    # --- Deduplicate Stocks for Leaders ---
    unique_symbols_df = data_df.drop_duplicates(subset=['SYMBOL'])

    # --- Active Position Builder Spotlight Table ---
    st.subheader("Active Position Builder Spotlight (High Conviction)")
    active_pb_df = unique_symbols_df.sort_values(by='POS_BUILDER_SCORE', ascending=False).head(20).copy()
    active_pb_df.rename(columns={'CHANGE_STR': 'Change %', 'POS_BUILDER_SCORE': 'Position Builder Score', 'INST_SCORE': 'Inst. Score'}, inplace=True)
    cols_pb = ['CHART_URL', 'SECTOR', 'LTP (₹)', 'Change %', 'Volume', 'Vol / 1D Vol', 'Vol / 5D Vol', 'Vol / 10D Vol', 'Vol / 20D Vol', 'Position Builder Score', 'Inst. Score']
    render_atelier_table(active_pb_df, cols_pb, enable_scroll=True, color_vol_ratios=True)

    # --- Display Count Selection ---
    display_option = st.selectbox(
        "Select Number of Stocks to Display:",
        options=["Top 10", "Top 20", "All"],
        index=0
    )

    if display_option == "Top 10":
        top_n = 10
        label_prefix = "Top 10"
    elif display_option == "Top 20":
        top_n = 20
        label_prefix = "Top 20"
    else:
        top_n = None
        label_prefix = "All"

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"{label_prefix} Bullish Momentum Leaders")
        bullish = unique_symbols_df.sort_values(by='INST_SCORE', ascending=False)
        if top_n is not None:
            bullish = bullish.head(top_n)
        bullish = bullish.copy()
        bullish.rename(columns={'CHANGE_STR': 'Change %', 'VWAP_DIST_STR': 'VWAP Dist %', 'INST_SCORE': 'Inst. Score'}, inplace=True)
        cols_bullish = ['CHART_URL', 'SECTOR', 'LTP (₹)', 'Change %', 'VWAP Dist %', 'Volume', 'Vol / 1D Vol', 'Vol / 5D Vol', 'Vol / 10D Vol', 'Vol / 20D Vol', 'Order Flow', 'Inst. Score']
        render_atelier_table(bullish, cols_bullish)

    with col2:
        st.subheader(f"{label_prefix} Bearish Short Setups")
        bearish = unique_symbols_df.sort_values(by='INST_SCORE', ascending=True)
        if top_n is not None:
            bearish = bearish.head(top_n)
        bearish = bearish.copy()
        bearish.rename(columns={'CHANGE_STR': 'Change %', 'VWAP_DIST_STR': 'VWAP Dist %', 'INST_SCORE': 'Inst. Score'}, inplace=True)
        cols_bearish = ['CHART_URL', 'SECTOR', 'LTP (₹)', 'Change %', 'VWAP Dist %', 'Volume', 'Vol / 1D Vol', 'Vol / 5D Vol', 'Vol / 10D Vol', 'Vol / 20D Vol', 'Order Flow', 'Inst. Score']
        render_atelier_table(bearish, cols_bearish)

dashboard_live_loop()

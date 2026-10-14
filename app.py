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
# PAGE CONFIGURATION & ULTRA-LUXURY UI
# ==========================================
st.set_page_config(
    page_title="F&O Institutional Sector Radar",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ultra-Luxury, Haute-Finance Obsidian & Champagne Gold Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@200;300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

    /* Deep Obsidian & Micro-Starlight Canvas */
    .stApp {
        background-color: #06080d;
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(212, 175, 55, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 100% 100%, rgba(56, 189, 248, 0.03) 0%, transparent 40%);
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #f1f5f9;
    }

    code, pre {
        font-family: 'Space Mono', monospace !important;
    }

    /* Ultra-Smooth Luxury Entrance Animation */
    @keyframes luxuryReveal {
        0% { opacity: 0; transform: translateY(16px); filter: blur(4px); }
        100% { opacity: 1; transform: translateY(0); filter: blur(0px); }
    }

    .main .block-container {
        animation: luxuryReveal 0.9s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        padding-top: 3rem;
        padding-bottom: 5rem;
        max-width: 98%;
    }

    /* Champagne Gold Gradient Headers */
    h1 {
        font-weight: 700 !important;
        letter-spacing: -0.04em;
        background: linear-gradient(135deg, #ffffff 20%, #e2b714 60%, #fff6bd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.75rem !important;
    }

    h2, h3 {
        font-weight: 600 !important;
        letter-spacing: -0.02em;
        color: #f8fafc !important;
        border-bottom: 1px solid rgba(212, 175, 55, 0.15);
        padding-bottom: 0.85rem;
        margin-top: 3rem !important;
        margin-bottom: 1.25rem !important;
    }

    /* Frosted Titanium Status Boxes */
    div.stAlert {
        background: rgba(13, 17, 23, 0.8) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(212, 175, 55, 0.2) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
    }

    /* Elite Floating Table Container */
    .luxury-table-panel {
        background: rgba(10, 14, 22, 0.65);
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 4px;
        box-shadow: 0 30px 70px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(212, 175, 55, 0.1);
        margin-bottom: 2rem;
        overflow-x: auto;
        animation: luxuryReveal 0.8s ease-out forwards;
        transition: all 0.4s ease;
    }

    .luxury-table-panel:hover {
        border-color: rgba(212, 175, 55, 0.35);
        box-shadow: 0 35px 90px rgba(0, 0, 0, 0.9), 0 0 25px rgba(212, 175, 55, 0.05);
    }

    /* Precision Financial Grid */
    .luxury-grid {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Space Mono', monospace;
        font-size: 0.82rem;
        text-align: left;
        white-space: nowrap;
    }

    .luxury-grid th {
        background: rgba(18, 24, 38, 0.9);
        color: #94a3b8;
        font-weight: 500;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.1em;
        padding: 15px 20px;
        border-bottom: 1px solid rgba(212, 175, 55, 0.2);
        position: sticky;
        top: 0;
        z-index: 10;
    }

    .luxury-grid td {
        padding: 14px 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        color: #e2e8f0;
        transition: background 0.2s ease;
    }

    .luxury-grid tbody tr:hover td {
        background: rgba(212, 175, 55, 0.04);
    }

    /* Numeric Glow & Status Pills */
    .price-up {
        color: #34d399 !important;
        font-weight: 600;
    }

    .price-down {
        color: #fb7185 !important;
        font-weight: 600;
    }

    .pill-bullish {
        background: rgba(52, 211, 153, 0.1);
        color: #34d399;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        border: 1px solid rgba(52, 211, 153, 0.25);
    }

    .pill-bearish {
        background: rgba(251, 113, 133, 0.1);
        color: #fb7185;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        border: 1px solid rgba(251, 113, 133, 0.25);
    }

    .pill-neutral {
        background: rgba(148, 163, 184, 0.1);
        color: #94a3b8;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        border: 1px solid rgba(148, 163, 184, 0.25);
    }

    .symbol-link-gold {
        color: #facc15;
        text-decoration: none;
        font-weight: 700;
        transition: color 0.2s;
    }

    .symbol-link-gold:hover {
        color: #fde047;
        text-decoration: underline;
    }

    /* Premium Dropdown Controls */
    div[data-baseweb="select"] > div {
        background-color: rgba(13, 17, 23, 0.85) !important;
        border: 1px solid rgba(212, 175, 55, 0.25) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        backdrop-filter: blur(16px);
    }

    div[data-baseweb="select"] span {
        color: #f8fafc !important;
    }

    /* Custom Minimal Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #06080d;
    }
    ::-webkit-scrollbar-thumb {
        background: #1e293b;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #d4af37;
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

def render_luxury_table(df, columns_to_show):
    """Renders a high-end luxury obsidian-gold financial grid table."""
    if df.empty:
        st.info("No data available to display.")
        return

    html = '<div class="luxury-table-panel"><table class="luxury-grid"><thead><tr>'
    
    display_cols = [c for c in columns_to_show if c in df.columns]
    header_names = {
        'CHART_URL': 'Symbol',
        'SECTOR': 'Sector',
        'LTP (₹)': 'LTP (₹)',
        'Change %': 'Change %',
        'VWAP Dist %': 'VWAP Dist %',
        'Volume': 'Volume',
        'Vol / 10D Vol': 'Vol / 10D Vol',
        'Order Flow': 'Order Flow',
        'Position Builder Score': 'Pos Builder Score',
        'Inst. Score': 'Inst. Score',
        'Sector': 'Sector',
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

    for _, row in df.iterrows():
        html += "<tr>"
        for col in display_cols:
            val = row[col]
            str_val = str(val)
            
            if col == 'CHART_URL':
                symbol_name = row.get('SYMBOL', str_val)
                url = str_val
                cell_content = f'<a href="{url}" target="_blank" class="symbol-link-gold">{symbol_name} ↗</a>'
            elif any(k in col.lower() for k in ['change', 'dist']):
                clean_val = str_val.replace('%', '').replace('+', '').strip()
                try:
                    f_val = float(clean_val)
                    cls = "price-up" if f_val > 0 else ("price-down" if f_val < 0 else "")
                    cell_content = f'<span class="{cls}">{str_val}</span>'
                except:
                    cell_content = str_val
            elif col == 'Sector Momentum':
                if str_val == 'BULLISH':
                    cell_content = f'<span class="pill-bullish">{str_val}</span>'
                elif str_val == 'BEARISH':
                    cell_content = f'<span class="pill-bearish">{str_val}</span>'
                else:
                    cell_content = f'<span class="pill-neutral">{str_val}</span>'
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
            'Vol / 10D Vol': f"{vol_ratio:.2f}x",
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
st.title("⚡F&O Institutional Sector Radar")

with st.spinner("Initializing Market Mapping & Historical Volumes..."):
    mapped_df = load_instrument_mapping(FNO_EXCEL_PATH, INSTRUMENTS_CSV_PATH)
    unique_keys = mapped_df['instrument_key'].unique().tolist()
    avg_10d_vols = fetch_10d_avg_volumes_throttled(unique_keys, ACCESS_TOKEN)

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
        data_df = process_market_data(mapped_df, quotes, avg_10d_vols)
        
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
            data_df = process_market_data(mapped_df, quotes, avg_10d_vols)
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
    render_luxury_table(sector_df, ['Sector', 'Avg Change %', 'Adv/Dec', 'Breadth Ratio', 'Avg Order Flow', 'Top Stock', 'Sector Momentum'])

    # --- Deduplicate Stocks for Leaders ---
    unique_symbols_df = data_df.drop_duplicates(subset=['SYMBOL'])

    # --- Active Position Builder Spotlight Table ---
    st.subheader("🔥 Active Position Builder Spotlight (High Conviction)")
    active_pb_df = unique_symbols_df.sort_values(by='POS_BUILDER_SCORE', ascending=False).head(10).copy()
    active_pb_df.rename(columns={'CHANGE_STR': 'Change %', 'POS_BUILDER_SCORE': 'Position Builder Score', 'INST_SCORE': 'Inst. Score'}, inplace=True)
    cols_pb = ['CHART_URL', 'SECTOR', 'LTP (₹)', 'Change %', 'Volume', 'Vol / 10D Vol', 'Position Builder Score', 'Inst. Score']
    render_luxury_table(active_pb_df, cols_pb)

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
        cols_bullish = ['CHART_URL', 'SECTOR', 'LTP (₹)', 'Change %', 'VWAP Dist %', 'Volume', 'Vol / 10D Vol', 'Order Flow', 'Inst. Score']
        render_luxury_table(bullish, cols_bullish)

    with col2:
        st.subheader(f"{label_prefix} Bearish Short Setups")
        bearish = unique_symbols_df.sort_values(by='INST_SCORE', ascending=True)
        if top_n is not None:
            bearish = bearish.head(top_n)
        bearish = bearish.copy()
        bearish.rename(columns={'CHANGE_STR': 'Change %', 'VWAP_DIST_STR': 'VWAP Dist %', 'INST_SCORE': 'Inst. Score'}, inplace=True)
        cols_bearish = ['CHART_URL', 'SECTOR', 'LTP (₹)', 'Change %', 'VWAP Dist %', 'Volume', 'Vol / 10D Vol', 'Order Flow', 'Inst. Score']
        render_luxury_table(bearish, cols_bearish)

dashboard_live_loop()

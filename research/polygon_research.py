#!/usr/bin/env python3
"""
Polygon.io Research: 500 tickers, Close → 4 AM pre-market, 1 year hourly.
Uses Polygon.io API (free tier ~148 days of hourly data).
"""
import os, sys, time, json, warnings
warnings.filterwarnings('ignore')
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = os.environ.get('POLYGON_API_KEY', '')
if not API_KEY:
    print("ERROR: Set POLYGON_API_KEY env var")
    sys.exit(1)

# 500 tickers
TICKERS = [
    "AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA","NFLX","AMD","INTC",
    "QCOM","CRM","ADBE","PYPL","UBER","ABNB","COIN","PLTR","SNOW","ZM",
    "ROKU","SQ","SHOP","CRWD","NET","DDOG","FSLY","DOCU","OKTA","TWLO",
    "ABBV","ABT","ACN","ADP","AIG","ALL","AMAT","AMGN","AMP","AMT",
    "ANET","AON","APA","APD","APH","APO","ARE","ATO","AVB","AVGO",
    "AXP","AZO","BA","BAC","BAX","BDX","BEN","BG","BIIB","BIO","BK",
    "BKNG","BKR","BLK","BMY","BR","BRO","BSX","BWA","BX","C","CAG",
    "CAH","CAT","CB","CBOE","CBRE","CCI","CCL","CDNS","CDW","CE","CF",
    "CFG","CHD","CHRW","CHTR","CI","CINF","CL","CLX","CMCSA","CME",
    "CMG","CMI","CMS","CNC","CNP","COF","COO","COP","COST","CPB",
    "CPRT","CPT","CRL","CSGP","CSX","CTAS","CTRA","CTSH","CTVA","CVS",
    "CVX","D","DAL","DD","DE","DG","DGX","DHI","DHR","DIS","DLR",
    "DLTR","DOV","DOW","DPZ","DRI","DTE","DUK","DVA","DVN","DXC",
    "DXCM","EA","EBAY","ECL","ED","EFX","EG","EL","ELV","EMN","EMR",
    "ENPH","EOG","EPAM","EQIX","EQR","EQT","ES","ESS","ETN","ETR",
    "EW","EXC","EXPD","EXPE","EXR","F","FAST","FCX","FDS","FDX",
    "FE","FFIV","FICO","FIS","FITB","FMC","FOX","FOXA","FRT","FSLR",
    "FTNT","FTV","GD","GE","GEHC","GILD","GIS","GL","GPC","GPN",
    "GRMN","GS","GWW","HAL","HAS","HBAN","HCA","HD","HES","HIG",
    "HII","HLT","HOLX","HON","HPE","HPQ","HRL","HSIC","HST","HSY",
    "HUBB","HUM","IBM","ICE","IDXX","IEX","IFF","ILMN","INCY","INTU",
    "INVH","IP","IQV","IR","IRM","ISRG","IT","ITW","IVZ","J","JBHT",
    "JBL","JCI","JKHY","JNJ","JNPR","JPM","K","KDP","KEY","KEYS",
    "KHC","KIM","KKR","KLAC","KMB","KMI","KMX","KO","KR","KVUE","L",
    "LDOS","LEN","LH","LHX","LIN","LKQ","LLY","LMT","LNT","LOW","LRCX",
    "LULU","LUV","LVS","LW","LYB","LYV","MA","MAA","MAR","MAS","MCD",
    "MCHP","MCK","MCO","MDLZ","MDT","MET","MGM","MHK","MKC","MKTX",
    "MLM","MMC","MMM","MNST","MO","MOH","MOS","MPC","MPWR","MRK",
    "MRNA","MRO","MS","MSCI","MSFT","MSI","MTB","MTCH","MTD","MU",
    "NCLH","NDAQ","NEE","NEM","NFLX","NI","NKE","NOC","NOW","NRG",
    "NSC","NTRS","NUE","NVDA","NVR","NWS","NWSA","NXPI","O","ODFL",
    "OKE","OMC","ON","ORCL","ORLY","OTIS","OXY","PANW","PARA","PAYC",
    "PAYX","PCAR","PCG","PEG","PEP","PFE","PFG","PG","PGR","PH",
    "PHM","PKG","PLD","PM","PNC","PNR","PNW","PPG","PPL","PRU",
    "PSA","PSX","PTC","PVH","PWR","QCOM","QRVO","RCL","REG","REGN",
    "RF","RHI","RJF","RL","RMD","ROK","ROL","ROP","ROST","RRC",
    "RSG","RTX","RVTY","SBAC","SBUX","SCHW","SEE","SHW","SJM","SLB",
    "SNPS","SO","SPG","SPGI","SRE","STE","STLD","STT","STX","STZ",
    "SWK","SWKS","SYF","SYK","SYY","T","TAP","TDG","TDY","TECH",
    "TEL","TER","TFC","TFX","TGT","TJX","TMO","TMUS","TPR","TRMB",
    "TROW","TRV","TSLA","TSN","TT","TTWO","TXN","TXT","TYL","UAL",
    "UDR","UHS","ULTA","UNH","UNP","UPS","URI","USB","V","VFC",
    "VICI","VLO","VMC","VRSK","VRSN","VRTX","VST","VTR","VTRS","VZ",
    "WAB","WAT","WBA","WBD","WDC","WEC","WELL","WFC","WHR","WM",
    "WMB","WMT","WRB","WST","WTW","WY","WYNN","XEL","XOM","XYL",
    "YUM","ZBH","ZION","ZTS"
]

def fetch_polygon_hourly(ticker, days_back=365):
    """Fetch hourly data from Polygon.io with pagination."""
    end = datetime.now()
    start = end - timedelta(days=days_back)
    
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/hour/{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}"
    params = {'apiKey': API_KEY, 'limit': 50000}
    
    all_results = []
    page = 0
    
    while url and page < 20:  # Max 20 pages
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code != 200:
                break
            data = resp.json()
            results = data.get('results', [])
            all_results.extend(results)
            
            url = data.get('next_url')
            params = None
            page += 1
            
            if not results:
                break
        except Exception as e:
            break
    
    if not all_results:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(all_results)
    df['datetime'] = pd.to_datetime(df['t'], unit='ms')
    df = df.set_index('datetime')
    df = df.rename(columns={'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close', 'v': 'Volume'})
    
    return df[['Open', 'High', 'Low', 'Close', 'Volume']]

def compute_4am_returns(df):
    """Compute Close → 4 AM pre-market returns."""
    df = df.copy()
    df['Date'] = df.index.date
    df['Hour'] = df.index.hour
    
    daily = []
    dates = sorted(df['Date'].unique())
    
    for i in range(len(dates) - 1):
        today = dates[i]
        next_day = dates[i + 1]
        
        # Today's close (last bar before 16:00 or 15:00)
        today_data = df[df['Date'] == today]
        if len(today_data) == 0:
            continue
        close_price = today_data['Close'].iloc[-1]
        
        # Next day 4 AM (first pre-market bar)
        next_day_data = df[df['Date'] == next_day]
        if len(next_day_data) == 0:
            continue
        
        # Find 4 AM bar
        four_am = next_day_data[next_day_data['Hour'] == 4]
        if len(four_am) == 0:
            # Try 5 AM if 4 AM not available
            four_am = next_day_data[next_day_data['Hour'] == 5]
        
        if len(four_am) == 0:
            continue
        
        four_am_price = four_am['Open'].iloc[0]
        overnight_ret = (four_am_price / close_price - 1) * 100
        
        daily.append({
            'Date': today,
            'Close': close_price,
            'FourAM': four_am_price,
            'OvernightReturn': overnight_ret,
            'Volume': today_data['Volume'].sum(),
        })
    
    if len(daily) < 10:
        return None
    
    return pd.DataFrame(daily)

def add_indicators(df):
    """Add RSI, BB, MACD to hourly data."""
    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(20).mean()
    bb_std = df['Close'].rolling(20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    df['BB_Position'] = ((df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])) * 100
    df['BB_Width'] = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']) * 100
    
    # MACD
    ema_fast = df['Close'].ewm(span=12, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_fast - ema_slow
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # ATR
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['ATR_Pct'] = (df['ATR'] / df['Close']) * 100
    
    return df

def extract_features(df_hourly, df_daily):
    """Extract indicator values at close and overnight returns."""
    records = []
    
    for _, row in df_daily.iterrows():
        date = row['Date']
        day_data = df_hourly[pd.to_datetime(df_hourly.index.date) == pd.Timestamp(date)]
        
        if len(day_data) == 0:
            continue
        
        last_bar = day_data.iloc[-1]
        
        if pd.notna(last_bar['RSI']):
            records.append({
                'Date': date,
                'Close': row['Close'],
                'FourAM': row['FourAM'],
                'OvernightReturn': row['OvernightReturn'],
                'Volume': row['Volume'],
                'RSI': round(last_bar['RSI'], 2),
                'ATR_Pct': round(last_bar['ATR_Pct'], 3) if pd.notna(last_bar['ATR_Pct']) else None,
                'BB_Position': round(last_bar['BB_Position'], 2) if pd.notna(last_bar['BB_Position']) else None,
                'BB_Width': round(last_bar['BB_Width'], 2) if pd.notna(last_bar['BB_Width']) else None,
                'MACD': round(last_bar['MACD'], 4) if pd.notna(last_bar['MACD']) else None,
                'MACD_Hist': round(last_bar['MACD_Hist'], 4) if pd.notna(last_bar['MACD_Hist']) else None,
                'DayOfWeek': pd.Timestamp(date).day_name(),
                'Hour': last_bar.name.hour if hasattr(last_bar.name, 'hour') else None,
            })
    
    if len(records) < 10:
        return None
    
    return pd.DataFrame(records)

def process_ticker(ticker):
    """Process one ticker: fetch, compute returns, extract features."""
    try:
        df_hourly = fetch_polygon_hourly(ticker)
        if df_hourly is None:
            return None
        
        df_hourly = add_indicators(df_hourly)
        df_daily = compute_4am_returns(df_hourly)
        
        if df_daily is None:
            return None
        
        features = extract_features(df_hourly, df_daily)
        if features is None:
            return None
        
        features['Ticker'] = ticker
        return features
    except Exception as e:
        return None

def run_polygon_research(max_tickers=500, max_workers=5):
    print("="*70)
    print("POLYGON.IO RESEARCH: Close → 4 AM Pre-Market")
    print(f"Testing {max_tickers} tickers, ~1 year hourly data...")
    print("="*70)
    
    all_results = []
    processed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_ticker, t): t for t in TICKERS[:max_tickers]}
        
        for future in as_completed(futures):
            ticker = futures[future]
            result = future.result()
            
            if result is not None:
                all_results.append(result)
                processed += 1
                if processed % 50 == 0:
                    print(f"  ... {processed} tickers processed")
            else:
                print(f"  {ticker}: skipped")
    
    if not all_results:
        print("ERROR: No data retrieved")
        return None
    
    results = pd.concat(all_results, ignore_index=True)
    print(f"\n✅ Polygon research complete: {len(results):,} observations across {results['Ticker'].nunique()} tickers")
    
    # Save
    results.to_csv('research/polygon_4am_results.csv', index=False)
    print(f"💾 Saved to: research/polygon_4am_results.csv")
    
    return results

def analyze(results):
    print("\n" + "="*70)
    print("POLYGON ANALYSIS: Close → 4 AM Pre-Market")
    print("="*70)
    
    baseline_wr = (results['OvernightReturn'] > 0).mean() * 100
    baseline_avg = results['OvernightReturn'].mean()
    print(f"Baseline (all days): WinRate={baseline_wr:.2f}%, AvgReturn={baseline_avg:.4f}%")
    print(f"Total: {len(results):,} observations, {results['Ticker'].nunique()} tickers")
    
    # Define bins
    results['RSI_Bin'] = pd.cut(results['RSI'], bins=[0, 30, 40, 50, 60, 70, 100],
                                labels=['<30','30-40','40-50','50-60','60-70','>70'])
    results['BB_Bin'] = pd.cut(results['BB_Position'], bins=[0, 10, 30, 50, 70, 90, 100],
                               labels=['<10%','10-30%','30-50%','50-70%','70-90%','>90%'])
    
    # Single indicators
    print("\n--- Single Indicators ---")
    for col, name in [('RSI_Bin', 'RSI'), ('BB_Bin', 'BB Position')]:
        stats = results.groupby(col).agg(
            Count=('OvernightReturn', 'count'),
            WinRate=('OvernightReturn', lambda x: (x > 0).mean() * 100),
            AvgReturn=('OvernightReturn', 'mean')
        ).round(2)
        print(f"\n{name}:")
        print(stats.to_string())
    
    # Combinations
    print("\n--- Best Combinations (min 30 trades) ---")
    conditions = {
        'RSI<30': results['RSI'] < 30,
        'RSI>70': results['RSI'] > 70,
        'BB<10': results['BB_Position'] < 10,
        'BB>90': results['BB_Position'] > 90,
        'MACD<0': results['MACD_Hist'] < 0,
        'MACD>0': results['MACD_Hist'] > 0,
        'Tuesday': results['DayOfWeek'] == 'Tuesday',
    }
    
    combos = []
    for name, mask in conditions.items():
        subset = results[mask]
        if len(subset) >= 30:
            wr = (subset['OvernightReturn'] > 0).mean() * 100
            avg = subset['OvernightReturn'].mean()
            combos.append((name, len(subset), wr, avg, 'single'))
    
    # Two-filter combos
    names = list(conditions.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            mask = conditions[names[i]] & conditions[names[j]]
            subset = results[mask]
            if len(subset) >= 30:
                wr = (subset['OvernightReturn'] > 0).mean() * 100
                avg = subset['OvernightReturn'].mean()
                combos.append((f"{names[i]} + {names[j]}", len(subset), wr, avg, 'double'))
    
    combos.sort(key=lambda x: -x[2])
    
    print(f"{'Combination':<50} {'N':>8} {'WinRate':>10} {'AvgRet':>10}")
    print("-"*80)
    for name, n, wr, avg, tier in combos[:30]:
        mark = "🔥" if wr >= 60 else "⭐" if wr >= 55 else ""
        print(f"{name:<50} {n:>8,} {wr:>9.2f}% {avg:>9.4f}% {mark}")
    
    # Summary
    summary = {
        'mode': 'polygon_4am',
        'total_observations': int(len(results)),
        'tickers_tested': int(results['Ticker'].nunique()),
        'baseline_win_rate': round(float(baseline_wr), 2),
        'baseline_avg_return': round(float(baseline_avg), 4),
        'top_combinations': [
            {'name': c[0], 'trades': c[1], 'win_rate': c[2], 'avg_return': c[3]}
            for c in combos[:10]
        ],
        'date': datetime.now().isoformat()
    }
    with open('research/polygon_4am_summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n💾 Summary saved to: research/polygon_4am_summary.json")

if __name__ == '__main__':
    results = run_polygon_research(max_tickers=500)
    if results is not None:
        analyze(results)
    
    print("\n" + "="*70)
    print("POLYGON RESEARCH COMPLETE")
    print("="*70)

"""
Polygon.io hourly backtest: Close → 4 AM pre-market.
100 tickers, aggressive rate limit handling (12s between calls).
"""
import requests
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime, timedelta
import os

API_KEY = os.environ.get('POLYGON_API_KEY', 'DEMO')

# Top 100 tickers by expected volume
TICKERS = [
    "AAPL","MSFT","GOOGL","AMZN","TSLA","META","NVDA","NFLX","AMD","INTC",
    "QCOM","CRM","ADBE","PYPL","UBER","ABNB","COIN","PLTR","SNOW","ZM",
    "ROKU","SQ","SHOP","CRWD","NET","DDOG","FSLY","DOCU","OKTA","TWLO",
    "SPY","QQQ","DIA","IWM","XLF","XLK","XLE","XLI","XLU","XLP",
    "BAC","JPM","WFC","GS","MS","C","AXP","V","MA","BLK",
    "DIS","NKE","SBUX","MCD","KO","PEP","WMT","TGT","COST","HD",
    "LOW","F","GM","T","VZ","TMUS","CHTR","CMCSA","NFLX","DISH",
    "PFE","JNJ","MRK","UNH","ABBV","LLY","BMY","AMGN","GILD","BIIB",
    "XOM","CVX","COP","EOG","OXY","SLB","HAL","PSX","VLO","MPC",
    "BA","CAT","GE","HON","MMM","UPS","FDX","CSX","UNP","NSC",
    "NEE","DUK","SO","D","AEP","SRE","EXC","XEL","WEC","ES",
]

print(f"Polygon.io Close → 4 AM Backtest")
print(f"API Key: {API_KEY[:5]}...{API_KEY[-4:]}")
print(f"Tickers: {len(TICKERS)}")
print(f"Rate limit: 5 calls/min → 12s sleep between calls")
print(f"Expected time: ~{len(TICKERS) * 4} minutes")
print("="*70)

all_results = []
errors = []

def get_hourly_bars(ticker, days=365):
    """Fetch all hourly bars for a ticker."""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/hour/{start_date}/{end_date}?adjusted=true&sort=asc&limit=50000&apiKey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=30)
        data = response.json()
        
        if 'results' not in data or not data['results']:
            return None
        
        df = pd.DataFrame(data['results'])
        df['datetime'] = pd.to_datetime(df['t'], unit='ms', utc=True).dt.tz_convert('America/New_York')
        df['date'] = df['datetime'].dt.date
        df['hour'] = df['datetime'].dt.hour
        
        return df
    except Exception as e:
        errors.append(f"{ticker}: {str(e)}")
        return None

def compute_overnight_4am(df):
    """Compute Close → 4 AM overnight returns."""
    # Get daily close (3-4 PM bars)
    daily_close = df[df['hour'] >= 15].groupby('date').last().reset_index()
    daily_close = daily_close.rename(columns={'c': 'close_price'})
    
    # Get 4 AM bars next day
    am4 = df[df['hour'] == 4].copy()
    
    if len(daily_close) == 0 or len(am4) == 0:
        return None
    
    # Merge: for each close date, find next day's 4 AM
    results = []
    for _, row in daily_close.iterrows():
        close_date = row['date']
        next_date = close_date + timedelta(days=1)
        
        # Find 4 AM on next trading day
        next_am = am4[am4['date'] == next_date]
        if len(next_am) == 0:
            continue
        
        am_open = next_am.iloc[0]['o']
        am_close = next_am.iloc[0]['c']
        
        overnight_return = (am_open / row['close_price'] - 1) * 100
        
        results.append({
            'date': str(close_date),
            'close_price': row['close_price'],
            'am4_open': am_open,
            'am4_close': am_close,
            'overnight_return': overnight_return,
        })
    
    return pd.DataFrame(results)

# Process tickers
start_time = time.time()

for i, ticker in enumerate(TICKERS, 1):
    print(f"\n[{i}/{len(TICKERS)}] {ticker}...")
    
    df = get_hourly_bars(ticker)
    if df is None:
        print(f"  No data")
        errors.append(f"{ticker}: No data")
        time.sleep(12)
        continue
    
    print(f"  Got {len(df)} hourly bars")
    
    overnight_df = compute_overnight_4am(df)
    if overnight_df is None or len(overnight_df) == 0:
        print(f"  No overnight data")
        errors.append(f"{ticker}: No overnight data")
        time.sleep(12)
        continue
    
    wr = (overnight_df['overnight_return'] > 0).mean() * 100
    avg_ret = overnight_df['overnight_return'].mean()
    
    print(f"  Overnight: {len(overnight_df)} days, WR={wr:.2f}%, Avg={avg_ret:.4f}%")
    
    all_results.append({
        'ticker': ticker,
        'days': len(overnight_df),
        'win_rate': wr,
        'avg_return': avg_ret,
        'median_return': overnight_df['overnight_return'].median(),
        'max_return': overnight_df['overnight_return'].max(),
        'min_return': overnight_df['overnight_return'].min(),
        'std': overnight_df['overnight_return'].std(),
    })
    
    # Save incremental
    with open('research/polygon_4am_progress.json', 'w') as f:
        json.dump({
            'processed': i,
            'total': len(TICKERS),
            'results': all_results,
            'errors': errors,
        }, f, indent=2)
    
    # Rate limit: sleep 12 seconds between tickers (5 calls/min max)
    time.sleep(12)

elapsed = time.time() - start_time
print(f"\n{'='*70}")
print(f"COMPLETE: {len(all_results)}/{len(TICKERS)} tickers in {elapsed/60:.1f} minutes")
print(f"{'='*70}")

# Summary
if all_results:
    results_df = pd.DataFrame(all_results)
    results_df = results_df.sort_values('win_rate', ascending=False)
    
    print(f"\n{'Ticker':<8} {'Days':>6} {'WinRate':>10} {'AvgRet':>10} {'Max':>10} {'Min':>10}")
    print("-"*60)
    for _, r in results_df.iterrows():
        mark = "🔥" if r['win_rate'] >= 55 else "⭐" if r['win_rate'] >= 52 else ""
        print(f"{r['ticker']:<8} {r['days']:>6} {r['win_rate']:>9.2f}% {r['avg_return']:>9.4f}% {r['max_return']:>9.2f}% {r['min_return']:>9.2f}% {mark}")
    
    # Overall stats
    total_days = results_df['days'].sum()
    overall_wr = results_df['win_rate'].mean()
    overall_avg = results_df['avg_return'].mean()
    
    print(f"\n{'='*70}")
    print(f"OVERALL: {total_days} total overnight observations")
    print(f"Average Win Rate: {overall_wr:.2f}%")
    print(f"Average Return: {overall_avg:.4f}%")
    print(f"{'='*70}")
    
    # Save final
    summary = {
        'mode': 'polygon_close_to_4am',
        'tickers_tested': len(TICKERS),
        'tickers_success': len(all_results),
        'total_days': int(total_days),
        'overall_win_rate': round(float(overall_wr), 2),
        'overall_avg_return': round(float(overall_avg), 4),
        'top_performers': results_df.head(20).to_dict('records'),
        'all_results': results_df.to_dict('records'),
        'errors': errors,
        'elapsed_minutes': round(elapsed/60, 1),
        'date': datetime.now().isoformat(),
    }
    
    with open('research/polygon_4am_results.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\nSaved: research/polygon_4am_results.json")

print("\nDONE")

"""
Backtest: Close → First 15 minutes / First hour of next day.
Uses 60-min data (yfinance gives ~2 years of hourly data).
"""
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from indicators import add_all_indicators, indicator_snapshot

def fetch_hourly(ticker, period='60d'):
    """Fetch hourly data for a ticker."""
    try:
        t = yf.Ticker(ticker)
        # Hourly data available for ~60 days max
        df = t.history(period=period, interval='60m')
        if df.empty or len(df) < 50:
            return None
        return df
    except Exception as e:
        return None

def compute_intraday_returns(df):
    """
    For each trading day, compute:
    - Close of previous day
    - Open of next day  
    - Return from Close → Open (first bar next day, ~9:30 AM)
    """
    df = df.copy()
    # Handle timezone-aware index
    df['Date'] = pd.to_datetime(df.index.date)
    df['Hour'] = df.index.hour
    df['Minute'] = df.index.minute
    
    # Group by date
    daily = []
    for date, group in df.groupby('Date'):
        if len(group) < 2:
            continue
        # Sort by time
        group = group.sort_index()
        
        # Close price (last bar of the day, usually 15:00 or 16:00)
        day_close = group['Close'].iloc[-1]
        day_close_time = group.index[-1]
        
        daily.append({
            'Date': date,
            'Close': day_close,
            'CloseTime': day_close_time,
            'Volume': group['Volume'].sum(),
            'High': group['High'].max(),
            'Low': group['Low'].min(),
        })
    
    if len(daily) < 5:
        return None
    
    df_daily = pd.DataFrame(daily)
    df_daily = df_daily.sort_values('Date').reset_index(drop=True)
    
    # Compute overnight returns: Close[i] → Close[i+1] (next day's first bar ≈ open)
    df_daily['NextOpen'] = df_daily['Close'].shift(-1)  
    df_daily['OvernightReturn'] = (df_daily['NextOpen'] / df_daily['Close'] - 1) * 100
    
    return df_daily

def backtest_with_indicators(ticker, period='60d'):
    """Full pipeline: fetch hourly, add indicators, compute returns."""
    df_hourly = fetch_hourly(ticker, period)
    if df_hourly is None:
        return None
    
    # Add indicators on FULL hourly data (not per-day)
    df_hourly = add_all_indicators(df_hourly)
    
    # Compute daily stats from hourly
    df_daily = compute_intraday_returns(df_hourly)
    if df_daily is None or len(df_daily) < 10:
        return None
    
    # For each day, get indicator values from the LAST hourly bar of that day
    indicators = []
    for i in range(len(df_daily) - 1):
        date = df_daily.iloc[i]['Date']
        # Match timezone-aware index with date
        day_mask = pd.to_datetime(df_hourly.index.date) == pd.Timestamp(date)
        day_data = df_hourly[day_mask]
        if len(day_data) > 0:
            # Get the last bar of the day (close bar)
            last_bar = day_data.iloc[-1]
            # Check if indicators are valid
            if pd.notna(last_bar['RSI']):
                snap = {
                    'RSI': round(last_bar['RSI'], 2),
                    'ATR_Pct': round(last_bar['ATR_Pct'], 3) if pd.notna(last_bar['ATR_Pct']) else None,
                    'BB_Position': round(last_bar['BB_Position'], 2) if pd.notna(last_bar['BB_Position']) else None,
                    'BB_Width': round(last_bar['BB_Width'], 2) if pd.notna(last_bar['BB_Width']) else None,
                    'MACD': round(last_bar['MACD'], 4) if pd.notna(last_bar['MACD']) else None,
                    'MACD_Hist': round(last_bar['MACD_Hist'], 4) if pd.notna(last_bar['MACD_Hist']) else None,
                    'MACD_Signal': round(last_bar['MACD_Signal'], 4) if pd.notna(last_bar['MACD_Signal']) else None,
                }
                snap['Date'] = date
                snap['ClosePrice'] = df_daily.iloc[i]['Close']
                snap['NextOpen'] = df_daily.iloc[i]['NextOpen']
                snap['OvernightReturn'] = df_daily.iloc[i]['OvernightReturn']
                snap['Volume'] = df_daily.iloc[i]['Volume']
                indicators.append(snap)
    
    if len(indicators) < 10:
        return None
    
    return pd.DataFrame(indicators)

def batch_backtest(tickers, period='1y', max_tickers=200):
    """Run backtest on multiple tickers."""
    all_results = []
    tested = 0
    for t in tickers[:max_tickers]:
        result = backtest_with_indicators(t, period)
        if result is not None:
            result['Ticker'] = t
            all_results.append(result)
            tested += 1
            print(f"  {tested}. {t}: {len(result)} days")
        else:
            print(f"  {t}: skipped (no data)")
    
    if not all_results:
        return None
    return pd.concat(all_results, ignore_index=True)

def analyze_by_indicators(df):
    """Find which indicator values predict positive overnight returns."""
    print("\n" + "="*70)
    print("INDICATOR ANALYSIS: Which values predict positive overnight return?")
    print("="*70)
    
    # RSI bins
    df['RSI_Bin'] = pd.cut(df['RSI'], bins=[0, 30, 40, 50, 60, 70, 100], 
                            labels=['<30','30-40','40-50','50-60','60-70','>70'])
    
    # BB Position bins  
    df['BB_Bin'] = pd.cut(df['BB_Position'], bins=[0, 10, 30, 50, 70, 90, 100],
                          labels=['<10%','10-30%','30-50%','50-70%','70-90%','>90%'])
    
    # ATR bins
    df['ATR_Bin'] = pd.cut(df['ATR_Pct'], bins=[0, 1, 2, 3, 5, 10, 50],
                           labels=['<1%','1-2%','2-3%','3-5%','5-10%','>10%'])
    
    # MACD histogram bins
    df['MACD_Bin'] = pd.cut(df['MACD_Hist'], bins=[-10, -0.5, -0.1, 0, 0.1, 0.5, 10],
                            labels=['<-0.5','-0.5 to -0.1','-0.1 to 0','0 to 0.1','0.1 to 0.5','>0.5'])
    
    results = {}
    for col, name in [('RSI_Bin', 'RSI'), ('BB_Bin', 'BB Position'), ('ATR_Bin', 'ATR %'), ('MACD_Bin', 'MACD Hist')]:
        stats = df.groupby(col).agg(
            Count=('OvernightReturn', 'count'),
            WinRate=('OvernightReturn', lambda x: (x > 0).mean() * 100),
            AvgReturn=('OvernightReturn', 'mean'),
            Median=('OvernightReturn', 'median')
        ).round(2)
        results[name] = stats
        print(f"\n{name}:")
        print(stats.to_string())
    
    return results

def find_best_combinations(df, min_trades=50):
    """Find combinations of indicator filters with highest win rates."""
    print("\n" + "="*70)
    print("COMBINATION ANALYSIS: Best indicator + day feature combos")
    print("="*70)
    
    combos = []
    
    # Define indicator conditions
    conditions = {
        'RSI<30 (oversold)': df['RSI'] < 30,
        'RSI<35': df['RSI'] < 35,
        'RSI>70 (overbought)': df['RSI'] > 70,
        'BB_Pos<10 (below lower)': df['BB_Position'] < 10,
        'BB_Pos<20': df['BB_Position'] < 20,
        'BB_Pos>80 (above upper)': df['BB_Position'] > 80,
        'BB_Pos>90': df['BB_Position'] > 90,
        'ATR_Pct>3 (volatile)': df['ATR_Pct'] > 3,
        'ATR_Pct>5': df['ATR_Pct'] > 5,
        'MACD_Hist<0 (bearish)': df['MACD_Hist'] < 0,
        'MACD_Hist<-0.2': df['MACD_Hist'] < -0.2,
        'MACD_Hist>0 (bullish)': df['MACD_Hist'] > 0,
    }
    
    # Single filters
    for name, mask in conditions.items():
        subset = df[mask]
        if len(subset) >= min_trades:
            wr = (subset['OvernightReturn'] > 0).mean() * 100
            avg = subset['OvernightReturn'].mean()
            combos.append((name, len(subset), wr, avg, 'single'))
    
    # Two-filter combinations
    names = list(conditions.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            mask = conditions[names[i]] & conditions[names[j]]
            subset = df[mask]
            if len(subset) >= min_trades:
                wr = (subset['OvernightReturn'] > 0).mean() * 100
                avg = subset['OvernightReturn'].mean()
                combos.append((f"{names[i]} + {names[j]}", len(subset), wr, avg, 'double'))
    
    # Sort by win rate
    combos.sort(key=lambda x: -x[2])
    
    print(f"\n{'Combination':<50} {'N':>8} {'WinRate':>10} {'AvgRet':>10}")
    print("-"*80)
    for name, n, wr, avg, tier in combos[:40]:
        tier_mark = "🔥" if wr >= 60 else "⭐" if wr >= 55 else ""
        print(f"{name:<50} {n:>8,} {wr:>9.2f}% {avg:>9.4f}% {tier_mark}")
    
    return combos

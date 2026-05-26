#!/usr/bin/env python3
"""
Research: Overnight Strategy with Indicators
500+ tickers, two modes: hourly (60d) + daily (1y)
Results saved to research/ directory
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'agents'))

import pandas as pd
import numpy as np
import yfinance as yf
import warnings
import json
from datetime import datetime
warnings.filterwarnings('ignore')

from indicators import add_all_indicators

# Extended ticker list (500+ liquid stocks)
TICKERS_500 = [
    # Mag7 + mega tech
    "AAPL","MSFT","GOOGL","GOOG","AMZN","META","NVDA","TSLA","NFLX","AMD",
    "INTC","QCOM","CRM","ADBE","PYPL","UBER","ABNB","COIN","PLTR","SNOW",
    "ZM","ROKU","SQ","SHOP","CRWD","NET","DDOG","FSLY","DOCU","OKTA","TWLO",
    # S&P 500 large cap
    "ABBV","ABT","ACN","ADP","AIG","ALL","AMAT","AMGN","AMP","AMT",
    "ANET","AON","APA","APD","APH","APO","ARE","ATO","AVB","AVGO",
    "AXP","AZO","BA","BAC","BAX","BDX","BEN","BG","BIIB","BIO","BK",
    "BKNG","BKR","BLK","BMY","BR","BRO","BSX","BWA","BX","C","CAG",
    "CAH","CAT","CB","CBOE","CBRE","CCI","CCL","CDAY","CDNS","CDW",
    "CE","CF","CFG","CHD","CHRW","CHTR","CI","CINF","CL","CLX",
    "CMA","CMCSA","CME","CMG","CMI","CMS","CNC","CNP","COF","COO",
    "COP","COST","CPAY","CPB","CPRT","CPT","CRL","CSGP","CSX","CTAS",
    "CTLT","CTRA","CTSH","CTVA","CVS","CVX","D","DAL","DD","DE",
    "DFS","DG","DGX","DHI","DHR","DIS","DLR","DLTR","DOV","DOW",
    "DPZ","DRI","DTE","DUK","DVA","DVN","DXC","DXCM","EA","EBAY",
    "ECL","ED","EFX","EG","EL","ELV","EMN","EMR","ENPH","EOG",
    "EPAM","EQIX","EQR","EQT","ES","ESS","ETN","ETR","EW","EXC",
    "EXPD","EXPE","EXR","F","FAST","FCX","FDS","FDX","FE","FFIV",
    "FI","FICO","FIS","FITB","FLT","FMC","FOX","FOXA","FRT","FSLR",
    "FTNT","FTV","GD","GE","GEHC","GILD","GIS","GL","GPC","GPN",
    "GRMN","GS","GWW","HAL","HAS","HBAN","HCA","HD","HES","HIG",
    "HII","HLT","HOG","HOLX","HON","HPE","HPQ","HRL","HSIC","HST",
    "HSY","HUBB","HUM","IBM","ICE","IDXX","IEX","IFF","ILMN","INCY",
    "INTU","INVH","IP","IPG","IQV","IR","IRM","ISRG","IT","ITW",
    "IVZ","J","JBHT","JBL","JCI","JKHY","JNJ","JNPR","JPM","K",
    "KDP","KEY","KEYS","KHC","KIM","KKR","KLAC","KMB","KMI","KMX",
    "KO","KR","KVUE","L","LDOS","LEN","LH","LHX","LIN","LKQ",
    "LLY","LMT","LNT","LOW","LRCX","LULU","LUV","LVS","LW","LYB",
    "LYV","MA","MAA","MAR","MAS","MCD","MCHP","MCK","MCO","MDLZ",
    "MDT","MET","META","MGM","MHK","MKC","MKTX","MLM","MMC","MMM",
    "MNST","MO","MOH","MOS","MPC","MPWR","MRK","MRNA","MRO","MS",
    "MSCI","MSFT","MSI","MTB","MTCH","MTD","MU","NCLH","NDAQ","NEE",
    "NEM","NFLX","NI","NKE","NOC","NOW","NRG","NSC","NTRS","NUE",
    "NVDA","NVR","NWS","NWSA","NXPI","O","ODFL","OKE","OMC","ON",
    "ORCL","ORLY","OTIS","OXY","PANW","PARA","PAYC","PAYX","PCAR","PCG",
    "PEAK","PEG","PEP","PFE","PFG","PG","PGR","PH","PHM","PKG",
    "PLD","PM","PNC","PNR","PNW","PPG","PPL","PRU","PSA","PSX",
    "PTC","PVH","PWR","QCOM","QRVO","RCL","REG","REGN","RF","RHI",
    "RJF","RL","RMD","ROK","ROL","ROP","ROST","RRC","RSG","RTX",
    "RVTY","SBAC","SBUX","SCHW","SEDG","SEE","SHW","SJM","SLB","SNA",
    "SNPS","SO","SPG","SPGI","SRE","STE","STLD","STT","STX","STZ",
    "SWK","SWKS","SYF","SYK","SYY","T","TAP","TDG","TDY","TECH",
    "TEL","TER","TFC","TFX","TGT","TJX","TMO","TMUS","TPR","TRMB",
    "TROW","TRV","TSLA","TSN","TT","TTWO","TXN","TXT","TYL","UAL",
    "UDR","UHS","ULTA","UNH","UNP","UPS","URI","USB","V","VFC",
    "VICI","VLO","VMC","VRSK","VRSN","VRTX","VST","VTR","VTRS","VZ",
    "WAB","WAT","WBA","WBD","WDC","WEC","WELL","WFC","WHR","WM",
    "WMB","WMT","WRB","WRK","WST","WTW","WY","WYNN","XEL","XOM",
    "XYL","YUM","ZBH","ZBH","ZION","ZTS",
]

def fetch_daily_with_indicators(ticker, period='1y'):
    """Fetch daily data and compute indicators."""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval='1d')
        if df.empty or len(df) < 30:
            return None
        df = add_all_indicators(df)
        return df
    except:
        return None

def compute_overnight_daily(df):
    """Compute overnight returns from daily data."""
    df = df.copy()
    df['NextOpen'] = df['Open'].shift(-1)
    df['OvernightReturn'] = (df['NextOpen'] / df['Close'] - 1) * 100
    df['NextDayReturn'] = (df['Close'].shift(-1) / df['NextOpen'] - 1) * 100  # Open→Close next day
    df['Next15MinReturn'] = df['OvernightReturn'] * 0.25  # Approximate: first 15 min ≈ 25% of overnight
    df['Date'] = df.index.date
    df['DayOfWeek'] = df.index.day_name()
    return df

def extract_features(df):
    """Extract indicator values and overnight returns for each day."""
    df = compute_overnight_daily(df)
    
    # Skip first 30 rows where indicators are NaN
    df_valid = df.iloc[30:-1].copy()
    
    if len(df_valid) < 10:
        return None
    
    records = []
    for _, row in df_valid.iterrows():
        if pd.notna(row['RSI']) and pd.notna(row['OvernightReturn']):
            records.append({
                'Date': row['Date'],
                'DayOfWeek': row['DayOfWeek'],
                'Close': row['Close'],
                'NextOpen': row['NextOpen'],
                'OvernightReturn': row['OvernightReturn'],
                'NextDayReturn': row['NextDayReturn'],
                'Next15MinReturn': row['Next15MinReturn'],
                'Volume': row['Volume'],
                'RSI': round(row['RSI'], 2),
                'ATR_Pct': round(row['ATR_Pct'], 3) if pd.notna(row['ATR_Pct']) else None,
                'BB_Position': round(row['BB_Position'], 2) if pd.notna(row['BB_Position']) else None,
                'BB_Width': round(row['BB_Width'], 2) if pd.notna(row['BB_Width']) else None,
                'MACD': round(row['MACD'], 4) if pd.notna(row['MACD']) else None,
                'MACD_Hist': round(row['MACD_Hist'], 4) if pd.notna(row['MACD_Hist']) else None,
                'ChangePct': ((row['Close'] - row['Open']) / row['Open'] * 100) if row['Open'] != 0 else 0,
            })
    
    if len(records) < 10:
        return None
    return pd.DataFrame(records)

def run_daily_research(tickers, max_tickers=500):
    print("="*70)
    print("DAILY RESEARCH: Close → Open + Indicators")
    print(f"Testing up to {max_tickers} tickers, 1 year of daily data...")
    print("="*70)
    
    all_results = []
    tested = 0
    for t in tickers[:max_tickers]:
        df = fetch_daily_with_indicators(t)
        if df is not None:
            features = extract_features(df)
            if features is not None:
                features['Ticker'] = t
                all_results.append(features)
                tested += 1
                if tested % 50 == 0:
                    print(f"  ... {tested} tickers processed")
    
    if not all_results:
        print("ERROR: No data retrieved")
        return None
    
    results = pd.concat(all_results, ignore_index=True)
    print(f"\n✅ Daily research complete: {len(results):,} observations across {results['Ticker'].nunique()} tickers")
    
    # Save
    results.to_csv('research/daily_indicators_results.csv', index=False)
    print(f"💾 Saved to: research/daily_indicators_results.csv")
    
    return results

def analyze(results):
    print("\n" + "="*70)
    print("ANALYSIS: Indicator-Based Filters")
    print("="*70)
    
    baseline_wr = (results['OvernightReturn'] > 0).mean() * 100
    baseline_avg = results['OvernightReturn'].mean()
    print(f"Baseline: WinRate={baseline_wr:.2f}%, AvgReturn={baseline_avg:.4f}%")
    print(f"Total: {len(results):,} observations, {results['Ticker'].nunique()} tickers")
    
    # Define bins
    results['RSI_Bin'] = pd.cut(results['RSI'], bins=[0, 30, 40, 50, 60, 70, 100], 
                                   labels=['<30','30-40','40-50','50-60','60-70','>70'])
    results['BB_Bin'] = pd.cut(results['BB_Position'], bins=[0, 10, 30, 50, 70, 90, 100],
                                labels=['<10%','10-30%','30-50%','50-70%','70-90%','>90%'])
    results['ATR_Bin'] = pd.cut(results['ATR_Pct'], bins=[0, 1, 2, 3, 5, 10, 50],
                                 labels=['<1%','1-2%','2-3%','3-5%','5-10%','>10%'])
    
    # Single filters
    print("\n--- Single Indicators ---")
    for col, name in [('RSI_Bin', 'RSI'), ('BB_Bin', 'BB Position'), ('ATR_Bin', 'ATR %')]:
        stats = results.groupby(col).agg(
            Count=('OvernightReturn', 'count'),
            WinRate=('OvernightReturn', lambda x: (x > 0).mean() * 100),
            AvgReturn=('OvernightReturn', 'mean')
        ).round(2)
        print(f"\n{name}:")
        print(stats.to_string())
    
    # Combinations
    print("\n--- Best Combinations (min 50 trades) ---")
    conditions = {
        'RSI<30': results['RSI'] < 30,
        'RSI>70': results['RSI'] > 70,
        'BB<10': results['BB_Position'] < 10,
        'BB>90': results['BB_Position'] > 90,
        'ATR>2': results['ATR_Pct'] > 2,
        'MACD_Hist<0': results['MACD_Hist'] < 0,
        'MACD_Hist>0': results['MACD_Hist'] > 0,
        'Change<-2%': results['ChangePct'] < -2,
        'Change>2%': results['ChangePct'] > 2,
        'Tuesday': results['DayOfWeek'] == 'Tuesday',
    }
    
    combos = []
    for name, mask in conditions.items():
        subset = results[mask]
        if len(subset) >= 50:
            wr = (subset['OvernightReturn'] > 0).mean() * 100
            avg = subset['OvernightReturn'].mean()
            combos.append((name, len(subset), wr, avg, 'single'))
    
    # Two-filter combos
    names = list(conditions.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            mask = conditions[names[i]] & conditions[names[j]]
            subset = results[mask]
            if len(subset) >= 50:
                wr = (subset['OvernightReturn'] > 0).mean() * 100
                avg = subset['OvernightReturn'].mean()
                combos.append((f"{names[i]} + {names[j]}", len(subset), wr, avg, 'double'))
    
    combos.sort(key=lambda x: -x[2])
    
    print(f"{'Combination':<50} {'N':>8} {'WinRate':>10} {'AvgRet':>10}")
    print("-"*80)
    for name, n, wr, avg, tier in combos[:30]:
        mark = "🔥" if wr >= 60 else "⭐" if wr >= 55 else ""
        print(f"{name:<50} {n:>8,} {wr:>9.2f}% {avg:>9.4f}% {mark}")
    
    # Top tickers
    print("\n--- Top Tickers by Win Rate (min 50 trades) ---")
    ticker_stats = results.groupby('Ticker').agg(
        Trades=('OvernightReturn', 'count'),
        WinRate=('OvernightReturn', lambda x: (x > 0).mean() * 100),
        AvgReturn=('OvernightReturn', 'mean')
    )
    top = ticker_stats[ticker_stats['Trades'] >= 50].sort_values('WinRate', ascending=False).head(20)
    print(top.to_string())
    
    # Summary
    summary = {
        'mode': 'daily',
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
    with open('research/daily_research_summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n💾 Summary saved to: research/daily_research_summary.json")

def run_hourly_research():
    """Run the existing hourly agent research."""
    print("\n" + "="*70)
    print("HOURLY RESEARCH: 60 days, hourly data + indicators")
    print("="*70)
    # Import and run from agents module
    from intraday_backtest import batch_backtest
    from orchestrator import analyze_by_indicators, find_best_combinations
    
    results = batch_backtest(TICKERS_500[:200], period='60d', max_tickers=200)
    if results is not None:
        results.to_csv('research/hourly_indicators_results.csv', index=False)
        print(f"💾 Saved to: research/hourly_indicators_results.csv")
        
        analyze_by_indicators(results)
        combos = find_best_combinations(results, min_trades=30)
        
        summary = {
            'mode': 'hourly',
            'total_observations': int(len(results)),
            'tickers_tested': int(results['Ticker'].nunique()),
            'baseline_win_rate': round((results['OvernightReturn'] > 0).mean() * 100, 2),
            'baseline_avg_return': round(results['OvernightReturn'].mean(), 4),
            'date': datetime.now().isoformat()
        }
        with open('research/hourly_research_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"💾 Summary saved to: research/hourly_research_summary.json")

if __name__ == '__main__':
    print("STARTING RESEARCH: 500+ tickers, Daily + Hourly")
    print()
    
    # Mode 1: Daily (1 year, 500 tickers)
    daily_results = run_daily_research(TICKERS_500, max_tickers=500)
    if daily_results is not None:
        analyze(daily_results)
    
    # Mode 2: Hourly (60 days, 200 tickers - faster)
    print("\n\n")
    run_hourly_research()
    
    print("\n" + "="*70)
    print("ALL RESEARCH COMPLETE")
    print("="*70)
    print("Results in: research/")
    print("  - daily_indicators_results.csv")
    print("  - daily_research_summary.json")
    print("  - hourly_indicators_results.csv")
    print("  - hourly_research_summary.json")

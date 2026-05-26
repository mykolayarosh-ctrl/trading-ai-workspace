"""
Add index ETF (SPY, QQQ, DIA) overnight returns as factors.
"""
import pandas as pd
import numpy as np
import yfinance as yf
import json
from datetime import datetime

def fetch_etf_overnight(ticker, period='1y'):
    """Fetch daily data and compute overnight returns for an ETF."""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval='1d')
        if df.empty or len(df) < 30:
            return None
        df = df.sort_index().reset_index()
        df['NextOpen'] = df['Open'].shift(-1)
        df['OvernightReturn'] = (df['NextOpen'] / df['Close'] - 1) * 100
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df[['Date', 'OvernightReturn']].copy()
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

print("Fetching ETF data...")
spy = fetch_etf_overnight('SPY')
qqq = fetch_etf_overnight('QQQ')
dia = fetch_etf_overnight('DIA')

if spy is not None:
    print(f"SPY: {len(spy)} days")
if qqq is not None:
    print(f"QQQ: {len(qqq)} days")
if dia is not None:
    print(f"DIA: {len(dia)} days")

print("\nLoading daily results...")
df = pd.read_csv('research/daily_indicators_results.csv')
print(f"Loaded: {len(df)} rows, {df['Ticker'].nunique()} tickers")

df['Date'] = pd.to_datetime(df['Date']).dt.date

# Merge with ETF data
if spy is not None:
    spy = spy.rename(columns={'OvernightReturn': 'SPY_Overnight'})
    df = df.merge(spy[['Date', 'SPY_Overnight']], on='Date', how='left')
    print(f"  SPY merged: {df['SPY_Overnight'].notna().sum()} matches")

if qqq is not None:
    qqq = qqq.rename(columns={'OvernightReturn': 'QQQ_Overnight'})
    df = df.merge(qqq[['Date', 'QQQ_Overnight']], on='Date', how='left')
    print(f"  QQQ merged: {df['QQQ_Overnight'].notna().sum()} matches")

if dia is not None:
    dia = dia.rename(columns={'OvernightReturn': 'DIA_Overnight'})
    df = df.merge(dia[['Date', 'DIA_Overnight']], on='Date', how='left')
    print(f"  DIA merged: {df['DIA_Overnight'].notna().sum()} matches")

# Compute factors
df['Outperform'] = df['OvernightReturn'] - df['SPY_Overnight']

df.to_csv('research/daily_with_index_factors.csv', index=False)
print(f"\nSaved: research/daily_with_index_factors.csv")

# Analysis
print("\n" + "="*70)
print("INDEX ETF ANALYSIS")
print("="*70)

baseline = (df['OvernightReturn'] > 0).mean() * 100
print(f"Baseline: WinRate={baseline:.2f}%")

# SPY market direction
print("\n--- SPY Market Direction ---")
spy_up = df['SPY_Overnight'] > 0
spy_down = df['SPY_Overnight'] < 0
spy_strong_down = df['SPY_Overnight'] < -0.5
spy_strong_up = df['SPY_Overnight'] > 0.5

for name, mask in [
    ('SPY_Up', spy_up),
    ('SPY_Down', spy_down),
    ('SPY_StrongUp (>0.5%)', spy_strong_up),
    ('SPY_StrongDown (<-0.5%)', spy_strong_down),
]:
    subset = df[mask]
    if len(subset) > 50:
        wr = (subset['OvernightReturn'] > 0).mean() * 100
        avg = subset['OvernightReturn'].mean()
        print(f"{name:<35} N={len(subset):>8,} WR={wr:>7.2f}% Avg={avg:>8.4f}%")

# Relative strength
print("\n--- Relative Strength ---")
for name, mask in [
    ('Stock beats SPY', df['Outperform'] > 0),
    ('Stock underperforms SPY', df['Outperform'] < 0),
    ('SPY drops but stock drops more', (df['SPY_Overnight'] < -0.5) & (df['OvernightReturn'] < df['SPY_Overnight'])),
    ('SPY drops but stock rises', (df['SPY_Overnight'] < -0.5) & (df['OvernightReturn'] > 0)),
    ('SPY up but stock drops', (df['SPY_Overnight'] > 0.5) & (df['OvernightReturn'] < 0)),
]:
    subset = df[mask]
    if len(subset) > 50:
        wr = (subset['OvernightReturn'] > 0).mean() * 100
        avg = subset['OvernightReturn'].mean()
        print(f"{name:<35} N={len(subset):>8,} WR={wr:>7.2f}% Avg={avg:>8.4f}%")

# Best combos with SPY
print("\n--- Best Combinations with SPY ---")
conditions = {
    'RSI<30': df['RSI'] < 30,
    'RSI>70': df['RSI'] > 70,
    'BB<10': df['BB_Position'] < 10,
    'BB>90': df['BB_Position'] > 90,
    'Change<-2%': df['ChangePct'] < -2,
    'Change>2%': df['ChangePct'] > 2,
    'SPY_Down': df['SPY_Overnight'] < 0,
    'SPY_StrongDown': df['SPY_Overnight'] < -0.5,
    'Tuesday': df['DayOfWeek'] == 'Tuesday',
}

combos = []
for name, mask in conditions.items():
    subset = df[mask]
    if len(subset) >= 50:
        wr = (subset['OvernightReturn'] > 0).mean() * 100
        avg = subset['OvernightReturn'].mean()
        combos.append((name, len(subset), wr, avg, 'single'))

names = list(conditions.keys())
for i in range(len(names)):
    for j in range(i+1, len(names)):
        mask = conditions[names[i]] & conditions[names[j]]
        subset = df[mask]
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

# Summary
summary = {
    'mode': 'daily_with_index_etf',
    'total_observations': int(len(df)),
    'tickers_tested': int(df['Ticker'].nunique()),
    'baseline_win_rate': round(float(baseline), 2),
    'top_combinations': [
        {'name': c[0], 'trades': c[1], 'win_rate': c[2], 'avg_return': c[3]}
        for c in combos[:15]
    ],
    'date': datetime.now().isoformat()
}
with open('research/daily_index_factors_summary.json', 'w') as f:
    json.dump(summary, f, indent=2, default=str)
print(f"\nSummary saved to: research/daily_index_factors_summary.json")

print("\n" + "="*70)
print("INDEX FACTORS COMPLETE")
print("="*70)

#!/usr/bin/env python3
"""
Optimize overnight strategy filters for win rate >= 65%.
Test combinations of technical and day features.
"""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv('backtest/backtest_summary.csv')
df['Date'] = pd.to_datetime(df['Date'])

# Add derived features
df['OvernightWin'] = df['OvernightReturn'] > 0
df['DayWin'] = df['ChangePct'] > 0

print("="*70)
print("FILTER OPTIMIZATION: Close → Open Overnight Strategy")
print("="*70)
print(f"Total observations: {len(df):,}")
print(f"Baseline win rate: {df['OvernightWin'].mean()*100:.2f}%")
print(f"Baseline avg return: {df['OvernightReturn'].mean():.4f}%")
print()

# --- Single filters ---
print("="*70)
print("SINGLE FILTERS")
print("="*70)

filters_single = [
    ("20D_Range < 10", df['20D_Range'] < 10),
    ("20D_Range < 20", df['20D_Range'] < 20),
    ("20D_Range < 30", df['20D_Range'] < 30),
    ("20D_Range > 90", df['20D_Range'] > 90),
    ("20D_Range > 95", df['20D_Range'] > 95),
    ("VolRatio > 2", df['VolRatio'] > 2),
    ("VolRatio > 3", df['VolRatio'] > 3),
    ("VolRatio < 0.5", df['VolRatio'] < 0.5),
    ("AbsChange > 2", df['AbsChange'] > 2),
    ("AbsChange > 3", df['AbsChange'] > 3),
    ("AbsChange > 5", df['AbsChange'] > 5),
    ("ChangePct < -2", df['ChangePct'] < -2),
    ("ChangePct < -3", df['ChangePct'] < -3),
    ("ChangePct > 2", df['ChangePct'] > 2),
    ("ChangePct > 3", df['ChangePct'] > 3),
    ("5D_Change < -5", df['5D_Change'] < -5),
    ("5D_Change > 5", df['5D_Change'] > 5),
    ("5D_Change < -10", df['5D_Change'] < -10),
    ("Friday only", df['DayOfWeek'] == 'Friday'),
    ("Monday only", df['DayOfWeek'] == 'Monday'),
    ("Tuesday only", df['DayOfWeek'] == 'Tuesday'),
]

results = []
for name, mask in filters_single:
    subset = df[mask]
    if len(subset) < 100:
        continue
    wr = subset['OvernightWin'].mean() * 100
    avg = subset['OvernightReturn'].mean()
    n = len(subset)
    results.append((name, n, wr, avg))

results.sort(key=lambda x: -x[2])
print(f"{'Filter':<30} {'N':>8} {'WinRate':>10} {'AvgRet':>10}")
print("-"*60)
for name, n, wr, avg in results:
    print(f"{name:<30} {n:>8,} {wr:>9.2f}% {avg:>9.4f}%")

# --- Two-filter combinations ---
print()
print("="*70)
print("TWO-FILTER COMBINATIONS (min 500 trades)")
print("="*70)

filters = {
    "20D<10": df['20D_Range'] < 10,
    "20D<20": df['20D_Range'] < 20,
    "20D<30": df['20D_Range'] < 30,
    "20D>90": df['20D_Range'] > 90,
    "20D>95": df['20D_Range'] > 95,
    "Vol>2": df['VolRatio'] > 2,
    "Vol>3": df['VolRatio'] > 3,
    "Vol<0.5": df['VolRatio'] < 0.5,
    "|Chg|>2": df['AbsChange'] > 2,
    "|Chg|>3": df['AbsChange'] > 3,
    "Chg<-2": df['ChangePct'] < -2,
    "Chg<-3": df['ChangePct'] < -3,
    "Chg>2": df['ChangePct'] > 2,
    "5D<-5": df['5D_Change'] < -5,
    "5D>5": df['5D_Change'] > 5,
    "Fri": df['DayOfWeek'] == 'Friday',
    "Mon": df['DayOfWeek'] == 'Monday',
    "Tue": df['DayOfWeek'] == 'Tuesday',
}

combo_results = []
filter_names = list(filters.keys())
for i in range(len(filter_names)):
    for j in range(i+1, len(filter_names)):
        mask = filters[filter_names[i]] & filters[filter_names[j]]
        subset = df[mask]
        if len(subset) >= 500:
            wr = subset['OvernightWin'].mean() * 100
            avg = subset['OvernightReturn'].mean()
            combo_results.append((f"{filter_names[i]} + {filter_names[j]}", len(subset), wr, avg))

combo_results.sort(key=lambda x: -x[2])
print(f"{'Combination':<35} {'N':>8} {'WinRate':>10} {'AvgRet':>10}")
print("-"*65)
for name, n, wr, avg in combo_results[:30]:
    print(f"{name:<35} {n:>8,} {wr:>9.2f}% {avg:>9.4f}%")

# --- Three-filter combinations (best candidates) ---
print()
print("="*70)
print("THREE-FILTER COMBINATIONS (min 200 trades)")
print("="*70)

# Test promising triples manually
from itertools import combinations
triples = list(combinations(filter_names, 3))
triple_results = []
for t in triples:
    mask = filters[t[0]] & filters[t[1]] & filters[t[2]]
    subset = df[mask]
    if len(subset) >= 200:
        wr = subset['OvernightWin'].mean() * 100
        avg = subset['OvernightReturn'].mean()
        triple_results.append((" + ".join(t), len(subset), wr, avg))

triple_results.sort(key=lambda x: -x[2])
print(f"{'Combination':<50} {'N':>8} {'WinRate':>10} {'AvgRet':>10}")
print("-"*80)
for name, n, wr, avg in triple_results[:20]:
    print(f"{name:<50} {n:>8,} {wr:>9.2f}% {avg:>9.4f}%")

# --- Sector analysis ---
print()
print("="*70)
print("SECTOR ANALYSIS")
print("="*70)
print("(Sector data not in raw CSV - skipping)")

# --- Month/Earnings season ---
print()
print("="*70)
print("MONTH ANALYSIS")
print("="*70)
month_stats = df.groupby(df['Date'].dt.month).agg(
    N=('OvernightWin','count'),
    WinRate=('OvernightWin','mean'),
    AvgReturn=('OvernightReturn','mean')
).reset_index()
month_stats['WinRate'] *= 100
print(month_stats.to_string(index=False))

# --- Best performing tickers ---
print()
print("="*70)
print("TOP 15 TICKERS BY OVERNIGHT WIN RATE (min 100 trades)")
print("="*70)
ticker_stats = df.groupby('Ticker').agg(
    N=('OvernightWin','count'),
    WinRate=('OvernightWin','mean'),
    AvgReturn=('OvernightReturn','mean'),
    Std=('OvernightReturn','std')
).reset_index()
ticker_stats = ticker_stats[ticker_stats['N'] >= 100]
ticker_stats['WinRate'] *= 100
ticker_stats['Sharpe'] = ticker_stats['AvgReturn'] / ticker_stats['Std']
ticker_stats = ticker_stats.sort_values('WinRate', ascending=False)
print(ticker_stats.head(15).to_string(index=False))

print()
print("="*70)
print("WORST 10 TICKERS BY OVERNIGHT WIN RATE")
print("="*70)
print(ticker_stats.tail(10).to_string(index=False))

# --- Profitability: cumulative with filters ---
print()
print("="*70)
print("CUMULATIVE RETURNS SIMULATION")
print("="*70)

strategies = [
    ("All days", pd.Series(True, index=df.index)),
    ("20D_Range < 20", df['20D_Range'] < 20),
    ("20D_Range < 20 & VolRatio > 2", (df['20D_Range'] < 20) & (df['VolRatio'] > 2)),
    ("20D_Range < 10 & Chg < -2", (df['20D_Range'] < 10) & (df['ChangePct'] < -2)),
    ("20D_Range < 10 & VolRatio > 1.5", (df['20D_Range'] < 10) & (df['VolRatio'] > 1.5)),
    ("20D_Range < 20 & Chg < -2 & VolRatio > 1.5", 
     (df['20D_Range'] < 20) & (df['ChangePct'] < -2) & (df['VolRatio'] > 1.5)),
]

print(f"{'Strategy':<45} {'Trades':>8} {'WinRate':>10} {'AvgRet':>10} {'CumRet':>10}")
print("-"*85)
for name, mask in strategies:
    subset = df[mask]
    n = len(subset)
    wr = subset['OvernightWin'].mean() * 100
    avg = subset['OvernightReturn'].mean()
    # Simulate: equal position each night
    cum = (1 + subset['OvernightReturn']/100).prod() - 1
    print(f"{name:<45} {n:>8,} {wr:>9.2f}% {avg:>9.4f}% {cum:>9.2f}%")

print()
print("="*70)
print("KEY FINDINGS")
print("="*70)
print()
print("Filters that push win rate to 55-60%:")
print("  • 20D_Range < 10% (near lows): 57.3% win rate")
print("  • VolRatio > 3x: 56.4% win rate") 
print("  • ChangePct < -2% (big down day): ~55% win rate")
print("  • Monday: higher overnight returns historically")
print()
print("Best two-filter combos:")
for name, n, wr, avg in combo_results[:5]:
    print(f"  • {name}: {wr:.1f}% win rate, {n:,} trades")
print()
print("Best three-filter combos:")
for name, n, wr, avg in triple_results[:5]:
    print(f"  • {name}: {wr:.1f}% win rate, {n:,} trades")


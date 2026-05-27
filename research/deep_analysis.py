"""
Deep analysis of overnight strategy.
Based on daily_with_index_factors.csv (101k observations, 455 tickers, 1 year).
"""
import pandas as pd
import numpy as np
import json
from datetime import datetime

print("Loading data...")
df = pd.read_csv('research/daily_with_index_factors.csv')
df['Date'] = pd.to_datetime(df['Date'])
df['Month'] = df['Date'].dt.month
df['Quarter'] = df['Date'].dt.quarter
df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)

print(f"Loaded: {len(df)} rows, {df['Ticker'].nunique()} tickers")
print(f"Columns: {list(df.columns)}")

# Helper
baseline = (df['OvernightReturn'] > 0).mean() * 100
baseline_avg = df['OvernightReturn'].mean()

results = {
    'baseline': {'win_rate': round(baseline, 2), 'avg_return': round(baseline_avg, 4)},
    'analyses': {}
}

print("\n" + "="*70)
print("1. SECTOR ANALYSIS")
print("="*70)
print("Sector data not available in daily_with_index_factors.csv")
print("Skipping sector analysis (requires sector info from yfinance)")

# sector_stats = []
# for sector in df['Sector'].dropna().unique():
#     if sector == 'N/A':
#         continue
#     subset = df[df['Sector'] == sector]
#     if len(subset) < 100:
#         continue
#     wr = (subset['OvernightReturn'] > 0).mean() * 100
#     avg_ret = subset['OvernightReturn'].mean()
#     avg_vol = subset['Volume'].mean()
#     sector_stats.append({
#         'sector': sector,
#         'trades': len(subset),
#         'win_rate': wr,
#         'avg_return': avg_ret,
#         'avg_volume': avg_vol,
#     })
# 
# sector_stats.sort(key=lambda x: -x['win_rate'])
# print(f"{'Sector':<25} {'Trades':>8} {'WinRate':>10} {'AvgRet':>10}")
# print("-"*60)
# for s in sector_stats:
#     mark = "🔥" if s['win_rate'] >= 55 else "⭐" if s['win_rate'] >= 53 else ""
#     print(f"{s['sector']:<25} {s['trades']:>8,} {s['win_rate']:>9.2f}% {s['avg_return']:>9.4f}% {mark}")
# 
# results['analyses']['sector'] = sector_stats

print("\n" + "="*70)
print("2. MONTHLY SEASONALITY")
print("="*70)
month_stats = []
for month in range(1, 13):
    subset = df[df['Month'] == month]
    if len(subset) < 100:
        continue
    wr = (subset['OvernightReturn'] > 0).mean() * 100
    avg_ret = subset['OvernightReturn'].mean()
    month_stats.append({
        'month': month,
        'name': ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][month-1],
        'trades': len(subset),
        'win_rate': wr,
        'avg_return': avg_ret,
    })

print(f"{'Month':<8} {'Trades':>8} {'WinRate':>10} {'AvgRet':>10}")
print("-"*40)
for m in month_stats:
    mark = "🔥" if m['win_rate'] >= 55 else "⭐" if m['win_rate'] >= 53 else ""
    print(f"{m['name']:<8} {m['trades']:>8,} {m['win_rate']:>9.2f}% {m['avg_return']:>9.4f}% {mark}")

results['analyses']['monthly'] = month_stats

print("\n" + "="*70)
print("3. QUARTERLY SEASONALITY")
print("="*70)
quarter_stats = []
for q in [1, 2, 3, 4]:
    subset = df[df['Quarter'] == q]
    wr = (subset['OvernightReturn'] > 0).mean() * 100
    avg_ret = subset['OvernightReturn'].mean()
    quarter_stats.append({
        'quarter': q,
        'trades': len(subset),
        'win_rate': wr,
        'avg_return': avg_ret,
    })

print(f"{'Quarter':<10} {'Trades':>8} {'WinRate':>10} {'AvgRet':>10}")
print("-"*40)
for q in quarter_stats:
    mark = "🔥" if q['win_rate'] >= 55 else "⭐" if q['win_rate'] >= 53 else ""
    print(f"Q{q['quarter']:<9} {q['trades']:>8,} {q['win_rate']:>9.2f}% {q['avg_return']:>9.4f}% {mark}")

results['analyses']['quarterly'] = quarter_stats

print("\n" + "="*70)
print("4. VOLATILITY REGIME (using ATR%)")
print("="*70)
df['Vol_Regime'] = pd.cut(df['ATR_Pct'], bins=[0, 2, 4, 100], labels=['Low','Medium','High'])

for regime in ['Low', 'Medium', 'High']:
    subset = df[df['Vol_Regime'] == regime]
    if len(subset) > 50:
        wr = (subset['OvernightReturn'] > 0).mean() * 100
        avg_ret = subset['OvernightReturn'].mean()
        print(f"{regime:<10} N={len(subset):>8,} WR={wr:>7.2f}% Avg={avg_ret:>8.4f}%")

results['analyses']['volatility_regime'] = []
for regime in ['Low', 'Medium', 'High']:
    subset = df[df['Vol_Regime'] == regime]
    if len(subset) > 50:
        results['analyses']['volatility_regime'].append({
            'regime': regime,
            'trades': len(subset),
            'win_rate': (subset['OvernightReturn'] > 0).mean() * 100,
            'avg_return': subset['OvernightReturn'].mean(),
        })

print("\n" + "="*70)
print("5. CONSECUTIVE DAYS ANALYSIS")
print("="*70)
print("Does yesterday's overnight predict today's?")

# For each ticker, compute previous overnight
df_sorted = df.sort_values(['Ticker', 'Date'])
df_sorted['Prev_Overnight'] = df_sorted.groupby('Ticker')['OvernightReturn'].shift(1)

for condition in [
    ('Prev was green', df_sorted['Prev_Overnight'] > 0),
    ('Prev was red', df_sorted['Prev_Overnight'] < 0),
    ('Prev strong green (>1%)', df_sorted['Prev_Overnight'] > 1),
    ('Prev strong red (<-1%)', df_sorted['Prev_Overnight'] < -1),
]:
    name, mask = condition
    subset = df_sorted[mask]
    if len(subset) > 100:
        wr = (subset['OvernightReturn'] > 0).mean() * 100
        avg = subset['OvernightReturn'].mean()
        print(f"{name:<30} N={len(subset):>8,} WR={wr:>7.2f}% Avg={avg:>8.4f}%")

print("\n" + "="*70)
print("6. BEST 3-FILTER COMBINATIONS")
print("="*70)

conditions = {
    'Change<-2%': df['ChangePct'] < -2,
    'Change>2%': df['ChangePct'] > 2,
    'RSI<30': df['RSI'] < 30,
    'RSI>70': df['RSI'] > 70,
    'BB<10': df['BB_Position'] < 10,
    'BB>90': df['BB_Position'] > 90,
    'MACD<0': df['MACD'] < 0,
    'MACD>0': df['MACD'] > 0,
    'Tuesday': df['DayOfWeek'] == 'Tuesday',
    'Wednesday': df['DayOfWeek'] == 'Wednesday',
    'Thursday': df['DayOfWeek'] == 'Thursday',
    'Friday': df['DayOfWeek'] == 'Friday',
    'SPY_Up': df['SPY_Overnight'] > 0,
    'SPY_StrongUp': df['SPY_Overnight'] > 0.5,
    'VolRatio>2': df['Volume'] / df.groupby('Ticker')['Volume'].transform('mean') > 2,
}

# Compute vol_ratio properly
df['AvgVol'] = df.groupby('Ticker')['Volume'].transform('mean')
df['VolRatio'] = df['Volume'] / df['AvgVol']
conditions['VolRatio>2'] = df['VolRatio'] > 2
conditions['VolRatio>3'] = df['VolRatio'] > 3

combos = []
keys = list(conditions.keys())

# 3-filter combinations
for i in range(len(keys)):
    for j in range(i+1, len(keys)):
        for k in range(j+1, len(keys)):
            mask = conditions[keys[i]] & conditions[keys[j]] & conditions[keys[k]]
            subset = df[mask]
            if len(subset) >= 30:
                wr = (subset['OvernightReturn'] > 0).mean() * 100
                avg = subset['OvernightReturn'].mean()
                combos.append((f"{keys[i]} + {keys[j]} + {keys[k]}", len(subset), wr, avg))

combos.sort(key=lambda x: -x[2])

print(f"{'Combination':<60} {'N':>6} {'WinRate':>10} {'AvgRet':>10}")
print("-"*90)
for name, n, wr, avg in combos[:20]:
    mark = "🔥" if wr >= 65 else "⭐" if wr >= 60 else "✅" if wr >= 55 else ""
    print(f"{name:<60} {n:>6,} {wr:>9.2f}% {avg:>9.4f}% {mark}")

results['analyses']['top_3filter_combos'] = [
    {'name': c[0], 'trades': c[1], 'win_rate': c[2], 'avg_return': c[3]} 
    for c in combos[:30]
]

print("\n" + "="*70)
print("7. SPY + SECTOR COMBOS")
print("="*70)
print("Sector data not available — skipping")

# spy_sector = []
# for sector in df['Sector'].dropna().unique():
#     if sector == 'N/A':
#         continue
#     mask = (df['Sector'] == sector) & (df['SPY_Overnight'] > 0.5)
#     subset = df[mask]
#     if len(subset) >= 20:
#         wr = (subset['OvernightReturn'] > 0).mean() * 100
#         avg = subset['OvernightReturn'].mean()
#         spy_sector.append((sector, len(subset), wr, avg))
# 
# spy_sector.sort(key=lambda x: -x[2])
# print(f"{'Sector':<25} {'Trades':>6} {'WinRate':>10} {'AvgRet':>10}")
# print("-"*55)
# for sector, n, wr, avg in spy_sector[:15]:
#     print(f"{sector:<25} {n:>6,} {wr:>9.2f}% {avg:>9.4f}%")
# 
# results['analyses']['spy_sector'] = [
#     {'sector': s[0], 'trades': s[1], 'win_rate': s[2], 'avg_return': s[3]}
#     for s in spy_sector
# ]

print("\n" + "="*70)
print("8. OVERNIGHT MAGNITUDE ANALYSIS")
print("="*70)
print("What overnight return can we expect?")

for threshold in [0.5, 1.0, 1.5, 2.0]:
    subset = df[df['OvernightReturn'] > threshold]
    pct = len(subset) / len(df) * 100
    print(f"Overnight > +{threshold}%: {pct:.2f}% of trades ({len(subset):,} trades)")

print("\nNegative overnights:")
for threshold in [-0.5, -1.0, -1.5, -2.0]:
    subset = df[df['OvernightReturn'] < threshold]
    pct = len(subset) / len(df) * 100
    print(f"Overnight < {threshold}%: {pct:.2f}% of trades ({len(subset):,} trades)")

print("\n" + "="*70)
print("9. TIER VALIDATION ON FULL DATASET")
print("="*70)

# Reproduce tier analysis
tier_conditions = {
    'T3 (|Change|>3% + Down)': (abs(df['ChangePct']) > 3) & (df['ChangePct'] < 0),
    'T2 (Change<-2%)': df['ChangePct'] < -2,
    'T2+ (Change>2%)': df['ChangePct'] > 2,
    'T1 (ATR<2%)': df['ATR_Pct'] < 2,
    'T1 (VolRatio>3)': df['VolRatio'] > 3,
}

for name, mask in tier_conditions.items():
    subset = df[mask]
    if len(subset) > 50:
        wr = (subset['OvernightReturn'] > 0).mean() * 100
        avg = subset['OvernightReturn'].mean()
        print(f"{name:<35} N={len(subset):>8,} WR={wr:>7.2f}% Avg={avg:>8.4f}%")

print("\n" + "="*70)
print("10. RECOMMENDED STRATEGIES SUMMARY")
print("="*70)

strategies = [
    ("Conservative (SPY Up + Any)", df['SPY_Overnight'] > 0, "Market-supported base case"),
    ("Aggressive (SPY Strong Up + T2)", (df['SPY_Overnight'] > 0.5) & (df['ChangePct'] < -2), "Best confirmed setup"),
    ("Momentum (SPY Up + Change>2% + Tuesday)", (df['SPY_Overnight'] > 0) & (df['ChangePct'] > 2) & (df['DayOfWeek'] == 'Tuesday'), "Momentum continuation"),
    ("Mean Reversion (SPY Up + BB>90 + Change<-2%)", (df['SPY_Overnight'] > 0) & (df['BB_Position'] > 90) & (df['ChangePct'] < -2), "Oversold bounce with market support"),
]

for name, mask, desc in strategies:
    subset = df[mask]
    if len(subset) > 20:
        wr = (subset['OvernightReturn'] > 0).mean() * 100
        avg = subset['OvernightReturn'].mean()
        print(f"\n{name}")
        print(f"  {desc}")
        print(f"  Trades: {len(subset):,} | Win Rate: {wr:.2f}% | Avg: {avg:.4f}%")

# Save
results['date'] = datetime.now().isoformat()
with open('research/deep_analysis_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n\nSaved: research/deep_analysis_results.json")
print("="*70)
print("DEEP ANALYSIS COMPLETE")
print("="*70)

"""
FIXED analysis — no look-ahead bias.
Use SPY DAILY CHANGE (known at close) instead of SPY Overnight (future data).
"""
import pandas as pd
import numpy as np
import yfinance as yf
import json
from datetime import datetime

print("Loading stock data...")
df = pd.read_csv('research/daily_with_index_factors.csv')
df['Date'] = pd.to_datetime(df['Date'])
print(f"Loaded: {len(df)} rows")

# Fetch SPY daily data (Open, Close) — no future data
print("\nFetching SPY daily data...")
spy = yf.Ticker('SPY')
spy_hist = spy.history(period='2y', interval='1d')
spy_hist = spy_hist.sort_index().reset_index()
spy_hist['Date'] = pd.to_datetime(spy_hist['Date']).dt.date
df['DateOnly'] = df['Date'].dt.date

# Calculate SPY DAILY change (Close/Open - 1) — KNOWN at close
spy_hist['SPY_DailyChange'] = (spy_hist['Close'] / spy_hist['Open'] - 1) * 100

# Merge
df = df.merge(spy_hist[['Date', 'SPY_DailyChange']], left_on='DateOnly', right_on='Date', how='left')
print(f"SPY daily data merged: {df['SPY_DailyChange'].notna().sum()} rows")

print("\n" + "="*80)
print("SPY DAILY CHANGE (known at close) vs Overnight Returns")
print("="*80)

# Test if SPY daily change predicts overnight
categories = {
    "SPY Daily > +2% (strong green)": df['SPY_DailyChange'] > 2,
    "SPY Daily > +1% (green)": df['SPY_DailyChange'] > 1,
    "SPY Daily > +0.5%": df['SPY_DailyChange'] > 0.5,
    "SPY Daily > 0% (up)": df['SPY_DailyChange'] > 0,
    "SPY Daily ≈ 0% (-0.5% to +0.5%)": (df['SPY_DailyChange'].between(-0.5, 0.5)),
    "SPY Daily < 0% (down)": df['SPY_DailyChange'] < 0,
    "SPY Daily < -0.5%": df['SPY_DailyChange'] < -0.5,
    "SPY Daily < -1% (red)": df['SPY_DailyChange'] < -1,
    "SPY Daily < -2% (strong red)": df['SPY_DailyChange'] < -2,
}

print(f"\n{'SPY Daily Condition':<40} {'N':>8} {'Wins':>7} {'Losses':>7} {'WR%':>7} {'AvgRet':>10}")
print("-"*80)

for name, mask in categories.items():
    subset = df[mask]
    if len(subset) < 30:
        continue
    wins = (subset['OvernightReturn'] > 0).sum()
    losses = (subset['OvernightReturn'] <= 0).sum()
    wr = wins / len(subset) * 100
    avg = subset['OvernightReturn'].mean()
    mark = "🔥" if wr >= 55 else "⭐" if wr >= 53 else "❌" if wr < 48 else ""
    print(f"{name:<40} {len(subset):>8,} {wins:>7} {losses:>7} {wr:>6.2f}% {avg:>9.4f}% {mark}")

print("\n" + "="*80)
print("COMBINED — Stock condition + SPY Daily Change (NO look-ahead)")
print("="*80)

combined = {
    "Stock Change<-2% + SPY Daily>+1%": (df['ChangePct'] < -2) & (df['SPY_DailyChange'] > 1),
    "Stock Change<-2% + SPY Daily>+0.5%": (df['ChangePct'] < -2) & (df['SPY_DailyChange'] > 0.5),
    "Stock Change<-2% + SPY Daily>0%": (df['ChangePct'] < -2) & (df['SPY_DailyChange'] > 0),
    "Stock Change<-2% + SPY Daily<0%": (df['ChangePct'] < -2) & (df['SPY_DailyChange'] < 0),
    "Stock Change>+2% + SPY Daily>+1%": (df['ChangePct'] > 2) & (df['SPY_DailyChange'] > 1),
    "Stock Change>+2% + SPY Daily>0%": (df['ChangePct'] > 2) & (df['SPY_DailyChange'] > 0),
    "Stock RSI<30 + SPY Daily>+0.5%": (df['RSI'] < 30) & (df['SPY_DailyChange'] > 0.5),
    "Stock BB>90 + SPY Daily>+0.5%": (df['BB_Position'] > 90) & (df['ChangePct'] < -2) & (df['SPY_DailyChange'] > 0.5),
    "Tuesday + Stock Change<-2% + SPY Daily>0%": (df['DayOfWeek'] == 'Tuesday') & (df['ChangePct'] < -2) & (df['SPY_DailyChange'] > 0),
}

print(f"\n{'Combined Condition':<55} {'N':>8} {'WR%':>7} {'AvgRet':>10}")
print("-"*75)

best_combos = []
for name, mask in combined.items():
    subset = df[mask]
    if len(subset) < 30:
        continue
    wins = (subset['OvernightReturn'] > 0).sum()
    wr = wins / len(subset) * 100
    avg = subset['OvernightReturn'].mean()
    mark = "🔥" if wr >= 60 else "⭐" if wr >= 55 else ""
    print(f"{name:<55} {len(subset):>8,} {wr:>6.2f}% {avg:>9.4f}% {mark}")
    best_combos.append({'name': name, 'n': len(subset), 'wr': wr, 'avg': avg})

# Sort by win rate
best_combos.sort(key=lambda x: -x['wr'])

print("\n" + "="*80)
print("TOP PERFORMERS (no look-ahead bias)")
print("="*80)
for c in best_combos[:5]:
    print(f"  {c['name']}: {c['wr']:.2f}% WR ({c['n']} trades, {c['avg']:.4f}% avg)")

# Compare: SPY Daily vs SPY Overnight
print("\n" + "="*80)
print("COMPARISON: SPY Daily Change vs SPY Overnight (look-ahead)")
print("="*80)

print("\nSPY Overnight (look-ahead — future data, NOT usable):")
for name, mask in [
    ("SPY Overnight > +0.5%", df['SPY_Overnight'] > 0.5),
    ("SPY Overnight > 0%", df['SPY_Overnight'] > 0),
    ("SPY Overnight < 0%", df['SPY_Overnight'] < 0),
]:
    subset = df[mask]
    wr = (subset['OvernightReturn'] > 0).mean() * 100
    print(f"  {name:<35} WR = {wr:.2f}%")

print("\nSPY Daily Change (known at close — USABLE in real-time):")
for name, mask in [
    ("SPY Daily > +1%", df['SPY_DailyChange'] > 1),
    ("SPY Daily > +0.5%", df['SPY_DailyChange'] > 0.5),
    ("SPY Daily > 0%", df['SPY_DailyChange'] > 0),
    ("SPY Daily < 0%", df['SPY_DailyChange'] < 0),
]:
    subset = df[mask]
    if len(subset) > 100:
        wr = (subset['OvernightReturn'] > 0).mean() * 100
        print(f"  {name:<35} WR = {wr:.2f}%")

# Save
results = {
    'analysis': 'no_lookahead_bias',
    'spy_daily_factor': True,
    'best_combinations': best_combos,
    'note': 'SPY_DailyChange is known at close, unlike SPY_Overnight which is future data',
    'date': datetime.now().isoformat(),
}

with open('research/no_lookahead_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n\nSaved: research/no_lookahead_analysis.json")
print("="*80)
print("ANALYSIS COMPLETE — NO LOOK-AHEAD BIAS")
print("="*80)

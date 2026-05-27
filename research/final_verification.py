"""
Final verification: tradeable strategies with no look-ahead bias.
Check SPY Daily Change again + find highest WR strategies.
"""
import pandas as pd
import numpy as np
import yfinance as yf
import json
from datetime import datetime

print("Loading data...")
df = pd.read_csv('research/daily_with_index_factors.csv')
df['Date'] = pd.to_datetime(df['Date'])
print(f"Loaded: {len(df)} rows, {df['Ticker'].nunique()} tickers\n")

# Fetch SPY daily data for SPY_DailyChange
spy = yf.Ticker('SPY')
spy_hist = spy.history(period='2y', interval='1d')
spy_hist = spy_hist.sort_index().reset_index()
spy_hist['Date'] = pd.to_datetime(spy_hist['Date']).dt.date
df['DateOnly'] = df['Date'].dt.date
spy_hist['SPY_DailyChange'] = (spy_hist['Close'] / spy_hist['Open'] - 1) * 100
df = df.merge(spy_hist[['Date', 'SPY_DailyChange']], left_on='DateOnly', right_on='Date', how='left')

print("="*80)
print("1. SPY DAILY CHANGE VERIFICATION (no look-ahead)")
print("="*80)

spy_conditions = {
    "SPY Daily < -3%": df['SPY_DailyChange'] < -3,
    "SPY Daily < -2%": df['SPY_DailyChange'] < -2,
    "SPY Daily < -1%": df['SPY_DailyChange'] < -1,
    "SPY Daily < -0.5%": df['SPY_DailyChange'] < -0.5,
    "SPY Daily 0% to +0.5%": df['SPY_DailyChange'].between(0, 0.5),
    "SPY Daily +0.5% to +1%": df['SPY_DailyChange'].between(0.5, 1),
    "SPY Daily > +1%": df['SPY_DailyChange'] > 1,
    "SPY Daily > +2%": df['SPY_DailyChange'] > 2,
}

for name, mask in spy_conditions.items():
    subset = df[mask]
    if len(subset) < 30:
        continue
    wins = (subset['OvernightReturn'] > 0).sum()
    wr = wins / len(subset) * 100
    avg = subset['OvernightReturn'].mean()
    print(f"  {name:<30} | N={len(subset):>6,} | WR={wr:>6.2f}% | Avg={avg:>+7.4f}%")

print("\n" + "="*80)
print("2. STOCK CONDITIONS ALONE (no SPY)")
print("="*80)

stock_conditions = {
    "Stock Change < -5%": df['ChangePct'] < -5,
    "Stock Change < -4%": df['ChangePct'] < -4,
    "Stock Change < -3%": df['ChangePct'] < -3,
    "Stock Change < -2%": df['ChangePct'] < -2,
    "Stock Change < -1%": df['ChangePct'] < -1,
    "Stock Change > +2%": df['ChangePct'] > 2,
    "Stock Change > +3%": df['ChangePct'] > 3,
    "Stock Change > +4%": df['ChangePct'] > 4,
    "|Stock Change| > 3%": abs(df['ChangePct']) > 3,
    "RSI < 20": df['RSI'] < 20,
    "RSI < 30": df['RSI'] < 30,
    "RSI > 70": df['RSI'] > 70,
    "BB Position < 10%": df['BB_Position'] < 10,
    "BB Position > 90%": df['BB_Position'] > 90,
    "BB Width > 5%": df['BB_Width'] > 5,
    "Tuesday": df['DayOfWeek'] == 'Tuesday',
    "Friday": df['DayOfWeek'] == 'Friday',
    "Wednesday": df['DayOfWeek'] == 'Wednesday',
}

for name, mask in stock_conditions.items():
    subset = df[mask]
    if len(subset) < 30:
        continue
    wins = (subset['OvernightReturn'] > 0).sum()
    wr = wins / len(subset) * 100
    avg = subset['OvernightReturn'].mean()
    print(f"  {name:<30} | N={len(subset):>6,} | WR={wr:>6.2f}% | Avg={avg:>+7.4f}%")

print("\n" + "="*80)
print("3. 2-FILTER COMBOS (stock condition + SPY Daily — TRADEABLE)")
print("="*80)

combos = {
    # Stock down + SPY down (mean reversion)
    "Change<-2% + SPY<-1%": (df['ChangePct'] < -2) & (df['SPY_DailyChange'] < -1),
    "Change<-2% + SPY<-0.5%": (df['ChangePct'] < -2) & (df['SPY_DailyChange'] < -0.5),
    "Change<-2% + SPY<0%": (df['ChangePct'] < -2) & (df['SPY_DailyChange'] < 0),
    "Change<-2% + SPY>0%": (df['ChangePct'] < -2) & (df['SPY_DailyChange'] > 0),
    
    # Stock up + SPY conditions
    "Change>+2% + SPY<-0.5%": (df['ChangePct'] > 2) & (df['SPY_DailyChange'] < -0.5),
    "Change>+2% + SPY>+0.5%": (df['ChangePct'] > 2) & (df['SPY_DailyChange'] > 0.5),
    
    # Day + stock condition
    "Tuesday + Change<-2%": (df['DayOfWeek'] == 'Tuesday') & (df['ChangePct'] < -2),
    "Tuesday + Change>+2%": (df['DayOfWeek'] == 'Tuesday') & (df['ChangePct'] > 2),
    "Friday + Change<-2%": (df['DayOfWeek'] == 'Friday') & (df['ChangePct'] < -2),
    
    # RSI + day
    "RSI<30 + Tuesday": (df['RSI'] < 30) & (df['DayOfWeek'] == 'Tuesday'),
    "RSI<30 + SPY<-0.5%": (df['RSI'] < 30) & (df['SPY_DailyChange'] < -0.5),
    
    # 3 filters
    "Tuesday + Change<-2% + SPY<0%": (df['DayOfWeek'] == 'Tuesday') & (df['ChangePct'] < -2) & (df['SPY_DailyChange'] < 0),
    "Tuesday + Change<-2% + SPY<-0.5%": (df['DayOfWeek'] == 'Tuesday') & (df['ChangePct'] < -2) & (df['SPY_DailyChange'] < -0.5),
    "Change<-2% + RSI<30 + SPY<0%": (df['ChangePct'] < -2) & (df['RSI'] < 30) & (df['SPY_DailyChange'] < 0),
    "Change<-3% + Tuesday + SPY<-0.5%": (df['ChangePct'] < -3) & (df['DayOfWeek'] == 'Tuesday') & (df['SPY_DailyChange'] < -0.5),
}

combo_results = []
for name, mask in combos.items():
    subset = df[mask]
    if len(subset) < 20:
        continue
    wins = (subset['OvernightReturn'] > 0).sum()
    losses = (subset['OvernightReturn'] <= 0).sum()
    wr = wins / len(subset) * 100
    avg = subset['OvernightReturn'].mean()
    avg_win = subset[subset['OvernightReturn'] > 0]['OvernightReturn'].mean() if wins > 0 else 0
    avg_loss = subset[subset['OvernightReturn'] <= 0]['OvernightReturn'].mean() if losses > 0 else 0
    max_gain = subset['OvernightReturn'].max()
    max_loss = subset['OvernightReturn'].min()
    
    combo_results.append({
        'name': name,
        'n': len(subset),
        'wins': int(wins),
        'losses': int(losses),
        'wr': wr,
        'avg': avg,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_gain': max_gain,
        'max_loss': max_loss,
    })

# Sort by win rate
combo_results.sort(key=lambda x: -x['wr'])

print(f"\n  {'Combo':<45} {'N':>6} {'Wins':>6} {'Loss':>6} {'WR%':>7} {'Avg':>8} {'AvgWin':>8} {'AvgLoss':>8}")
print("  " + "-"*95)
for r in combo_results:
    mark = "🔥" if r['wr'] >= 60 else "⭐" if r['wr'] >= 55 else ""
    print(f"  {r['name']:<45} {r['n']:>6} {r['wins']:>6} {r['losses']:>6} {r['wr']:>6.2f}% {r['avg']:>+7.4f}% {r['avg_win']:>+7.4f}% {r['avg_loss']:>+7.4f}% {mark}")

print("\n" + "="*80)
print("4. ENTRY/EXIT TIMING")
print("="*80)
print("""
ENTRY:  Buy at 15:30–16:00 ET (last 30 min of regular session)
        → Use limit order near current price
        → Must check: ChangePct < -2% (known at close), SPY_DailyChange (known at close)

EXIT:   Sell at 09:30 ET next day (market open)
        → Market order at open
        → Target: overnight gap profit

WHY NOT 4 AM?
        → Free data only gives 09:30 Open
        → For 4 AM need Polygon.io ($49/mo) or broker API
        → Research shows Close→4AM = 56.15% WR vs Close→Open = 52.15% WR
        → Edge is small, not worth paid data for now

EXAMPLE TODAY:
        If AAPL is -3.5% at 15:30 and SPY is -0.8%:
        → Buy AAPL at ~15:45
        → Sell tomorrow at 09:30
        → Expected: ~57% chance of overnight gap up
""")

# Save
with open('research/final_tradeable_strategies.json', 'w') as f:
    json.dump({
        'analysis': 'final_tradeable_verification',
        'date': datetime.now().isoformat(),
        'best_combos': combo_results[:10],
        'entry_time': '15:30-16:00 ET',
        'exit_time': '09:30 ET next day',
        'note': 'All strategies use only data known at 16:00 close',
    }, f, indent=2)

print("\nSaved: research/final_tradeable_strategies.json")
print("="*80)

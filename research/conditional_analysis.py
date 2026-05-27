"""
Conditional Analysis — for each specific condition, show win/loss distribution.
"""
import pandas as pd
import json
from datetime import datetime

print("Loading data...")
df = pd.read_csv('research/daily_with_index_factors.csv')
df['Date'] = pd.to_datetime(df['Date'])
print(f"Loaded: {len(df)} rows, {df['Ticker'].nunique()} tickers\n")

print("="*80)
print("CONDITIONAL ANALYSIS — Overnight Returns by Filter")
print("="*80)

conditions = {
    # Change conditions
    "Change < -4%": df['ChangePct'] < -4,
    "Change < -3%": df['ChangePct'] < -3,
    "Change < -2%": df['ChangePct'] < -2,
    "Change < -1%": df['ChangePct'] < -1,
    "Change > +1%": df['ChangePct'] > 1,
    "Change > +2%": df['ChangePct'] > 2,
    "Change > +3%": df['ChangePct'] > 3,
    "Change > +4%": df['ChangePct'] > 4,
    "|Change| > 3% (any direction)": abs(df['ChangePct']) > 3,
    
    # RSI
    "RSI < 20 (oversold)": df['RSI'] < 20,
    "RSI < 30 (oversold)": df['RSI'] < 30,
    "RSI > 70 (overbought)": df['RSI'] > 70,
    "RSI > 80 (overbought)": df['RSI'] > 80,
    
    # Bollinger Bands
    "BB Position < 10% (near lower)": df['BB_Position'] < 10,
    "BB Position > 90% (near upper)": df['BB_Position'] > 90,
    "BB Width > 5% (volatile)": df['BB_Width'] > 5,
    
    # MACD
    "MACD < 0 (bearish)": df['MACD'] < 0,
    "MACD > 0 (bullish)": df['MACD'] > 0,
    "MACD Histogram < 0": df['MACD_Hist'] < 0,
    "MACD Histogram > 0": df['MACD_Hist'] > 0,
    
    # Day of week
    "Monday": df['DayOfWeek'] == 'Monday',
    "Tuesday": df['DayOfWeek'] == 'Tuesday',
    "Wednesday": df['DayOfWeek'] == 'Wednesday',
    "Thursday": df['DayOfWeek'] == 'Thursday',
    "Friday": df['DayOfWeek'] == 'Friday',
    
    # SPY Context
    "SPY Up overnight": df['SPY_Overnight'] > 0,
    "SPY Down overnight": df['SPY_Overnight'] < 0,
    "SPY Strong Up (>0.5%)": df['SPY_Overnight'] > 0.5,
    "SPY Strong Down (<-0.5%)": df['SPY_Overnight'] < -0.5,
    
    # Combined — most important
    "Change < -2% + Tuesday": (df['ChangePct'] < -2) & (df['DayOfWeek'] == 'Tuesday'),
    "Change < -2% + SPY Up": (df['ChangePct'] < -2) & (df['SPY_Overnight'] > 0),
    "Change < -2% + SPY Strong Up": (df['ChangePct'] < -2) & (df['SPY_Overnight'] > 0.5),
    "RSI < 30 + Change < -2%": (df['RSI'] < 30) & (df['ChangePct'] < -2),
    "BB > 90 + Change < -2%": (df['BB_Position'] > 90) & (df['ChangePct'] < -2),
    "Change > 2% + Tuesday": (df['ChangePct'] > 2) & (df['DayOfWeek'] == 'Tuesday'),
    "Change > 2% + SPY Strong Up": (df['ChangePct'] > 2) & (df['SPY_Overnight'] > 0.5),
}

results = []

for name, mask in conditions.items():
    subset = df[mask]
    n = len(subset)
    if n < 30:
        continue
    
    wins = (subset['OvernightReturn'] > 0).sum()
    losses = (subset['OvernightReturn'] <= 0).sum()
    win_rate = wins / n * 100
    
    avg_win = subset[subset['OvernightReturn'] > 0]['OvernightReturn'].mean() if wins > 0 else 0
    avg_loss = subset[subset['OvernightReturn'] <= 0]['OvernightReturn'].mean() if losses > 0 else 0
    
    max_gain = subset['OvernightReturn'].max()
    max_loss = subset['OvernightReturn'].min()
    
    avg_all = subset['OvernightReturn'].mean()
    
    results.append({
        'condition': name,
        'n': n,
        'wins': int(wins),
        'losses': int(losses),
        'win_rate': round(win_rate, 2),
        'avg_return': round(avg_all, 4),
        'avg_win': round(avg_win, 4),
        'avg_loss': round(avg_loss, 4),
        'max_gain': round(max_gain, 2),
        'max_loss': round(max_loss, 2),
    })

# Sort by win rate
results.sort(key=lambda x: -x['win_rate'])

print(f"\n{'Condition':<45} {'N':>6} {'Wins':>7} {'Losses':>7} {'WR%':>7} {'AvgRet':>9} {'AvgWin':>9} {'AvgLoss':>9} {'MaxGain':>8} {'MaxLoss':>8}")
print("-" * 125)

for r in results:
    mark = "🔥" if r['win_rate'] >= 60 else "⭐" if r['win_rate'] >= 55 else ""
    print(f"{r['condition']:<45} {r['n']:>6,} {r['wins']:>7} {r['losses']:>7} {r['win_rate']:>6.2f}% {r['avg_return']:>8.4f}% {r['avg_win']:>8.4f}% {r['avg_loss']:>8.4f}% {r['max_gain']:>7.2f}% {r['max_loss']:>7.2f}% {mark}")

# Save
with open('research/conditional_analysis_results.json', 'w') as f:
    json.dump({
        'analysis': 'conditional_by_filter',
        'total_observations': len(df),
        'conditions': results,
        'date': datetime.now().isoformat(),
    }, f, indent=2)

print(f"\n\nSaved: research/conditional_analysis_results.json")
print("="*80)
print("CONDITIONAL ANALYSIS COMPLETE")
print("="*80)

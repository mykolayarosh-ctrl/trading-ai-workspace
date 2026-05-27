"""
Add sector data to daily results and analyze by sector.
"""
import pandas as pd
import yfinance as yf
import json
from datetime import datetime
import time

print("Loading data...")
df = pd.read_csv('research/daily_with_index_factors.csv')
print(f"Loaded: {len(df)} rows, {df['Ticker'].nunique()} tickers")

# Get unique tickers
tickers = df['Ticker'].unique().tolist()
print(f"Fetching sector info for {len(tickers)} tickers...")

# Fetch sector info via yfinance (batch for speed)
sector_map = {}
batch_size = 50
for i in range(0, len(tickers), batch_size):
    batch = tickers[i:i+batch_size]
    print(f"  Batch {i//batch_size + 1}/{(len(tickers)-1)//batch_size + 1}: {len(batch)} tickers")
    for ticker in batch:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            sector_map[ticker] = {'sector': sector, 'industry': industry}
        except Exception as e:
            sector_map[ticker] = {'sector': 'Unknown', 'industry': 'Unknown'}
        time.sleep(0.01)

# Add to dataframe
df['Sector'] = df['Ticker'].map(lambda x: sector_map.get(x, {}).get('sector', 'Unknown'))
df['Industry'] = df['Ticker'].map(lambda x: sector_map.get(x, {}).get('industry', 'Unknown'))

# Save enriched data
df.to_csv('research/daily_with_sectors.csv', index=False)
print(f"\nSaved: research/daily_with_sectors.csv")

# Analysis
print("\n" + "="*70)
print("SECTOR ANALYSIS")
print("="*70)

baseline = (df['OvernightReturn'] > 0).mean() * 100
print(f"Baseline: {baseline:.2f}% WR\n")

sector_stats = []
for sector in df['Sector'].unique():
    if sector == 'Unknown':
        continue
    subset = df[df['Sector'] == sector]
    if len(subset) < 100:
        continue
    wr = (subset['OvernightReturn'] > 0).mean() * 100
    avg_ret = subset['OvernightReturn'].mean()
    avg_vol = subset['Volume'].mean()
    tickers_in_sector = subset['Ticker'].nunique()
    sector_stats.append({
        'sector': sector,
        'trades': len(subset),
        'tickers': tickers_in_sector,
        'win_rate': wr,
        'avg_return': avg_ret,
    })

sector_stats.sort(key=lambda x: -x['win_rate'])

print(f"{'Sector':<30} {'Tickers':>8} {'Trades':>8} {'WinRate':>10} {'AvgRet':>10}")
print("-"*70)
for s in sector_stats:
    mark = "🔥" if s['win_rate'] >= 55 else "⭐" if s['win_rate'] >= 53 else ""
    print(f"{s['sector']:<30} {s['tickers']:>8} {s['trades']:>8,} {s['win_rate']:>9.2f}% {s['avg_return']:>9.4f}% {mark}")

# With SPY context
print("\n" + "="*70)
print("SECTOR + SPY STRONG UP COMBOS")
print("="*70)

spy_sector = []
for sector in df['Sector'].unique():
    if sector == 'Unknown':
        continue
    mask = (df['Sector'] == sector) & (df['SPY_Overnight'] > 0.5)
    subset = df[mask]
    if len(subset) >= 20:
        wr = (subset['OvernightReturn'] > 0).mean() * 100
        avg = subset['OvernightReturn'].mean()
        spy_sector.append({
            'sector': sector,
            'trades': len(subset),
            'win_rate': wr,
            'avg_return': avg,
        })

spy_sector.sort(key=lambda x: -x['win_rate'])

print(f"{'Sector':<30} {'Trades':>8} {'WinRate':>10} {'AvgRet':>10}")
print("-"*60)
for s in spy_sector[:15]:
    mark = "🔥" if s['win_rate'] >= 70 else "⭐" if s['win_rate'] >= 60 else ""
    print(f"{s['sector']:<30} {s['trades']:>8,} {s['win_rate']:>9.2f}% {s['avg_return']:>9.4f}% {mark}")

# Industry breakdown for top sector
print("\n" + "="*70)
print("INDUSTRY BREAKDOWN — TOP PERFORMING SECTOR")
print("="*70)

if sector_stats:
    top_sector = sector_stats[0]['sector']
    industry_stats = []
    for industry in df[df['Sector'] == top_sector]['Industry'].unique():
        if industry == 'Unknown':
            continue
        subset = df[(df['Sector'] == top_sector) & (df['Industry'] == industry)]
        if len(subset) < 20:
            continue
        wr = (subset['OvernightReturn'] > 0).mean() * 100
        avg = subset['OvernightReturn'].mean()
        industry_stats.append({
            'industry': industry,
            'trades': len(subset),
            'win_rate': wr,
            'avg_return': avg,
        })
    
    industry_stats.sort(key=lambda x: -x['win_rate'])
    print(f"Top sector: {top_sector}")
    print(f"{'Industry':<40} {'Trades':>8} {'WinRate':>10} {'AvgRet':>10}")
    print("-"*70)
    for ind in industry_stats[:10]:
        print(f"{ind['industry']:<40} {ind['trades']:>8,} {ind['win_rate']:>9.2f}% {ind['avg_return']:>9.4f}%")

# Save results
results = {
    'analysis_type': 'sector',
    'baseline_win_rate': round(baseline, 2),
    'sector_ranking': sector_stats,
    'spy_strong_up_sector': spy_sector,
    'date': datetime.now().isoformat(),
}

with open('research/sector_analysis_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"\nSaved: research/sector_analysis_results.json")
print("\n" + "="*70)
print("SECTOR ANALYSIS COMPLETE")
print("="*70)

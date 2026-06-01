#!/usr/bin/env python3
"""Test yfinance prepost=True for pre-market data (4 AM vs 9:30 AM open)."""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Download 7 days of 1-minute data with pre/post market (max 8 days per request)
print("Downloading SPY 1-minute data with pre/post market (7 days)...")
spy = yf.Ticker("SPY")
df = spy.history(period="7d", interval="1m", prepost=True)

print(f"Total rows: {len(df)}")
print(f"Date range: {df.index.min()} to {df.index.max()}")
print(f"\nSample data:")
print(df.head(10))

# Check timezone
print(f"\nTimezone: {df.index.tz}")

# Convert to US/Eastern if needed
if df.index.tz is not None:
    df.index = df.index.tz_convert('US/Eastern')

# Extract pre-market data (before 9:30 AM)
df['hour'] = df.index.hour
df['minute'] = df.index.minute
df['time'] = df.index.time

# 4:00 AM data
df_4am = df[(df['hour'] == 4) & (df['minute'] == 0)]
# 9:30 AM data  
df_930 = df[(df['hour'] == 9) & (df['minute'] == 30)]

print(f"\n4:00 AM entries: {len(df_4am)}")
print(f"9:30 AM entries: {len(df_930)}")

# For each trading day, get 4 AM price and 9:30 AM open
results = []

# Group by date
for date, group in df.groupby(df.index.date):
    # Get first pre-market price (around 4 AM)
    premarket = group[(group['hour'] >= 4) & (group['hour'] < 9)]
    
    # Get 9:30 AM open
    open_930 = group[(group['hour'] == 9) & (group['minute'] == 30)]
    
    if len(premarket) > 0 and len(open_930) > 0:
        first_premarket = premarket.iloc[0]
        open_price = open_930.iloc[0]
        
        results.append({
            'date': date,
            'first_premarket_time': premarket.index[0],
            'first_premarket_price': first_premarket['Close'],
            'open_930_time': open_930.index[0],
            'open_930_price': open_price['Close'],
            'gap_pct': ((open_price['Close'] - first_premarket['Close']) / first_premarket['Close']) * 100
        })

results_df = pd.DataFrame(results)
print(f"\nMatched days: {len(results_df)}")

if len(results_df) > 0:
    print(f"\nGap from 4 AM to 9:30 AM Open:")
    print(f"  Mean gap: {results_df['gap_pct'].mean():.3f}%")
    print(f"  Median gap: {results_df['gap_pct'].median():.3f}%")
    print(f"  Std: {results_df['gap_pct'].std():.3f}%")
    print(f"  Positive gaps: {(results_df['gap_pct'] > 0).sum()} / {len(results_df)} ({(results_df['gap_pct'] > 0).mean()*100:.1f}%)")
    print(f"  Negative gaps: {(results_df['gap_pct'] < 0).sum()} / {len(results_df)} ({(results_df['gap_pct'] < 0).mean()*100:.1f}%)")
    
    # Show some examples
    print(f"\nLargest positive gaps:")
    print(results_df.nlargest(5, 'gap_pct')[['date', 'first_premarket_price', 'open_930_price', 'gap_pct']])
    
    print(f"\nLargest negative gaps:")
    print(results_df.nsmallest(5, 'gap_pct')[['date', 'first_premarket_price', 'open_930_price', 'gap_pct']])
    
    # Save results
    results_df.to_csv('/tmp/premarket_analysis.csv', index=False)
    print(f"\nSaved to /tmp/premarket_analysis.csv")
else:
    print("No matching days found!")
    # Debug: show unique hours
    print(f"\nUnique hours in data:")
    print(df['hour'].unique())

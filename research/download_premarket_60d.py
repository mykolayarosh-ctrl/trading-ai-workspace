#!/usr/bin/env python3
"""Download 60 days of pre-market data from yfinance and compare Close→4AM vs Close→9:30AM."""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Download in chunks of 7 days (yfinance limit for 1m data)
end_date = datetime.now()
all_data = []

print("Downloading 60 days of SPY 1-minute data in 7-day chunks...")
for i in range(9):  # 9 chunks * 7 days = ~63 days
    chunk_end = end_date - timedelta(days=i*7)
    chunk_start = chunk_end - timedelta(days=8)
    
    try:
        spy = yf.Ticker("SPY")
        df = spy.history(start=chunk_start.strftime('%Y-%m-%d'), 
                        end=chunk_end.strftime('%Y-%m-%d'),
                        interval="1m", prepost=True)
        
        if len(df) > 0:
            print(f"  Chunk {i+1}: {chunk_start.date()} to {chunk_end.date()} = {len(df)} rows")
            all_data.append(df)
        else:
            print(f"  Chunk {i+1}: No data")
            
    except Exception as e:
        print(f"  Chunk {i+1}: Error - {e}")
    
    time.sleep(1)  # Rate limit

# Combine all data
if len(all_data) == 0:
    print("No data downloaded!")
    exit()

combined = pd.concat(all_data)
combined = combined[~combined.index.duplicated(keep='first')]
combined = combined.sort_index()

print(f"\nTotal combined rows: {len(combined)}")
print(f"Date range: {combined.index.min()} to {combined.index.max()}")

# Convert timezone
if combined.index.tz is not None:
    combined.index = combined.index.tz_convert('US/Eastern')

combined['hour'] = combined.index.hour
combined['minute'] = combined.index.minute

# Extract key prices per day
results = []
for date, group in combined.groupby(combined.index.date):
    # Previous day close (last price before 4 PM of previous day)
    # Today 4 AM first price
    premarket = group[(group['hour'] >= 4) & (group['hour'] < 9)]
    # 9:30 AM open
    open_930 = group[(group['hour'] == 9) & (group['minute'] == 30)]
    # 4 PM close
    close_4pm = group[(group['hour'] == 16) & (group['minute'] == 0)]
    
    if len(premarket) > 0 and len(open_930) > 0:
        first_4am = premarket.iloc[0]
        open_price = open_930.iloc[0]
        
        # Also get last price before 9:30 (pre-market close)
        premarket_last = premarket.iloc[-1]
        
        results.append({
            'date': date,
            'am4_price': first_4am['Close'],
            'am4_time': premarket.index[0],
            'premarket_last': premarket_last['Close'],
            'premarket_time': premarket.index[-1],
            'open_930': open_price['Close'],
            'gap_4am_to_open': ((open_price['Close'] - first_4am['Close']) / first_4am['Close']) * 100,
            'premarket_move': ((premarket_last['Close'] - first_4am['Close']) / first_4am['Close']) * 100,
        })

results_df = pd.DataFrame(results)
print(f"\nMatched trading days: {len(results_df)}")

if len(results_df) >= 10:
    print(f"\n=== 4 AM to 9:30 AM Gap Analysis ===")
    print(f"Mean gap: {results_df['gap_4am_to_open'].mean():.3f}%")
    print(f"Median gap: {results_df['gap_4am_to_open'].median():.3f}%")
    print(f"Std: {results_df['gap_4am_to_open'].std():.3f}%")
    print(f"Positive: {(results_df['gap_4am_to_open'] > 0).mean()*100:.1f}%")
    
    print(f"\n=== Pre-market Movement (4 AM → 9:30 AM last price) ===")
    print(f"Mean move: {results_df['premarket_move'].mean():.3f}%")
    print(f"Median move: {results_df['premarket_move'].median():.3f}%")
    print(f"Std: {results_df['premarket_move'].std():.3f}%")
    
    # Save
    results_df.to_csv('/tmp/premarket_60days.csv', index=False)
    print(f"\nSaved to /tmp/premarket_60days.csv")
else:
    print("Not enough data")

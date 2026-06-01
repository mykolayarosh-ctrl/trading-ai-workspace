#!/usr/bin/env python3
"""
Overnight Gap Strategy Backtest for S&P 500
Strategy: Buy at Close → Sell at next day Open (or pre-market proxy)
Analyzes: correlations between day features and overnight returns
"""
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import warnings, time, json, sys, os
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

sns.set_style('darkgrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['figure.dpi'] = 120

def fetch_sp500():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        return tables[0]['Symbol'].tolist()
    except Exception as e:
        print(f"Wiki error: {e}")
        # Fallback hard list
        return ['AAPL','MSFT','NVDA','GOOGL','AMZN','META','TSLA','BRK-B','AVGO','TSM',
                'WMT','JPM','V','MA','UNH','XOM','HD','PG','COST','ABBV','KO','PEP',
                'PFE','MRK','JNJ','BAC','DIS','NFLX','ADBE','CRM','INTC','AMD','QCOM',
                'TXN','IBM','GE','HON','CAT','GS','MS','BLK','RTX','BA','LMT','NOC',
                'MMM','UPS','FDX','SBUX','MCD','NKE','VZ','T','CMCSA','TMUS','SPGI',
                'ISRG','ZTS','BMY','LLY','ABT','MDT','GILD','AMGN','CVS','CI','ELV',
                'UNP','CSX','NSC','DE','AGCO','F','GM','STLA','FCX','NEM','DOW',
                'APD','LIN','SHW','ECL','PPG','NUE','STLD','MT','VALE','RIO','BHP',
                'OXY','COP','CVX','SLB','HAL','BKR','PSX','VLO','MPC','ENPH','SEDG',
                'FSLR','NEE','DUK','SO','AEP','EXC','SRE','WEC','ES','ETR','CNP',
                'D','ED','PEG','FE','AEE','LNT','XEL','WMB','KMI','OKE','ET',
                'EPD','MPLX','ETRN','TRGP','KFT','CAG','CPB','GIS','HSY','HRL',
                'K','KHC','MKC','SJM','TSN','ADM','BG','INGR','FLO','LANC','PPC',
                'PFGC','SYY','USFD','CHEF','DRI','MCD','YUM','CMG','SBUX','DPZ',
                'CAKE','SHAK','WING','TXRH','BJRI','PLAY','RICK','DENN','LOCO',
                'GTIM','KR','COST','WMT','TGT','BJ','DG','DLTR','FIVE','BIG',
                'PSMT','IMKTA','VLGEA','WMK','SPTN','UNFI','ANDE','CHEF','CORE',
                'GO','SPB','HELE','NWL','TUP','EPC','ENR','SPWH','BGFV','HIBB',
                'DKS','ASO','BURL','ROST','TJX','BKE','ANF','AEO','URBN','LE',
                'GES','MOV','SCVL','SHOO','CAL','DLTH','DESP','EXPI','KVYO','ZIP']

def batch_download(tickers, period='1y'):
    """Download data in batches and return dict of DataFrames."""
    all_data = {}
    batch_size = 50
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        print(f"Batch {i//batch_size + 1}/{(len(tickers)-1)//batch_size + 1}: {len(batch)} tickers")
        try:
            data = yf.download(batch, period=period, interval='1d', 
                             group_by='ticker', auto_adjust=True, progress=False, threads=True)
            if data.empty:
                continue
            for t in batch:
                if len(batch) == 1:
                    df = data.copy()
                else:
                    if t not in data.columns.get_level_values(0):
                        continue
                    df = data[t].copy()
                if df.empty or len(df) < 30:
                    continue
                df = df.dropna()
                if len(df) < 20:
                    continue
                all_data[t] = df
        except Exception as e:
            print(f"  Batch error: {e}")
        time.sleep(0.3)
    return all_data

def compute_features(df):
    """Add day features and overnight return."""
    df = df.copy()
    df['ChangePct'] = df['Close'].pct_change() * 100
    df['PrevClose'] = df['Close'].shift(1)
    
    # Overnight return: next day's open vs today's close
    df['NextOpen'] = df['Open'].shift(-1)
    df['OvernightReturn'] = (df['NextOpen'] / df['Close'] - 1) * 100
    
    # 20-day range
    df['20D_High'] = df['High'].rolling(20).max()
    df['20D_Low'] = df['Low'].rolling(20).min()
    df['20D_Range'] = ((df['Close'] - df['20D_Low']) / (df['20D_High'] - df['20D_Low'])) * 100
    
    # Volume ratio
    df['AvgVolume20'] = df['Volume'].rolling(20).mean()
    df['VolRatio'] = df['Volume'] / df['AvgVolume20']
    
    # 5-day change
    df['5D_Change'] = (df['Close'] / df['Close'].shift(5) - 1) * 100
    
    # Abs change
    df['AbsChange'] = df['ChangePct'].abs()
    
    # Direction (bullish/bearish)
    df['Direction'] = np.where(df['ChangePct'] > 0, 'Up', np.where(df['ChangePct'] < 0, 'Down', 'Flat'))
    
    return df

def analyze_strategy(all_data):
    """Aggregate all overnight returns and analyze by features."""
    records = []
    for ticker, df in all_data.items():
        df = compute_features(df)
        # Drop rows with missing overnight return or insufficient history
        valid = df.dropna(subset=['OvernightReturn', '20D_Range', 'VolRatio', '5D_Change'])
        for idx, row in valid.iterrows():
            records.append({
                'Ticker': ticker,
                'Date': idx,
                'ClosePrice': row['Close'],
                'ChangePct': row['ChangePct'],
                'AbsChange': row['AbsChange'],
                'OvernightReturn': row['OvernightReturn'],
                '20D_Range': row['20D_Range'],
                'VolRatio': row['VolRatio'],
                '5D_Change': row['5D_Change'],
                'Direction': row['Direction'],
                'Volume': row['Volume'],
                'DayOfWeek': idx.strftime('%A'),
            })
    
    df_all = pd.DataFrame(records)
    print(f"\nTotal observations: {len(df_all):,}")
    print(f"Tickers covered: {df_all['Ticker'].nunique()}")
    print(f"Date range: {df_all['Date'].min()} to {df_all['Date'].max()}")
    return df_all

def stats_by_bins(df, col, bins, labels, title):
    """Calculate win rate and avg return by bins."""
    df['Bin'] = pd.cut(df[col], bins=bins, labels=labels, include_lowest=True)
    stats = df.groupby('Bin').agg(
        Count=('OvernightReturn', 'count'),
        WinRate=('OvernightReturn', lambda x: (x > 0).mean() * 100),
        AvgReturn=('OvernightReturn', 'mean'),
        MedianReturn=('OvernightReturn', 'median'),
        StdReturn=('OvernightReturn', 'std'),
        AvgAbsDay=('AbsChange', 'mean'),
    ).round(2)
    stats['Sharpe'] = (stats['AvgReturn'] / stats['StdReturn']).round(2)
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(stats.to_string())
    return stats

def plot_overnight_distribution(df, save_path='chart_01_distribution.png'):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Distribution of overnight returns
    ax = axes[0, 0]
    data = df['OvernightReturn'].dropna()
    ax.hist(data, bins=200, range=(-5, 5), color='steelblue', edgecolor='white', alpha=0.7)
    ax.axvline(data.mean(), color='red', linestyle='--', label=f'Mean: {data.mean():.3f}%')
    ax.axvline(data.median(), color='orange', linestyle='--', label=f'Median: {data.median():.3f}%')
    ax.axvline(0, color='black', linewidth=0.5)
    ax.set_xlabel('Overnight Return (%)')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Overnight Returns (Close → Next Open)')
    ax.legend()
    ax.set_xlim(-5, 5)
    
    # 2. Win rate by direction of day
    ax = axes[0, 1]
    dir_stats = df.groupby('Direction').agg(
        WinRate=('OvernightReturn', lambda x: (x > 0).mean() * 100),
        AvgReturn=('OvernightReturn', 'mean'),
        Count=('OvernightReturn', 'count')
    ).reset_index()
    colors = ['#ff4757' if d == 'Down' else '#00ff88' if d == 'Up' else '#8899aa' for d in dir_stats['Direction']]
    bars = ax.bar(dir_stats['Direction'], dir_stats['WinRate'], color=colors, edgecolor='white')
    ax.axhline(50, color='black', linestyle='--', alpha=0.5)
    ax.set_ylabel('Win Rate (%)')
    ax.set_title('Overnight Win Rate by Day Direction')
    for bar, avg in zip(bars, dir_stats['AvgReturn']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{avg:.2f}%\n(n={dir_stats.iloc[bars.index(bar)]["Count"]:,})',
                ha='center', fontsize=9)
    ax.set_ylim(0, 80)
    
    # 3. Overnight return vs Day Change%
    ax = axes[1, 0]
    sample = df.sample(min(5000, len(df)))
    ax.scatter(sample['ChangePct'], sample['OvernightReturn'], alpha=0.3, s=5, color='steelblue')
    z = np.polyfit(sample['ChangePct'].dropna(), sample['OvernightReturn'].dropna(), 1)
    p = np.poly1d(z)
    x_line = np.linspace(sample['ChangePct'].min(), sample['ChangePct'].max(), 100)
    ax.plot(x_line, p(x_line), color='red', linewidth=2, label=f'Trend (slope={z[0]:.3f})')
    ax.axhline(0, color='black', linewidth=0.5)
    ax.axvline(0, color='black', linewidth=0.5)
    ax.set_xlabel('Day Change (%)')
    ax.set_ylabel('Overnight Return (%)')
    ax.set_title('Day Change vs Overnight Return')
    ax.legend()
    ax.set_xlim(-10, 10)
    ax.set_ylim(-5, 5)
    
    # 4. Overnight return by day of week
    ax = axes[1, 1]
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    dow_stats = df.groupby('DayOfWeek').agg(
        WinRate=('OvernightReturn', lambda x: (x > 0).mean() * 100),
        AvgReturn=('OvernightReturn', 'mean'),
        Count=('OvernightReturn', 'count')
    ).reindex([d for d in dow_order if d in df['DayOfWeek'].values])
    colors = ['#00d4ff'] * len(dow_stats)
    bars = ax.bar(dow_stats.index, dow_stats['WinRate'], color=colors, edgecolor='white')
    ax.axhline(50, color='black', linestyle='--', alpha=0.5)
    ax.set_ylabel('Win Rate (%)')
    ax.set_title('Win Rate by Day of Week (Buy at Close → Sell Next Open)')
    for bar, avg, cnt in zip(bars, dow_stats['AvgReturn'], dow_stats['Count']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{avg:.2f}%\n(n={cnt:,})', ha='center', fontsize=9)
    ax.set_ylim(0, 80)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def plot_feature_analysis(df, save_path='chart_02_features.png'):
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    
    # 1. Overnight return by 20D Range bins
    ax = axes[0, 0]
    bins = [0, 10, 30, 50, 70, 90, 100]
    labels = ['0-10%', '10-30%', '30-50%', '50-70%', '70-90%', '90-100%']
    stats = stats_by_bins(df, '20D_Range', bins, labels, 'Overnight Return by 20D Position')
    colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(labels)))
    bars = ax.bar(range(len(labels)), stats['WinRate'], color=colors, edgecolor='white')
    ax.axhline(50, color='black', linestyle='--', alpha=0.5)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30)
    ax.set_ylabel('Win Rate (%)')
    ax.set_title('Win Rate by Position in 20D Range')
    for bar, avg, cnt in zip(bars, stats['AvgReturn'], stats['Count']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{avg:.2f}%\n(n={cnt:,})', ha='center', fontsize=8)
    ax.set_ylim(0, 80)
    
    # 2. Overnight return by Vol Ratio bins
    ax = axes[0, 1]
    bins = [0, 0.5, 1.0, 1.5, 2.0, 3.0, 10.0]
    labels = ['<0.5x', '0.5-1x', '1-1.5x', '1.5-2x', '2-3x', '>3x']
    stats = stats_by_bins(df, 'VolRatio', bins, labels, 'Overnight Return by Volume Ratio')
    colors = plt.cm.Oranges(np.linspace(0.3, 0.9, len(labels)))
    bars = ax.bar(range(len(labels)), stats['WinRate'], color=colors, edgecolor='white')
    ax.axhline(50, color='black', linestyle='--', alpha=0.5)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30)
    ax.set_ylabel('Win Rate (%)')
    ax.set_title('Win Rate by Volume Ratio (vs 20D Avg)')
    for bar, avg, cnt in zip(bars, stats['AvgReturn'], stats['Count']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{avg:.2f}%\n(n={cnt:,})', ha='center', fontsize=8)
    ax.set_ylim(0, 80)
    
    # 3. Overnight return by Abs Change bins
    ax = axes[0, 2]
    bins = [0, 1, 2, 3, 5, 10, 50]
    labels = ['<1%', '1-2%', '2-3%', '3-5%', '5-10%', '>10%']
    stats = stats_by_bins(df, 'AbsChange', bins, labels, 'Overnight Return by |Day Change|')
    colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(labels)))
    bars = ax.bar(range(len(labels)), stats['WinRate'], color=colors, edgecolor='white')
    ax.axhline(50, color='black', linestyle='--', alpha=0.5)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30)
    ax.set_ylabel('Win Rate (%)')
    ax.set_title('Win Rate by Magnitude of Day Change')
    for bar, avg, cnt in zip(bars, stats['AvgReturn'], stats['Count']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{avg:.2f}%\n(n={cnt:,})', ha='center', fontsize=8)
    ax.set_ylim(0, 80)
    
    # 4. Cumulative returns by different filters
    ax = axes[1, 0]
    # Simulate strategy: buy all days vs filtered
    df_sorted = df.sort_values('Date')
    
    # Strategy 1: Buy every day
    cum_all = (1 + df_sorted['OvernightReturn']/100).cumprod()
    
    # Strategy 2: Only days with |Change| > 2%
    mask_big = df_sorted['AbsChange'] > 2
    cum_big = (1 + df_sorted.loc[mask_big, 'OvernightReturn']/100).cumprod()
    
    # Strategy 3: Only days with 20D_Range > 80% (near highs)
    mask_high = df_sorted['20D_Range'] > 80
    cum_high = (1 + df_sorted.loc[mask_high, 'OvernightReturn']/100).cumprod()
    
    # Strategy 4: Only days with VolRatio > 1.5
    mask_vol = df_sorted['VolRatio'] > 1.5
    cum_vol = (1 + df_sorted.loc[mask_vol, 'OvernightReturn']/100).cumprod()
    
    ax.plot(cum_all.values, label=f'All days ({len(df_sorted):,} trades)', linewidth=2, alpha=0.8)
    ax.plot(cum_big.values, label=f'|Change|>2% ({mask_big.sum():,} trades)', linewidth=2)
    ax.plot(cum_high.values, label=f'20D Range>80% ({mask_high.sum():,} trades)', linewidth=2)
    ax.plot(cum_vol.values, label=f'VolRatio>1.5x ({mask_vol.sum():,} trades)', linewidth=2)
    ax.axhline(1, color='black', linewidth=0.5)
    ax.set_xlabel('Trade Number')
    ax.set_ylabel('Cumulative Return (Multiple)')
    ax.set_title('Cumulative Returns by Strategy Filter')
    ax.legend(loc='upper left', fontsize=9)
    ax.set_yscale('log')
    
    # 5. Heatmap: Win rate by 20D Range × VolRatio
    ax = axes[1, 1]
    df['RangeBin'] = pd.cut(df['20D_Range'], bins=[0, 25, 50, 75, 100], labels=['0-25%', '25-50%', '50-75%', '75-100%'])
    df['VolBin'] = pd.cut(df['VolRatio'], bins=[0, 0.8, 1.2, 2.0, 10], labels=['<0.8x', '0.8-1.2x', '1.2-2x', '>2x'])
    heat = df.groupby(['RangeBin', 'VolBin'])['OvernightReturn'].apply(lambda x: (x > 0).mean() * 100).unstack()
    sns.heatmap(heat, annot=True, fmt='.1f', cmap='RdYlGn', center=50, vmin=40, vmax=60, ax=ax, cbar_kws={'label': 'Win Rate %'})
    ax.set_title('Win Rate Heatmap: 20D Range vs Vol Ratio')
    ax.set_xlabel('Volume Ratio')
    ax.set_ylabel('20D Range Position')
    
    # 6. Top sectors performance
    ax = axes[1, 2]
    # We don't have sector in df_all, so skip or use a placeholder
    # Instead: overnight return by month
    df['Month'] = df['Date'].dt.month_name()
    month_order = ['January','February','March','April','May','June','July','August','September','October','November','December']
    month_stats = df.groupby('Month').agg(
        WinRate=('OvernightReturn', lambda x: (x > 0).mean() * 100),
        AvgReturn=('OvernightReturn', 'mean')
    ).reindex([m for m in month_order if m in df['Month'].values])
    colors = plt.cm.Blues(np.linspace(0.3, 0.9, len(month_stats)))
    bars = ax.bar(range(len(month_stats)), month_stats['WinRate'], color=colors, edgecolor='white')
    ax.axhline(50, color='black', linestyle='--', alpha=0.5)
    ax.set_xticks(range(len(month_stats)))
    ax.set_xticklabels(month_stats.index, rotation=45, ha='right')
    ax.set_ylabel('Win Rate (%)')
    ax.set_title('Win Rate by Month (Seasonality)')
    for bar, avg in zip(bars, month_stats['AvgReturn']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{avg:.2f}%', ha='center', fontsize=8)
    ax.set_ylim(0, 80)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def plot_extended_analysis(df, save_path='chart_03_extended.png'):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Mean Reversion vs Momentum
    ax = axes[0, 0]
    # Days where stock was up >2% — does it gap up or down next day?
    up_days = df[df['ChangePct'] > 2]
    down_days = df[df['ChangePct'] < -2]
    
    ax.hist(up_days['OvernightReturn'].dropna(), bins=100, range=(-5, 5), alpha=0.6, label=f'After +2% day (n={len(up_days):,})', color='green')
    ax.hist(down_days['OvernightReturn'].dropna(), bins=100, range=(-5, 5), alpha=0.6, label=f'After -2% day (n={len(down_days):,})', color='red')
    ax.axvline(up_days['OvernightReturn'].mean(), color='darkgreen', linestyle='--', linewidth=2, label=f'Mean after +2%: {up_days["OvernightReturn"].mean():.3f}%')
    ax.axvline(down_days['OvernightReturn'].mean(), color='darkred', linestyle='--', linewidth=2, label=f'Mean after -2%: {down_days["OvernightReturn"].mean():.3f}%')
    ax.axvline(0, color='black', linewidth=0.5)
    ax.set_xlabel('Overnight Return (%)')
    ax.set_ylabel('Frequency')
    ax.set_title('Mean Reversion Test: Overnight After Big Day')
    ax.legend(fontsize=8)
    ax.set_xlim(-5, 5)
    
    # 2. Volatility clustering
    ax = axes[0, 1]
    df['OvernightAbs'] = df['OvernightReturn'].abs()
    rolling_vol = df.groupby('Ticker')['OvernightAbs'].rolling(20).mean().reset_index(0, drop=True)
    df['AvgOvernightVol20'] = rolling_vol
    df['VolSpike'] = df['OvernightAbs'] / df['AvgOvernightVol20']
    
    high_vol_days = df[df['VolSpike'] > 2]
    normal_days = df[df['VolSpike'] <= 1]
    
    ax.hist(normal_days['OvernightReturn'].dropna(), bins=100, range=(-5, 5), alpha=0.5, label=f'Normal vol (n={len(normal_days):,})', color='steelblue')
    ax.hist(high_vol_days['OvernightReturn'].dropna(), bins=100, range=(-5, 5), alpha=0.7, label=f'High vol spike (n={len(high_vol_days):,})', color='orange')
    ax.axvline(normal_days['OvernightReturn'].mean(), color='blue', linestyle='--', label=f'Normal mean: {normal_days["OvernightReturn"].mean():.3f}%')
    ax.axvline(high_vol_days['OvernightReturn'].mean(), color='darkorange', linestyle='--', label=f'High vol mean: {high_vol_days["OvernightReturn"].mean():.3f}%')
    ax.axvline(0, color='black', linewidth=0.5)
    ax.set_xlabel('Overnight Return (%)')
    ax.set_ylabel('Frequency')
    ax.set_title('Volatility Clustering: High vs Normal Overnight Vol')
    ax.legend(fontsize=8)
    ax.set_xlim(-5, 5)
    
    # 3. Gap size distribution
    ax = axes[1, 0]
    gaps = df['OvernightReturn'].dropna()
    gap_bins = [-10, -2, -1, -0.5, 0, 0.5, 1, 2, 10]
    gap_labels = ['<-2%', '-2 to -1%', '-1 to -0.5%', '-0.5 to 0%', '0 to 0.5%', '0.5 to 1%', '1 to 2%', '>2%']
    df['GapBin'] = pd.cut(gaps, bins=gap_bins, labels=gap_labels, include_lowest=True)
    gap_counts = df['GapBin'].value_counts().reindex(gap_labels)
    colors = ['#ff4757']*4 + ['#00ff88']*4
    bars = ax.bar(range(len(gap_labels)), gap_counts.values, color=colors, edgecolor='white')
    ax.set_xticks(range(len(gap_labels)))
    ax.set_xticklabels(gap_labels, rotation=45, ha='right')
    ax.set_ylabel('Count')
    ax.set_title('Distribution of Overnight Gap Sizes')
    for bar, cnt in zip(bars, gap_counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
                f'{cnt:,}\n({cnt/len(gaps)*100:.1f}%)', ha='center', fontsize=8)
    
    # 4. Best vs Worst performers (tickers with most consistent overnight gaps)
    ax = axes[1, 1]
    ticker_stats = df.groupby('Ticker').agg(
        WinRate=('OvernightReturn', lambda x: (x > 0).mean() * 100),
        AvgReturn=('OvernightReturn', 'mean'),
        Count=('OvernightReturn', 'count'),
        Std=('OvernightReturn', 'std')
    )
    ticker_stats = ticker_stats[ticker_stats['Count'] >= 100]  # Minimum sample
    ticker_stats['Sharpe'] = ticker_stats['AvgReturn'] / ticker_stats['Std']
    
    top10 = ticker_stats.nlargest(10, 'Sharpe')
    bottom10 = ticker_stats.nsmallest(10, 'Sharpe')
    
    y_pos = np.arange(10)
    ax.barh(y_pos, top10['Sharpe'].values, color='#00ff88', alpha=0.8, label='Top 10 Sharpe')
    ax.barh(y_pos + 12, bottom10['Sharpe'].values, color='#ff4757', alpha=0.8, label='Bottom 10 Sharpe')
    
    ax.set_yticks(list(y_pos) + list(y_pos + 12))
    ax.set_yticklabels(list(top10.index) + list(bottom10.index), fontsize=8)
    ax.axvline(0, color='black', linewidth=0.5)
    ax.set_xlabel('Sharpe Ratio (Avg/Std)')
    ax.set_title('Best vs Worst Tickers for Overnight Strategy')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def main():
    print("="*60)
    print("OVERNIGHT GAP STRATEGY BACKTEST")
    print("Strategy: Buy at Close → Sell at Next Open")
    print("="*60)
    
    tickers = fetch_sp500()
    print(f"\nTotal tickers to fetch: {len(tickers)}")
    
    all_data = batch_download(tickers, period='1y')
    print(f"Successfully downloaded: {len(all_data)} tickers")
    
    df_all = analyze_strategy(all_data)
    
    # Overall stats
    print(f"\n{'='*60}")
    print("OVERALL STATISTICS")
    print(f"{'='*60}")
    print(f"Mean overnight return: {df_all['OvernightReturn'].mean():.4f}%")
    print(f"Median overnight return: {df_all['OvernightReturn'].median():.4f}%")
    print(f"Std overnight return: {df_all['OvernightReturn'].std():.4f}%")
    print(f"Win rate (positive): {(df_all['OvernightReturn'] > 0).mean()*100:.2f}%")
    print(f"Sharpe (daily): {df_all['OvernightReturn'].mean() / df_all['OvernightReturn'].std():.4f}")
    
    # Annualized
    daily_mean = df_all['OvernightReturn'].mean() / 100
    daily_std = df_all['OvernightReturn'].std() / 100
    ann_return = daily_mean * 252
    ann_vol = daily_std * np.sqrt(252)
    ann_sharpe = ann_return / ann_vol if ann_vol > 0 else 0
    print(f"\nAnnualized return (252 trades): {ann_return*100:.2f}%")
    print(f"Annualized volatility: {ann_vol*100:.2f}%")
    print(f"Annualized Sharpe: {ann_sharpe:.4f}")
    
    # Max drawdown simulation
    df_sorted = df_all.sort_values('Date')
    cumulative = (1 + df_sorted['OvernightReturn']/100).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    print(f"Max drawdown: {drawdown.min()*100:.2f}%")
    
    # Plots
    print(f"\n{'='*60}")
    print("GENERATING CHARTS...")
    print(f"{'='*60}")
    plot_overnight_distribution(df_all)
    plot_feature_analysis(df_all)
    plot_extended_analysis(df_all)
    
    # Save summary CSV
    summary_file = 'backtest_summary.csv'
    df_all.to_csv(summary_file, index=False)
    print(f"\nSaved raw data: {summary_file} ({len(df_all):,} rows)")
    
    # JSON summary for quick reading
    summary = {
        'total_observations': int(len(df_all)),
        'tickers_covered': int(df_all['Ticker'].nunique()),
        'date_range': f"{df_all['Date'].min()} to {df_all['Date'].max()}",
        'mean_overnight_return': round(float(df_all['OvernightReturn'].mean()), 4),
        'median_overnight_return': round(float(df_all['OvernightReturn'].median()), 4),
        'win_rate': round(float((df_all['OvernightReturn'] > 0).mean() * 100), 2),
        'annualized_return': round(float(ann_return * 100), 2),
        'annualized_sharpe': round(float(ann_sharpe), 4),
        'max_drawdown': round(float(drawdown.min() * 100), 2),
        'after_big_up_day_mean': round(float(df_all[df_all['ChangePct'] > 2]['OvernightReturn'].mean()), 4),
        'after_big_down_day_mean': round(float(df_all[df_all['ChangePct'] < -2]['OvernightReturn'].mean()), 4),
    }
    with open('backtest_summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print("Saved summary: backtest_summary.json")
    
    print(f"\n{'='*60}")
    print("BACKTEST COMPLETE")
    print(f"{'='*60}")
    print("Charts generated:")
    print("  - chart_01_distribution.png")
    print("  - chart_02_features.png")
    print("  - chart_03_extended.png")

if __name__ == '__main__':
    main()

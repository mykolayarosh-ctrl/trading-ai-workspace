import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 10
sns.set_style('darkgrid')

df = pd.read_csv('backtest/backtest_summary.csv')
df['Date'] = pd.to_datetime(df['Date'])
df['OvernightWin'] = df['OvernightReturn'] > 0

# ===== Chart 1: Win Rate by Filter Combinations =====
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 1a. Single filters
ax = axes[0, 0]
single_data = [
    ('Baseline\n(All Days)', 52.05, 44582, '#999999'),
    ('20D Range <10%', 57.28, 4370, '#00ff88'),
    ('Change < -3%', 56.68, 2396, '#00ff88'),
    ('Vol Ratio >3x', 56.65, 316, '#00ff88'),
    ('Change < -2%', 56.22, 4991, '#00ff88'),
    ('Tuesday', 55.45, 9264, '#ffaa00'),
    ('20D Range <20%', 55.00, 8535, '#ffaa00'),
]
names, wins, counts, colors = zip(*single_data)
bars = ax.barh(range(len(names)), wins, color=colors, edgecolor='white', height=0.6)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names)
ax.axvline(50, color='black', linestyle='--', alpha=0.5)
ax.axvline(60, color='green', linestyle='--', alpha=0.3)
ax.set_xlabel('Win Rate (%)')
ax.set_title('Single Filters vs Baseline')
for i, (bar, cnt) in enumerate(zip(bars, counts)):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, 
            f'{bar.get_width():.1f}% (n={cnt:,})', va='center', fontsize=9)
ax.set_xlim(40, 65)

# 1b. Two-filter combos (top 10)
ax = axes[0, 1]
combo_data = [
    ('Chg<-2% + Tuesday', 64.98, 1005, '#00ff88'),
    ('|Chg|>3% + Tuesday', 64.53, 1094, '#00ff88'),
    ('20D<10% + Friday', 62.69, 973, '#00ff88'),
    ('|Chg|>2% + Tuesday', 62.38, 2185, '#00ff88'),
    ('Chg>2% + Tuesday', 60.17, 1180, '#ffaa00'),
    ('20D<30% + Vol>2x', 60.16, 502, '#ffaa00'),
    ('5D>5% + Tuesday', 59.63, 1122, '#ffaa00'),
    ('5D<-5% + Tuesday', 58.91, 791, '#ffaa00'),
    ('20D<10% + Chg<-2%', 58.49, 1561, '#ffaa00'),
    ('20D<10% + |Chg|>2%', 58.33, 1596, '#ffaa00'),
]
names, wins, counts, colors = zip(*combo_data)
bars = ax.barh(range(len(names)), wins, color=colors, edgecolor='white', height=0.6)
ax.set_yticks(range(len(names)))
ax.set_yticklabels([n.replace(' + ', '\n+ ') for n in names], fontsize=9)
ax.axvline(50, color='black', linestyle='--', alpha=0.5)
ax.axvline(60, color='green', linestyle='--', alpha=0.3)
ax.axvline(65, color='green', linestyle='-', alpha=0.5)
ax.set_xlabel('Win Rate (%)')
ax.set_title('Two-Filter Combinations (Top 10)')
for i, (bar, cnt) in enumerate(zip(bars, counts)):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, 
            f'{bar.get_width():.1f}% (n={cnt:,})', va='center', fontsize=8)
ax.set_xlim(50, 70)

# 1c. Three-filter combos (top 10)
ax = axes[1, 0]
triple_data = [
    ('|Chg|>2% + Chg<-3%\n+ Tuesday', 67.90, 486, '#00d4ff'),
    ('20D<20% + Chg<-3%\n+ Tuesday', 67.13, 216, '#00d4ff'),
    ('Chg<-3% + 5D<-5%\n+ Tuesday', 66.82, 214, '#00d4ff'),
    ('|Chg|>3% + 5D<-5%\n+ Tuesday', 66.38, 235, '#00d4ff'),
    ('20D<20% + |Chg|>3%\n+ Tuesday', 66.13, 248, '#00d4ff'),
    ('20D<10% + Chg<-2%\n+ Tuesday', 66.02, 259, '#00d4ff'),
    ('20D<10% + |Chg|>2%\n+ Tuesday', 65.91, 264, '#00d4ff'),
    ('20D<10% + Chg<-2%\n+ Friday', 65.67, 367, '#00ff88'),
    ('20D<30% + Chg<-3%\n+ Tuesday', 65.46, 249, '#00ff88'),
    ('20D<10% + |Chg|>2%\n+ Friday', 65.08, 378, '#00ff88'),
]
names, wins, counts, colors = zip(*triple_data)
bars = ax.barh(range(len(names)), wins, color=colors, edgecolor='white', height=0.6)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=9)
ax.axvline(50, color='black', linestyle='--', alpha=0.5)
ax.axvline(65, color='green', linestyle='-', alpha=0.5)
ax.axvline(70, color='green', linestyle='-', alpha=0.7)
ax.set_xlabel('Win Rate (%)')
ax.set_title('Three-Filter Combinations (Top 10) — TARGET: 65%+')
for i, (bar, cnt) in enumerate(zip(bars, counts)):
    ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2, 
            f'{bar.get_width():.1f}% (n={cnt:,})', va='center', fontsize=8)
ax.set_xlim(55, 72)

# 1d. Win rate by day of week + magnitude
ax = axes[1, 1]
dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
dow_bigdown = []
dow_all = []
for dow in dow_order:
    mask_all = df['DayOfWeek'] == dow
    mask_bigdown = mask_all & (df['ChangePct'] < -2)
    dow_all.append(df.loc[mask_all, 'OvernightWin'].mean() * 100)
    dow_bigdown.append(df.loc[mask_bigdown, 'OvernightWin'].mean() * 100 if mask_bigdown.sum() > 0 else 0)

x = np.arange(len(dow_order))
width = 0.35
bars1 = ax.bar(x - width/2, dow_all, width, label='All days', color='steelblue', edgecolor='white')
bars2 = ax.bar(x + width/2, dow_bigdown, width, label='After -2% day', color='#ff4757', edgecolor='white')
ax.axhline(50, color='black', linestyle='--', alpha=0.5)
ax.axhline(60, color='green', linestyle='--', alpha=0.3)
ax.set_xticks(x)
ax.set_xticklabels(dow_order)
ax.set_ylabel('Win Rate (%)')
ax.set_title('Win Rate by Day of Week\n(All Days vs After Big Down Day)')
ax.legend()
for bar in bars2:
    if bar.get_height() > 0:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{bar.get_height():.1f}%', ha='center', fontsize=9, color='#ff4757', fontweight='bold')
ax.set_ylim(40, 70)

plt.tight_layout()
plt.savefig('backtest/chart_04_filter_combos.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved: chart_04_filter_combos.png')

# ===== Chart 2: Heatmap of best strategies =====
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# 2a. 20D Range vs Day of Week
ax = axes[0]
df['RangeBin'] = pd.cut(df['20D_Range'], bins=[0, 15, 30, 50, 70, 85, 100], 
                         labels=['0-15%', '15-30%', '30-50%', '50-70%', '70-85%', '85-100%'])
heat1 = df.groupby(['RangeBin', 'DayOfWeek'])['OvernightWin'].mean().unstack() * 100
heat1 = heat1.reindex(columns=dow_order)
sns.heatmap(heat1, annot=True, fmt='.1f', cmap='RdYlGn', center=52, vmin=45, vmax=65, 
            ax=ax, cbar_kws={'label': 'Win Rate %'})
ax.set_title('Win Rate Heatmap: 20D Range vs Day of Week')
ax.set_xlabel('Day of Week')
ax.set_ylabel('Position in 20D Range')

# 2b. Change% vs VolRatio
ax = axes[1]
df['ChgBin'] = pd.cut(df['ChangePct'], bins=[-50, -5, -3, -2, -1, 0, 1, 2, 3, 5, 50],
                       labels=['<-5%', '-5 to -3%', '-3 to -2%', '-2 to -1%', '-1 to 0%',
                               '0 to 1%', '1 to 2%', '2 to 3%', '3 to 5%', '>5%'])
df['VolBin'] = pd.cut(df['VolRatio'], bins=[0, 0.8, 1.0, 1.5, 2.5, 10],
                       labels=['<0.8x', '0.8-1x', '1-1.5x', '1.5-2.5x', '>2.5x'])
heat2 = df.groupby(['ChgBin', 'VolBin'])['OvernightWin'].mean().unstack() * 100
sns.heatmap(heat2, annot=True, fmt='.1f', cmap='RdYlGn', center=52, vmin=40, vmax=70,
            ax=ax, cbar_kws={'label': 'Win Rate %'})
ax.set_title('Win Rate Heatmap: Day Change vs Volume Ratio')
ax.set_xlabel('Volume Ratio vs 20D Avg')
ax.set_ylabel('Day Change %')
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

plt.tight_layout()
plt.savefig('backtest/chart_05_heatmaps.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved: chart_05_heatmaps.png')

# ===== Chart 3: Practical Strategy Card =====
fig, ax = plt.subplots(figsize=(12, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

# Title
ax.text(5, 11.5, 'OVERNIGHT GAP STRATEGY', fontsize=24, ha='center', fontweight='bold', color='#0a0e1a')
ax.text(5, 11.0, 'Close → Next Open | S&P 500 Backtest (1 Year, 44,582 Trades)', 
        fontsize=12, ha='center', color='#555555')

# Baseline box
rect1 = Rectangle((0.5, 9.5), 4, 1.2, facecolor='#eeeeee', edgecolor='#999999', linewidth=2)
ax.add_patch(rect1)
ax.text(2.5, 10.4, 'BASELINE', fontsize=14, ha='center', fontweight='bold', color='#666666')
ax.text(2.5, 10.0, 'Buy every day at Close', fontsize=11, ha='center', color='#666666')
ax.text(2.5, 9.7, 'Win Rate: 52.1% | Avg: +0.05%', fontsize=10, ha='center', color='#888888')

# Tier 1 box
rect2 = Rectangle((5.5, 9.5), 4, 1.2, facecolor='#d4edda', edgecolor='#28a745', linewidth=2)
ax.add_patch(rect2)
ax.text(7.5, 10.4, 'TIER 1 (Simple)', fontsize=14, ha='center', fontweight='bold', color='#155724')
ax.text(7.5, 10.0, '20D Range < 10% (near lows)', fontsize=11, ha='center', color='#155724')
ax.text(7.5, 9.7, 'Win Rate: 57.3% | Avg: +0.16% | n=4,370', fontsize=10, ha='center', color='#28a745')

# Tier 2 box
rect3 = Rectangle((0.5, 7.8), 4, 1.5, facecolor='#fff3cd', edgecolor='#ffc107', linewidth=2)
ax.add_patch(rect3)
ax.text(2.5, 9.0, 'TIER 2 (Two Filters)', fontsize=14, ha='center', fontweight='bold', color='#856404')
ax.text(2.5, 8.6, 'Change < -2% + Tuesday', fontsize=11, ha='center', color='#856404')
ax.text(2.5, 8.3, 'Win Rate: 65.0% | Avg: +0.43% | n=1,005', fontsize=10, ha='center', color='#856404')
ax.text(2.5, 8.0, 'OR: |Change| > 3% + Tuesday', fontsize=10, ha='center', color='#856404')

# Tier 3 box
rect4 = Rectangle((5.5, 7.8), 4, 1.5, facecolor='#cce5ff', edgecolor='#007bff', linewidth=3)
ax.add_patch(rect4)
ax.text(7.5, 9.0, 'TIER 3 (Three Filters)', fontsize=14, ha='center', fontweight='bold', color='#004085')
ax.text(7.5, 8.6, '|Change| > 3% + Change < -3%', fontsize=11, ha='center', color='#004085')
ax.text(7.5, 8.3, '+ Tuesday', fontsize=11, ha='center', color='#004085')
ax.text(7.5, 8.0, 'Win Rate: 67.9% | Avg: +0.52% | n=486', fontsize=11, ha='center', color='#007bff', fontweight='bold')

# Key insight
ax.text(5, 7.2, 'KEY INSIGHT: Mean Reversion + Tuesday Effect', fontsize=14, ha='center', 
        fontweight='bold', color='#0a0e1a')
ax.text(5, 6.7, 'After big down days (>2-3%), stocks tend to bounce overnight — especially on Tuesdays.', 
        fontsize=11, ha='center', color='#333333')

# Best tickers
ax.text(5, 6.0, 'BEST TICKERS FOR OVERNIGHT (Win Rate > 60%)', fontsize=13, ha='center', 
        fontweight='bold', color='#0a0e1a')
tickers_text = 'VALE (62.8%) | MPLX (61.9%) | KMI (61.5%) | RTX (61.0%) | WMB (61.0%) | BA (61.0%) | CAT (60.2%)'
ax.text(5, 5.6, tickers_text, fontsize=10, ha='center', color='#555555')

# Warning
ax.text(5, 5.0, '⚠️  IMPORTANT: This is Close → 9:30 AM Open, not 4:00 AM pre-market.', 
        fontsize=11, ha='center', color='#ff4757', fontweight='bold')
ax.text(5, 4.6, 'For true 4 AM data, paid API needed (Polygon.io ~$49/mo).', 
        fontsize=10, ha='center', color='#888888')

# Practical filter
ax.text(5, 3.8, 'RECOMMENDED FILTER FOR SCREENER', fontsize=13, ha='center', 
        fontweight='bold', color='#0a0e1a')
rect5 = Rectangle((1, 2.8), 8, 0.8, facecolor='#f8f9fa', edgecolor='#333333', linewidth=1)
ax.add_patch(rect5)
ax.text(5, 3.3, '20D Range < 30% AND (ChangePct < -2% OR VolRatio > 2x)', 
        fontsize=12, ha='center', color='#333333', fontfamily='monospace')
ax.text(5, 3.0, 'Expected Win Rate: ~58-62% | Trades per month: ~40-60', 
        fontsize=10, ha='center', color='#666666')

plt.tight_layout()
plt.savefig('backtest/chart_06_strategy_card.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Saved: chart_06_strategy_card.png')

print('\nAll charts generated!')

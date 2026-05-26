#!/usr/bin/env python3
"""
Multi-Agent Orchestrator for Overnight Strategy Research.

Agents:
1. DataFetcher — downloads market data + adds indicators
2. Backtester — tests Close→Open and Close→FirstHour strategies
3. StrategyFinder — finds best indicator combinations
4. HypothesisGenerator — proposes new patterns to test
5. TraderAdvisor — summarizes actionable signals
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from intraday_backtest import batch_backtest, analyze_by_indicators, find_best_combinations
import pandas as pd

# Sample tickers for proof of concept (expand to 1000 later)
TEST_TICKERS = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","NFLX","AMD","QCOM",
    "JPM","BAC","GS","MS","BLK","C","WFC","USB","PNC","TFC",
    "XOM","CVX","COP","OXY","SLB","MPC","VLO","PSX","MRO","DVN",
    "JNJ","PFE","UNH","ABBV","LLY","MRK","TMO","ABT","DHR","BMY",
    "WMT","COST","HD","LOW","TGT","NKE","SBUX","MCD","YUM","CMG",
    "DIS","NFLX","CMCSA","T","VZ","TMUS","META","GOOGL","SNAP","PINS",
    "BA","LMT","RTX","NOC","GD","HII","LHX","TXT","TDG","TDY",
    "CAT","DE","AGCO","PCAR","OSK","F","GM","STLA","LCID","RIVN",
    "NEE","DUK","SO","AEP","EXC","SRE","WEC","ES","ETR","CNP",
    "ENPH","SEDG","FSLR","RUN","NOVA","SPWR","BE","QS","LAZR","NKLA",
]

def run_agents():
    print("="*70)
    print("MULTI-AGENT OVERNIGHT STRATEGY RESEARCH")
    print("="*70)
    print()
    print("Agent 1: DataFetcher — Downloading hourly data + indicators...")
    print(f"Testing {len(TEST_TICKERS)} tickers...")
    
    results = batch_backtest(TEST_TICKERS, period='60d', max_tickers=100)
    
    if results is None or len(results) == 0:
        print("ERROR: No data retrieved. Check internet/yfinance.")
        return
    
    print(f"\n✅ Agent 1 complete: {len(results):,} observations across {results['Ticker'].nunique()} tickers")
    
    print("\n" + "="*70)
    print("Agent 2: Backtester — Baseline statistics")
    print("="*70)
    baseline_wr = (results['OvernightReturn'] > 0).mean() * 100
    baseline_avg = results['OvernightReturn'].mean()
    print(f"Baseline (all days, all tickers): WinRate={baseline_wr:.2f}%, AvgReturn={baseline_avg:.4f}%")
    print(f"Total observations: {len(results):,}")
    
    print("\n" + "="*70)
    print("Agent 3: StrategyFinder — Finding best indicator filters...")
    print("="*70)
    
    indicator_stats = analyze_by_indicators(results)
    combos = find_best_combinations(results, min_trades=30)
    
    print("\n" + "="*70)
    print("Agent 4: HypothesisGenerator — New patterns to test")
    print("="*70)
    
    # Propose hypotheses based on findings
    hypotheses = []
    
    # Check top combos
    top5 = [c for c in combos if c[4] == 'double' and c[2] > 55][:5]
    for name, n, wr, avg, _ in top5:
        hypotheses.append(f"H1: {name} → WinRate={wr:.1f}% (n={n})")
    
    # Check RSI extremes
    rsi_low = results[results['RSI'] < 30]
    if len(rsi_low) > 30:
        wr = (rsi_low['OvernightReturn'] > 0).mean() * 100
        hypotheses.append(f"H2: RSI<30 (oversold) → WinRate={wr:.1f}% (n={len(rsi_low)})")
    
    rsi_high = results[results['RSI'] > 70]
    if len(rsi_high) > 30:
        wr = (rsi_high['OvernightReturn'] > 0).mean() * 100
        hypotheses.append(f"H3: RSI>70 (overbought) → WinRate={wr:.1f}% (n={len(rsi_high)})")
    
    # BB extremes
    bb_low = results[results['BB_Position'] < 10]
    if len(bb_low) > 30:
        wr = (bb_low['OvernightReturn'] > 0).mean() * 100
        hypotheses.append(f"H4: BB_Position<10% (below lower band) → WinRate={wr:.1f}% (n={len(bb_low)})")
    
    bb_high = results[results['BB_Position'] > 90]
    if len(bb_high) > 30:
        wr = (bb_high['OvernightReturn'] > 0).mean() * 100
        hypotheses.append(f"H5: BB_Position>90% (above upper band) → WinRate={wr:.1f}% (n={len(bb_high)})")
    
    # Volatility
    high_vol = results[results['ATR_Pct'] > 5]
    if len(high_vol) > 30:
        wr = (high_vol['OvernightReturn'] > 0).mean() * 100
        hypotheses.append(f"H6: ATR>5% (high volatility) → WinRate={wr:.1f}% (n={len(high_vol)})")
    
    for h in hypotheses:
        print(f"  📌 {h}")
    
    print("\n" + "="*70)
    print("Agent 5: TraderAdvisor — Actionable Summary")
    print("="*70)
    
    # Find today's signals (if we have data)
    latest = results.sort_values('Date').groupby('Ticker').last().reset_index()
    
    # Score each ticker
    def score_ticker(row):
        score = 0
        if pd.notna(row['RSI']) and row['RSI'] < 35:
            score += 2  # Oversold
        if pd.notna(row['BB_Position']) and row['BB_Position'] < 15:
            score += 2  # Below lower band
        if pd.notna(row['MACD_Hist']) and row['MACD_Hist'] < -0.1:
            score += 1  # Bearish momentum
        if pd.notna(row['ATR_Pct']) and row['ATR_Pct'] > 3:
            score += 1  # Volatile
        return score
    
    latest['SignalScore'] = latest.apply(score_ticker, axis=1)
    
    # Filter only those with some signal
    signals = latest[latest['SignalScore'] >= 2].sort_values('SignalScore', ascending=False)
    
    print(f"\n📊 Today's top signals (score >= 2):")
    print(f"{'Ticker':<8} {'Score':>6} {'RSI':>6} {'BB%':>6} {'ATR%':>6} {'MACD_H':>8} {'Close':>10}")
    print("-"*60)
    for _, row in signals.head(20).iterrows():
        rsi = f"{row['RSI']:.1f}" if pd.notna(row['RSI']) else "N/A"
        bb = f"{row['BB_Position']:.1f}" if pd.notna(row['BB_Position']) else "N/A"
        atr = f"{row['ATR_Pct']:.2f}" if pd.notna(row['ATR_Pct']) else "N/A"
        macd = f"{row['MACD_Hist']:.3f}" if pd.notna(row['MACD_Hist']) else "N/A"
        print(f"{row['Ticker']:<8} {row['SignalScore']:>6} {rsi:>6} {bb:>6} {atr:>6} {macd:>8} ${row['ClosePrice']:>8.2f}")
    
    # Save results
    results.to_csv('backtest_results.csv', index=False)
    print(f"\n💾 Saved detailed results to: backtest_results.csv")
    
    # Save summary
    summary = {
        'total_observations': int(len(results)),
        'tickers_tested': int(results['Ticker'].nunique()),
        'baseline_win_rate': round(float(baseline_wr), 2),
        'baseline_avg_return': round(float(baseline_avg), 4),
        'top_hypotheses': hypotheses[:5],
        'top_signals': signals.head(10)[['Ticker','SignalScore','RSI','BB_Position','ATR_Pct','MACD_Hist']].to_dict('records')
    }
    import json
    with open('research_summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print("💾 Saved summary to: research_summary.json")
    
    print("\n" + "="*70)
    print("ALL AGENTS COMPLETE")
    print("="*70)

if __name__ == '__main__':
    run_agents()

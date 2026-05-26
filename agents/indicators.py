"""
Technical indicators for overnight strategy filtering.
"""
import numpy as np
import pandas as pd

def add_rsi(df, period=14):
    """Relative Strength Index — oversold < 30, overbought > 70."""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def add_atr(df, period=14):
    """Average True Range — volatility measure."""
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=period).mean()
    df['ATR_Pct'] = (df['ATR'] / df['Close']) * 100
    return df

def add_bollinger(df, period=20, std_dev=2):
    """Bollinger Bands — price position relative to bands."""
    df['BB_Middle'] = df['Close'].rolling(window=period).mean()
    bb_std = df['Close'].rolling(window=period).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * std_dev)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * std_dev)
    df['BB_Position'] = ((df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])) * 100
    df['BB_Width'] = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']) * 100
    return df

def add_macd(df, fast=12, slow=26, signal=9):
    """MACD — momentum indicator."""
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = ema_fast - ema_slow
    df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    return df

def add_vwap(df):
    """VWAP — Volume Weighted Average Price (intraday only)."""
    typical = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (typical * df['Volume']).cumsum() / df['Volume'].cumsum()
    df['VWAP_Dist'] = ((df['Close'] - df['VWAP']) / df['VWAP']) * 100
    return df

def add_all_indicators(df):
    """Add all indicators to a DataFrame."""
    df = add_rsi(df)
    df = add_atr(df)
    df = add_bollinger(df)
    df = add_macd(df)
    return df

def indicator_snapshot(df):
    """Get latest values of all indicators."""
    if len(df) < 30:
        return None
    last = df.iloc[-1]
    return {
        'RSI': round(last['RSI'], 2) if pd.notna(last['RSI']) else None,
        'ATR_Pct': round(last['ATR_Pct'], 3) if pd.notna(last['ATR_Pct']) else None,
        'BB_Position': round(last['BB_Position'], 2) if pd.notna(last['BB_Position']) else None,
        'BB_Width': round(last['BB_Width'], 2) if pd.notna(last['BB_Width']) else None,
        'MACD': round(last['MACD'], 4) if pd.notna(last['MACD']) else None,
        'MACD_Hist': round(last['MACD_Hist'], 4) if pd.notna(last['MACD_Hist']) else None,
        'MACD_Signal': round(last['MACD_Signal'], 4) if pd.notna(last['MACD_Signal']) else None,
    }

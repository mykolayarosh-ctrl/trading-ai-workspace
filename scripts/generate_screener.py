#!/usr/bin/env python3
"""Generate stock screener HTML with data from Yahoo Finance."""
import json, sys, os, datetime, time
from urllib.request import urlopen, Request
from urllib.error import HTTPError

def fetch_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        import pandas as pd
        tables = pd.read_html(url)
        return tables[0]['Symbol'].tolist()
    except Exception:
        # Fallback
        return []

def fetch_nasdaq100_tickers():
    url = "https://en.wikipedia.org/wiki/NASDAQ-100"
    try:
        import pandas as pd
        tables = pd.read_html(url)
        for t in tables:
            if 'Ticker' in t.columns:
                return t['Ticker'].tolist()
            if 'Symbol' in t.columns:
                return t['Symbol'].tolist()
        return []
    except Exception:
        return []

def yf_ticker_info(ticker):
    """Fetch basic info for a ticker via yfinance rapidapi-style or direct."""
    # Using yfinance direct — we try to use the library if available
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="20d", interval="1d")
        if hist.empty:
            return None
        return {
            'ticker': ticker,
            'name': info.get('longName', info.get('shortName', ticker)),
            'price': hist['Close'].iloc[-1],
            'prev_close': hist['Close'].iloc[-2] if len(hist) > 1 else hist['Close'].iloc[-1],
            'volume': hist['Volume'].iloc[-1],
            'avg_volume': hist['Volume'].mean(),
            'market_cap': info.get('marketCap', 0),
            'sector': info.get('sector', 'N/A'),
            'high_20d': hist['High'].max(),
            'low_20d': hist['Low'].min(),
            'hist': hist,
        }
    except Exception as e:
        return None

def compute_score(d):
    price = d['price']
    prev = d['prev_close']
    change_pct = ((price - prev) / prev) * 100 if prev else 0
    
    high = d['high_20d']
    low = d['low_20d']
    range_20d = ((price - low) / (high - low)) * 100 if high != low else 50
    
    # 5 day change
    hist = d['hist']
    if len(hist) >= 5:
        chg_5d = ((price - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) * 100
    else:
        chg_5d = change_pct
    
    vol_ratio = d['volume'] / d['avg_volume'] if d['avg_volume'] else 1
    
    # Score formula matching the original
    score = (abs(change_pct) * 2) + (chg_5d * 0.5) + (range_20d * 0.3) + (min(vol_ratio, 5) * 3)
    
    # Gap probability estimate
    gap_prob = min(100, (abs(change_pct) * 3) + (range_20d * 0.4) + (min(vol_ratio, 3) * 10))
    
    ah_signal = "🔥" if vol_ratio > 2 and abs(change_pct) > 2 else "—"
    
    return {
        'change_pct': change_pct,
        'range_20d': range_20d,
        'chg_5d': chg_5d,
        'vol_ratio': vol_ratio,
        'score': score,
        'gap_prob': gap_prob,
        'ah_signal': ah_signal,
    }

def format_number(n):
    if n >= 1e12:
        return f"${n/1e12:.1f}T"
    if n >= 1e9:
        return f"${n/1e9:.1f}B"
    if n >= 1e6:
        return f"${n/1e6:.1f}M"
    return f"${n:.1f}"

def generate_html(stocks):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    header = open("stock_screener_header.html").read()
    
    # Add sortable headers and script
    sort_script = '''
    <script>
    (function() {
        let sortDir = {};
        function parseVal(text, type) {
            text = text.trim();
            if (type === 'num') return parseFloat(text.replace(/[^0-9.\\-]/g, '')) || 0;
            if (type === 'money') return parseFloat(text.replace(/[$,]/g, '')) || 0;
            if (type === 'pct') return parseFloat(text.replace(/[%+,]/g, '')) || 0;
            if (type === 'vol') return parseFloat(text.replace(/,/g, '')) || 0;
            if (type === 'ratio') return parseFloat(text.replace(/x/g, '')) || 0;
            if (type === 'cap') {
                let val = parseFloat(text.replace(/[$,]/g, '')) || 0;
                if (text.includes('T')) val *= 1000;
                return val;
            }
            return text.toLowerCase();
        }
        window.sortTable = function(n) {
            const table = document.querySelector('table tbody');
            const headers = document.querySelectorAll('table thead th');
            const type = headers[n].getAttribute('data-sort') || 'text';
            const rows = Array.from(table.rows);
            const dir = sortDir[n] === 'asc' ? 'desc' : 'asc';
            sortDir = {}; sortDir[n] = dir;
            headers.forEach(h => h.classList.remove('sort-asc','sort-desc'));
            headers[n].classList.add(dir === 'asc' ? 'sort-asc' : 'sort-desc');
            rows.sort((a, b) => {
                let av = a.cells[n] ? a.cells[n].textContent : '';
                let bv = b.cells[n] ? b.cells[n].textContent : '';
                av = parseVal(av, type); bv = parseVal(bv, type);
                if (typeof av === 'number' && typeof bv === 'number') {
                    return dir === 'asc' ? av - bv : bv - av;
                }
                return dir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
            });
            rows.forEach(r => table.appendChild(r));
        };
    })();
    </script>
'''
    
    # Replace static headers with sortable ones
    old_headers = '''<th>#</th>
                <th>Ticker</th>
                <th>Price</th>
                <th>Change</th>
                <th>Score</th>
                <th>Gap Prob</th>
                <th>AH Signal</th>
                <th>Volume</th>
                <th>Vol Ratio</th>
                <th>20D Range</th>
                <th>5D Chg</th>
                <th>Mkt Cap</th>
                <th>Sector</th>'''
    
    new_headers = '''<th data-sort="num" onclick="sortTable(0)">#</th>
                <th data-sort="text" onclick="sortTable(1)">Ticker</th>
                <th data-sort="money" onclick="sortTable(2)">Price</th>
                <th data-sort="pct" onclick="sortTable(3)">Change</th>
                <th data-sort="num" onclick="sortTable(4)">Score</th>
                <th data-sort="pct" onclick="sortTable(5)">Gap Prob</th>
                <th data-sort="text" onclick="sortTable(6)">AH Signal</th>
                <th data-sort="vol" onclick="sortTable(7)">Volume</th>
                <th data-sort="ratio" onclick="sortTable(8)">Vol Ratio</th>
                <th data-sort="pct" onclick="sortTable(9)">20D Range</th>
                <th data-sort="pct" onclick="sortTable(10)">5D Chg</th>
                <th data-sort="cap" onclick="sortTable(11)">Mkt Cap</th>
                <th data-sort="text" onclick="sortTable(12)">Sector</th>'''
    
    header = header.replace(old_headers, new_headers)
    header = header.replace("{last_update}", now).replace("{count}", str(len(stocks)))
    
    # Add sort styles
    sort_styles = '''        th {
            cursor: pointer;
            user-select: none;
        }
        th.sort-asc::after { content: ' ▲'; font-size: 10px; color: #00d4ff; }
        th.sort-desc::after { content: ' ▼'; font-size: 10px; color: #00d4ff; }
'''
    header = header.replace("        tr:hover { background: #111a2a; }", "        tr:hover { background: #111a2a; }\n" + sort_styles)
    
    rows_html = []
    for i, s in enumerate(stocks, 1):
        change_class = "positive" if s['change_pct'] >= 0 else "negative"
        change_sign = "+" if s['change_pct'] >= 0 else ""
        chg5d_class = "positive" if s['chg_5d'] >= 0 else "negative"
        chg5d_sign = "+" if s['chg_5d'] >= 0 else ""
        
        score_class = "score-high" if s['score'] >= 20 else ("score-mid" if s['score'] >= 10 else "score-low")
        gap_class = "gap-high" if s['gap_prob'] >= 70 else ("gap-mid" if s['gap_prob'] >= 40 else "gap-low")
        highlight = ' class="highlight"' if s['score'] >= 20 else ''
        
        row = f'''            <tr{highlight}>
                <td>{i}</td>
                <td>
                    <span class="ticker">{s['ticker']}</span>
                    <br><span class="name">{s['name']}</span>
                </td>
                <td>${s['price']:.2f}</td>
                <td class="{change_class}">{change_sign}{s['change_pct']:.2f}%</td>
                <td class="score {score_class}">{s['score']:.1f}</td>
                <td class="gap-prob {gap_class}">{s['gap_prob']:.1f}%</td>
                <td>{s['ah_signal']}</td>
                <td>{s['volume']:,.0f}</td>
                <td>{s['vol_ratio']:.2f}x</td>
                <td>{s['range_20d']:.1f}%</td>
                <td class="{chg5d_class}">{chg5d_sign}{s['chg_5d']:.2f}%</td>
                <td>{format_number(s['market_cap'])}</td>
                <td class="sector">{s['sector']}</td>
            </tr>'''
        rows_html.append(row)
    
    footer = '''        </tbody>
    </table>
''' + sort_script + '''
</body>
</html>'''
    
    return header + "\n".join(rows_html) + "\n" + footer

def main():
    print("Fetching tickers...")
    sp500 = fetch_sp500_tickers()
    nasdaq = fetch_nasdaq100_tickers()
    tickers = list(dict.fromkeys(sp500 + nasdaq))
    
    if not tickers:
        # Hard fallback
        tickers = ["AAPL","MSFT","GOOGL","AMZN","TSLA","META","NVDA","NFLX","AMD","QCOM",
                   "INTC","CRM","ADBE","PYPL","UBER","ABNB","COIN","PLTR","SNOW","ZM",
                   "ROKU","SQ","SHOP","CRWD","NET","DDOG","FSLY","DOCU","OKTA","TWLO"]
    
    print(f"Processing {len(tickers)} tickers...")
    stocks = []
    
    for ticker in tickers:
        d = yf_ticker_info(ticker)
        if not d:
            continue
        # Filters
        if d['price'] < 10:
            continue
        if d['volume'] < 500_000:
            continue
        if d['market_cap'] < 2_000_000_000:
            continue
        
        metrics = compute_score(d)
        stocks.append({**d, **metrics})
        time.sleep(0.05)  # Rate limit
    
    # Sort by score desc
    stocks.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"Passed filters: {len(stocks)} stocks")
    
    html = generate_html(stocks)
    with open("stock_screener.html", "w") as f:
        f.write(html)
    print("Written stock_screener.html")

if __name__ == "__main__":
    main()

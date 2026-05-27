#!/usr/bin/env python3
"""Generate stock screener HTML with data from Yahoo Finance."""
import json, sys, os, datetime, time
from urllib.request import urlopen, Request
from urllib.error import HTTPError

def fetch_spy_data():
    """Fetch SPY daily change (Open→Close) for market context.
    
    KEY DISCOVERY: Inverse relation!
    - SPY Daily < -2% → 77% WR (buy the dip, mean reversion overnight)
    - SPY Daily > +1% → 31% WR (profit taking, avoid)
    """
    try:
        import yfinance as yf
        spy = yf.Ticker('SPY')
        hist = spy.history(period='5d', interval='1d')
        if len(hist) < 1:
            return None
        
        # Get today's daily change (Open → Close) — KNOWN at close
        last_open = hist['Open'].iloc[-1]
        last_close = hist['Close'].iloc[-1]
        daily_change = (last_close / last_open - 1) * 100
        
        # Signal based on research (inverse relation!)
        if daily_change < -2:
            signal = 'STRONG_DOWN'
            signal_text = f'SPY Daily -{abs(daily_change):.2f}% → 77% WR 🔥 BUY THE DIP'
            rec = '✅ STRONG BUY — Market oversold, high probability of overnight bounce'
        elif daily_change < -1:
            signal = 'DOWN'
            signal_text = f'SPY Daily -{abs(daily_change):.2f}% → 63% WR 🔥 Bounce likely'
            rec = '✅ BUY — Market weak, mean reversion expected overnight'
        elif daily_change < -0.5:
            signal = 'SLIGHT_DOWN'
            signal_text = f'SPY Daily -{abs(daily_change):.2f}% → 61% WR ⭐ Mild bounce'
            rec = '✅ BUY — Slight weakness, mild overnight bounce expected'
        elif daily_change > 2:
            signal = 'STRONG_UP'
            signal_text = f'SPY Daily +{daily_change:.2f}% → 31% WR ❌ AVOID'
            rec = '❌ AVOID — Strong day = profit taking overnight, high drop risk'
        elif daily_change > 1:
            signal = 'UP'
            signal_text = f'SPY Daily +{daily_change:.2f}% → 32% WR ⚠️ Caution'
            rec = '⚠️ REDUCE SIZE — Strong green day, overnight pullback likely'
        else:
            signal = 'NEUTRAL'
            signal_text = f'SPY Daily {daily_change:+.2f}% → ~52% WR'
            rec = '➡️ NEUTRAL — No strong edge from market context'
        
        return {
            'change_pct': daily_change,
            'signal': signal,
            'signal_text': signal_text,
            'recommendation': rec,
            'last_close': last_close
        }
    except Exception as e:
        print(f'  SPY fetch error: {e}')
        return None


def fetch_sp500_tickers():
    """Fetch S&P 500 tickers from Wikipedia CSV mirror."""
    urls = [
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv",
    ]
    for url in urls:
        try:
            if url.endswith('.csv'):
                import pandas as pd
                df = pd.read_csv(url)
                return df['Symbol'].tolist()
            else:
                import pandas as pd
                tables = pd.read_html(url)
                return tables[0]['Symbol'].tolist()
        except Exception:
            continue
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

# Extended large-cap + growth fallback — covers most liquid stocks
_EXTENDED_FALLBACK = [
    # Mag7 + mega tech
    "AAPL","MSFT","GOOGL","GOOG","AMZN","TSLA","META","NVDA","NFLX","AMD",
    "INTC","QCOM","CRM","ADBE","PYPL","UBER","ABNB","COIN","PLTR","SNOW",
    "ZM","ROKU","SQ","SHOP","CRWD","NET","DDOG","FSLY","DOCU","OKTA","TWLO",
    # S&P 500 large cap (partial, most liquid)
    "ABBV","ABT","ACN","ADP","AIG","ALL","AMAT","AMGN","AMP","AMT","AMGN",
    "ANET","ANTM","AON","APA","APD","APH","APO","ARE","ATO","AVB","AVGO",
    "AXP","AZO","BA","BAC","BAX","BDX","BEN","BG","BIIB","BIO","BK",
    "BKNG","BLK","BMY","BR","BSX","BURL","BX","C","CAG","CAH","CARR",
    "CAT","CB","CBOE","CBRE","CCI","CCL","CDNS","CDW","CE","CF","CFG",
    "CHD","CHRW","CHTR","CI","CINF","CL","CLX","CMA","CMCSA","CME","CMG",
    "CMI","CMS","CNC","CNP","COF","COO","COP","COST","CPB","CPRT","CPT",
    "CRL","CSGP","CSX","CTAS","CTLT","CTRA","CVS","CVX","D","DAL","DD",
    "DE","DFS","DG","DGX","DHI","DHR","DIS","DLR","DOV","DOW","DPZ",
    "DRI","DTE","DUK","DVA","DVN","EA","EBAY","ECL","ED","EFX","EIX",
    "EL","ELV","EMN","EMR","EOG","EPAM","EQR","EQT","ES","ESS","ETN",
    "ETR","EWC","EW","EXC","EXPD","EXPE","EXR","F","FANG","FAST","FCX",
    "FDX","FE","FICO","FIS","FI","FISV","FLT","FMC","FRT","FTNT","FTV",
    "GD","GE","GEHC","GILD","GIS","GL","GLW","GM","GPC","GPN","GRMN",
    "GS","GWW","HAL","HAS","HBAN","HCA","HD","HES","HIG","HII","HLT",
    "HOLX","HON","HPE","HPQ","HRL","HSIC","HST","HSY","HUM","HWM","IBM",
    "ICE","IDXX","IEX","IFF","ILMN","INCY","INTU","IP","IPG","IQV","IR",
    "IRM","ISRG","IT","ITW","IVZ","JCI","JKHY","JNJ","JNPR","JPM","K",
    "KDP","KEY","KEYS","KHC","KIM","KLAC","KMB","KMI","KMX","KO","KR",
    "L","LDOS","LEN","LH","LHX","LIN","LKQ","LLY","LMT","LNT","LOW",
    "LRCX","LUV","LVS","LW","LYB","LYV","MA","MAA","MAR","MAS","MCD",
    "MCHP","MCK","MCO","MDLZ","MDT","MET","META","MGM","MHK","MKC","MKTX",
    "MLM","MMC","MMM","MNST","MO","MOH","MOS","MPC","MPWR","MRK","MRNA",
    "MRO","MS","MSCI","MSFT","MSI","MTB","MTCH","MTD","MU","NCLH","NDAQ",
    "NEE","NEM","NI","NKE","NOC","NOW","NRG","NSC","NTAP","NTRS","NUE",
    "NVR","NWS","NWSA","O","ODFL","OKE","OMC","ON","ORCL","ORLY","OXY",
    "PANW","PARA","PAYC","PAYX","PCAR","PEAK","PEG","PENN","PEP","PFE",
    "PFG","PG","PGR","PH","PHM","PKG","PLD","PM","PNC","PNR","PNW",
    "POOL","PPG","PPL","PRU","PSA","PSX","PTC","PWR","PXD","RCL","REG",
    "REGN","RF","RHI","RJF","RL","RMD","ROK","ROL","ROP","ROST","RSG",
    "RTX","RVTY","SBAC","SBNY","SBUX","SCHW","SEE","SHW","SJM","SNA","SNPS",
    "SO","SPG","SPGI","SRE","STE","STLD","STT","STX","STZ","SWK","SWKS",
    "SYF","SYK","SYY","T","TAP","TDG","TDY","TECH","TEL","TER","TFC",
    "TFX","TGT","TJX","TMO","TMUS","TPR","TRGP","TRMB","TROW","TRV","TSCO",
    "TT","TTWO","TXN","TXT","TYL","UAL","UDR","UHS","ULTA","UNH","UNP",
    "UPS","URI","USB","V","VFC","VLO","VMC","VNO","VRSK","VRSN","VRTX",
    "VTR","VTRS","VZ","WAB","WAT","WBA","WBD","WDC","WEC","WELL","WFC",
    "WMB","WM","WMT","WRK","WST","WTW","WY","WYNN","XEL","XOM","XRAY",
    "XYL","YUM","ZBH","ZBRA","ZION","ZTS","CEG","VST","CRGY","GEV",
    # Additional popular mid/growth
    "RIVN","LCID","DDOG","MDB","SNOW","NET","OKTA","DDOG","CFLT","S",
    "DOCN","ASAN","RBLX","U","PATH","AI","SOUN","ARM","SMCI","DJT",
    "HOOD","SOFI","AFRM","RBLX","GTLB","WOLF","ENPH","SEDG","FSLR","RUN",
    "ARRY","NOVA","SPWR","BE","QS","LAZR","FSR","NKLA","GOEV","FFIE",
    "JOBY","ACHR","LILM","EH",
]


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
    
    # Tier classification based on backtest (Close → Open win rates)
    # With SPY Signal context
    tier = ""
    tier_class = ""
    tier_desc = ""
    spy_context = ""
    
    # Check conditions
    strong_down = abs(change_pct) > 3 and change_pct < 0
    moderate_down = change_pct < -2
    near_low = range_20d < 10
    high_vol = vol_ratio > 3
    strong_up = change_pct > 2
    
    # Base tier assignment
    if strong_down:
        tier = "T3"
        tier_class = "tier-3"
        tier_desc = "Strong down >3% — 67.9% WR"
    elif moderate_down:
        tier = "T2" 
        tier_class = "tier-2"
        tier_desc = "Down >2% — 65% WR"
    elif strong_up:
        tier = "T2+"
        tier_class = "tier-2"
        tier_desc = "Up >2% momentum — 63.4% WR"
    elif near_low or high_vol:
        tier = "T1"
        tier_class = "tier-1"
        if near_low:
            tier_desc = "Near 20D low — 57.3% WR"
        else:
            tier_desc = "High volume >3x — 56.4% WR"
    else:
        tier = ""
        tier_class = ""
        tier_desc = ""
    
    ah_signal = "🔥" if vol_ratio > 2 and abs(change_pct) > 2 else "—"
    
    return {
        'change_pct': change_pct,
        'range_20d': range_20d,
        'chg_5d': chg_5d,
        'vol_ratio': vol_ratio,
        'score': score,
        'gap_prob': gap_prob,
        'ah_signal': ah_signal,
        'tier': tier,
        'tier_class': tier_class,
        'tier_desc': tier_desc,
    }

def format_number(n):
    if n >= 1e12:
        return f"${n/1e12:.1f}T"
    if n >= 1e9:
        return f"${n/1e9:.1f}B"
    if n >= 1e6:
        return f"${n/1e6:.1f}M"
    return f"${n:.1f}"

def generate_html(stocks, spy_data=None):
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
                <th data-sort="text" onclick="sortTable(5)">Tier</th>
                <th data-sort="pct" onclick="sortTable(6)">Gap Prob</th>
                <th data-sort="text" onclick="sortTable(7)">AH Signal</th>
                <th data-sort="vol" onclick="sortTable(8)">Volume</th>
                <th data-sort="ratio" onclick="sortTable(9)">Vol Ratio</th>
                <th data-sort="pct" onclick="sortTable(10)">20D Range</th>
                <th data-sort="pct" onclick="sortTable(11)">5D Chg</th>
                <th data-sort="cap" onclick="sortTable(12)">Mkt Cap</th>
                <th data-sort="text" onclick="sortTable(13)">Sector</th>'''
    
    header = header.replace(old_headers, new_headers)
    header = header.replace("{last_update}", now).replace("{count}", str(len(stocks)))
    
    # Replace SPY placeholders
    if spy_data:
        header = header.replace("{spy_signal}", spy_data.get('signal_text', 'N/A'))
        header = header.replace("{spy_change}", f"{spy_data.get('change_pct', 0):.2f}%")
        if spy_data.get('signal') in ['STRONG_UP', 'UP']:
            rec = '✅ GO — Market supports overnight gaps'
        elif spy_data.get('signal') == 'STRONG_DOWN':
            rec = '❌ STOP — High probability of overnight drop'
        else:
            rec = '⚠️ CAUTION — Market weak, reduce size'
        header = header.replace("{spy_rec}", rec)
    else:
        header = header.replace("{spy_signal}", "SPY data unavailable")
        header = header.replace("{spy_change}", "N/A")
        header = header.replace("{spy_rec}", "Check SPY manually")
    
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
                <td class="tier-cell">
                    <span class="tier-badge {s['tier_class']}">{s['tier']}</span>
                    <br><span style="font-size:9px;color:#8899aa">{s['tier_desc']}</span>
                </td>
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
        tickers = _EXTENDED_FALLBACK
    
    # Fetch SPY data for market context
    print("Fetching SPY market data...")
    spy_data = fetch_spy_data()
    if spy_data:
        print(f"  SPY: {spy_data['signal_text']}")
    else:
        print("  Warning: Could not fetch SPY data")
    
    print(f"Processing {len(tickers)} tickers...")
    stocks = []
    
    # Batch download for speed
    import yfinance as yf
    batch_size = 100
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        print(f"  Batch {i//batch_size + 1}/{(len(tickers)-1)//batch_size + 1}: {len(batch)} tickers")
        try:
            data = yf.download(batch, period="25d", interval="1d", group_by='ticker',
                             auto_adjust=True, prepost=False, threads=True, progress=False)
            if data.empty:
                continue
            
            for ticker in batch:
                try:
                    if len(batch) == 1:
                        ticker_data = data
                    else:
                        if ticker not in data.columns.get_level_values(0):
                            continue
                        ticker_data = data[ticker]
                    
                    if ticker_data.empty or len(ticker_data) < 2:
                        continue
                    
                    close = ticker_data['Close']
                    volume = ticker_data['Volume']
                    if close.isna().all() or volume.isna().all():
                        continue
                    
                    price = float(close.iloc[-1])
                    prev = float(close.iloc[-2])
                    vol = float(volume.iloc[-1])
                    avg_vol = float(volume.mean())
                    high_20d = float(ticker_data['High'].max())
                    low_20d = float(ticker_data['Low'].min())
                    
                    # Try to get info for market cap and sector
                    market_cap = 0
                    sector = "N/A"
                    name = ticker
                    try:
                        t_info = yf.Ticker(ticker)
                        info = t_info.info
                        market_cap = info.get('marketCap', 0)
                        sector = info.get('sector', 'N/A')
                        name = info.get('longName', info.get('shortName', ticker))
                    except Exception:
                        pass
                    
                    if price < 10 or vol < 500_000 or market_cap < 2_000_000_000:
                        continue
                    
                    d = {
                        'ticker': ticker, 'name': name, 'price': price,
                        'prev_close': prev, 'volume': vol, 'avg_volume': avg_vol,
                        'market_cap': market_cap, 'sector': sector,
                        'high_20d': high_20d, 'low_20d': low_20d,
                        'hist': ticker_data,
                    }
                    metrics = compute_score(d)
                    stocks.append({**d, **metrics})
                    
                except Exception as e:
                    continue
        except Exception as e:
            print(f"  Batch error: {e}")
            continue
        
        time.sleep(0.5)  # Rate limit between batches
    
    # Sequential fallback for any tickers that failed in batch
    processed = {s['ticker'] for s in stocks}
    for ticker in tickers:
        if ticker in processed:
            continue
        try:
            d = yf_ticker_info(ticker)
            if d and d['price'] >= 10 and d['volume'] >= 500_000 and d['market_cap'] >= 2_000_000_000:
                metrics = compute_score(d)
                stocks.append({**d, **metrics})
        except Exception:
            continue
        time.sleep(0.05)
    
    # Sort by score desc
    stocks.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"Passed filters: {len(stocks)} stocks")
    
    html = generate_html(stocks, spy_data)
    with open("stock_screener.html", "w") as f:
        f.write(html)
    print("Written stock_screener.html")

if __name__ == "__main__":
    main()

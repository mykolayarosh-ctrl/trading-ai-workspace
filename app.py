from flask import Flask, send_file, render_template_string, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    """Show stock screener"""
    if os.path.exists('stock_screener.html'):
        return send_file('stock_screener.html')
    else:
        return render_template_string('''
        <html>
        <head><title>Stock Screener</title></head>
        <body>
            <h1>Stock Screener</h1>
            <p>Data is being generated. Please wait a few minutes.</p>
            <p>Last updated: Never</p>
        </body>
        </html>
        ''')

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'data_exists': os.path.exists('stock_screener.html')
    })

@app.route('/api/refresh')
def refresh():
    """Trigger manual refresh (runs generate_screener.py)"""
    try:
        os.system('python3 scripts/generate_screener.py')
        return jsonify({'status': 'success', 'message': 'Data refreshed'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

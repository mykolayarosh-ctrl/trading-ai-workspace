from flask import Flask, send_file, render_template_string, jsonify
import os
import subprocess
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

@app.route('/api/refresh', methods=['POST', 'GET'])
def refresh():
    """Trigger manual refresh (runs generate_screener.py)"""
    try:
        result = subprocess.run(
            ['python3', 'scripts/generate_screener.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        if result.returncode == 0:
            return jsonify({
                'status': 'success', 
                'message': 'Screener updated successfully',
                'output': result.stdout[-500:] if result.stdout else '',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Generation failed',
                'error': result.stderr[-500:] if result.stderr else 'Unknown error'
            }), 500
    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'Generation timed out (5 minutes)'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/status')
def status():
    """Get current data status"""
    try:
        if os.path.exists('stock_screener.html'):
            mtime = os.path.getmtime('stock_screener.html')
            return jsonify({
                'data_exists': True,
                'last_updated': datetime.fromtimestamp(mtime).isoformat(),
                'file_size': os.path.getsize('stock_screener.html')
            })
        else:
            return jsonify({
                'data_exists': False,
                'last_updated': None
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

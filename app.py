from flask import Flask, send_file, render_template_string, jsonify
import os
import subprocess
import threading
import json
from datetime import datetime

app = Flask(__name__)
refresh_process = None
refresh_start_time = None
refresh_status = {'running': False, 'last_result': None, 'last_output': ''}

def run_refresh_in_background():
    global refresh_process, refresh_start_time, refresh_status
    refresh_status['running'] = True
    refresh_status['last_result'] = None
    refresh_status['last_output'] = ''
    refresh_start_time = datetime.now().isoformat()
    
    try:
        proc = subprocess.Popen(
            ['python3', 'scripts/generate_screener.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        refresh_process = proc
        stdout, stderr = proc.communicate(timeout=600)  # 10 min max
        
        refresh_status['last_output'] = (stdout + '\n' + stderr)[-1000:]
        if proc.returncode == 0:
            refresh_status['last_result'] = 'success'
        else:
            refresh_status['last_result'] = 'error: ' + stderr[-500:]
    except subprocess.TimeoutExpired:
        proc.kill()
        refresh_status['last_result'] = 'timeout (10 min)'
    except Exception as e:
        refresh_status['last_result'] = f'exception: {str(e)}'
    finally:
        refresh_status['running'] = False
        refresh_process = None

@app.route('/')
def index():
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
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'data_exists': os.path.exists('stock_screener.html')
    })

@app.route('/api/refresh', methods=['POST', 'GET'])
def refresh():
    global refresh_process, refresh_status
    # If refresh is running, kill it and start new
    if refresh_status['running'] and refresh_process:
        try:
            refresh_process.kill()
        except:
            pass
        refresh_status['running'] = False
    
    thread = threading.Thread(target=run_refresh_in_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'started',
        'message': 'Refresh started in background. Check /api/refresh/status for progress.'
    })

@app.route('/api/refresh/status')
def refresh_status_endpoint():
    global refresh_status
    return jsonify({
        'running': refresh_status['running'],
        'last_result': refresh_status['last_result'],
        'started': refresh_start_time,
        'last_output': refresh_status['last_output'][-500:] if refresh_status['last_output'] else ''
    })

@app.route('/api/status')
def status():
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

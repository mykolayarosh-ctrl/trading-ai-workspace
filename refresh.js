    function refreshPage() {
        const btn = document.querySelector('.refresh-btn');
        const msg = document.getElementById('refresh-msg');
        
        btn.disabled = true;
        btn.textContent = '🔄 Starting...';
        msg.style.display = 'none';
        
        fetch('/api/refresh', { method: 'POST' })
            .then(response => {
                if (!response.ok) {
                    throw new Error('API not available');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'started' || data.status === 'running') {
                    btn.textContent = '🔄 Updating...';
                    msg.textContent = 'Fetching data from Yahoo Finance (~2-5 min)...';
                    msg.style.display = 'block';
                    pollRefreshStatus();
                } else {
                    btn.textContent = '❌ Error';
                    msg.textContent = 'Unexpected: ' + JSON.stringify(data);
                    msg.style.display = 'block';
                    btn.disabled = false;
                }
            })
            .catch(error => {
                // Fallback: API not available (GitHub Pages), just reload
                btn.textContent = '🔄 Reloading...';
                window.location.href = window.location.pathname + '?t=' + Date.now();
            });
    }
    
    function pollRefreshStatus() {
        const btn = document.querySelector('.refresh-btn');
        const msg = document.getElementById('refresh-msg');
        
        fetch('/api/refresh/status')
            .then(r => {
                if (!r.ok) throw new Error('API unavailable');
                return r.json();
            })
            .then(data => {
                if (data.running) {
                    msg.textContent = 'Fetching data... (started ' + data.started + ')';
                    setTimeout(pollRefreshStatus, 5000);
                } else if (data.last_result === 'success') {
                    btn.textContent = '✅ Updated!';
                    msg.textContent = 'Data refreshed! Reloading...';
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    btn.textContent = '❌ Error';
                    msg.textContent = 'Refresh failed: ' + (data.last_result || 'Unknown error');
                    msg.style.display = 'block';
                    btn.disabled = false;
                }
            })
            .catch(error => {
                // Fallback on error
                btn.textContent = '❌ Failed';
                msg.textContent = 'Network error: ' + error.message;
                msg.style.display = 'block';
                btn.disabled = false;
            });
    }
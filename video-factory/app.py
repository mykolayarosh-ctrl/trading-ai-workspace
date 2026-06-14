from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
import json
import threading
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from video_generator import VideoFactory

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Global state
video_jobs = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_video():
    data = request.json or {}
    
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    tone = data.get('tone', 'educational')
    duration = data.get('duration', 'medium')
    language = data.get('language', 'uk')
    custom_script = data.get('custom_script', '').strip()
    
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def run_job():
        try:
            factory = VideoFactory(
                output_dir="output",
                temp_dir=f"temp/{job_id}"
            )
            
            if custom_script:
                # Parse custom script
                try:
                    script = json.loads(custom_script)
                except:
                    # Simple text format: each line is a scene
                    lines = custom_script.split('\n')
                    lines = [l.strip() for l in lines if l.strip()]
                    scenes = []
                    for line in lines:
                        scenes.append({
                            'narration': line,
                            'visual': line.split('.')[0] if '.' in line else line,
                            'duration': 10
                        })
                    script = {'title': topic, 'scenes': scenes}
            else:
                script = factory.generate_script(topic, tone, duration, language)
            
            video_jobs[job_id]['status'] = 'generating'
            video_jobs[job_id]['progress'] = 'Generating script...'
            
            # Build video
            output_path = factory.build_video(script, title=topic)
            
            if output_path and os.path.exists(output_path):
                video_jobs[job_id]['status'] = 'complete'
                video_jobs[job_id]['output_path'] = output_path
                video_jobs[job_id]['progress'] = 'Done!'
            else:
                video_jobs[job_id]['status'] = 'error'
                video_jobs[job_id]['progress'] = 'Failed to generate video'
            
            factory.cleanup()
            
        except Exception as e:
            video_jobs[job_id]['status'] = 'error'
            video_jobs[job_id]['progress'] = str(e)
    
    video_jobs[job_id] = {
        'status': 'starting',
        'progress': 'Initializing...',
        'created_at': datetime.now().isoformat()
    }
    
    thread = threading.Thread(target=run_job)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'status': 'started',
        'message': 'Video generation started'
    })

@app.route('/api/status/<job_id>')
def job_status(job_id):
    job = video_jobs.get(job_id, {})
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)

@app.route('/api/download/<job_id>')
def download_video(job_id):
    job = video_jobs.get(job_id, {})
    if job.get('status') == 'complete' and 'output_path' in job:
        return send_file(job['output_path'], as_attachment=True)
    return jsonify({'error': 'Video not ready'}), 404

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'video-factory'})

if __name__ == '__main__':
    os.makedirs('output', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

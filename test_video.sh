cd /root/.openclaw/workspace/video-factory && source venv/bin/activate && python -c "
from video_generator import VideoFactory
import os

f = VideoFactory()
script = f.generate_script('Space Exploration', 'educational', 'short', 'en')
print('Building video...')
print('Scenes:', len(script['scenes']))

try:
    output = f.build_video(script, title='Space Exploration')
    if output and os.path.exists(output):
        size = os.path.getsize(output)
        print('SUCCESS! Video created:', output)
        print('Size:', size, 'bytes (', round(size/1024/1024, 2), 'MB)')
    else:
        print('Failed to create video')
except Exception as e:
    print('Error:', type(e).__name__, str(e)[:200])
" 2>&1

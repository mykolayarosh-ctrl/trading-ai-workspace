import os
import json
import requests
import asyncio
import edge_tts
import subprocess
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import tempfile
from datetime import datetime

# Pexels API (free: 200 requests/hour)
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY', '')
PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_URL = "https://api.pexels.com/v1/search"

class VideoFactory:
    def __init__(self, output_dir="output", temp_dir="temp"):
        self.output_dir = output_dir
        self.temp_dir = temp_dir
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(f"{temp_dir}/audio", exist_ok=True)
        os.makedirs(f"{temp_dir}/media", exist_ok=True)
    
    def generate_script(self, topic, tone="educational", duration="medium", language="uk"):
        """Generate a simple script template for the video"""
        # For MVP, we'll create a structured template
        # In production, this would call an AI API
        
        templates = {
            "uk": {
                "intro": f"Вітаю! Сьогодні ми поговоримо про {topic}.",
                "body": f"{topic} — це дуже цікава тема, яка заслуговує на увагу.",
                "outro": f"Дякую за перегляд! Підписуйтесь на канал та ставте лайки."
            },
            "en": {
                "intro": f"Welcome! Today we're going to talk about {topic}.",
                "body": f"{topic} is a fascinating topic that deserves attention.",
                "outro": f"Thanks for watching! Subscribe to the channel and hit the like button."
            }
        }
        
        lang = language if language in templates else "en"
        t = templates[lang]
        
        # Create scenes based on duration
        if duration == "short":
            scenes = [
                {"narration": t["intro"], "visual": f"{topic} introduction", "duration": 5},
                {"narration": t["body"], "visual": topic, "duration": 8},
                {"narration": t["outro"], "visual": "subscribe like share", "duration": 5}
            ]
        elif duration == "long":
            scenes = [
                {"narration": t["intro"], "visual": f"{topic} introduction", "duration": 8},
                {"narration": f"Let's understand what {topic} really means.", "visual": topic, "duration": 12},
                {"narration": f"The history of {topic} goes back many years.", "visual": f"{topic} history", "duration": 15},
                {"narration": f"Today, {topic} plays a crucial role in our lives.", "visual": f"{topic} modern", "duration": 12},
                {"narration": f"Here are some key facts about {topic}.", "visual": f"{topic} facts", "duration": 10},
                {"narration": f"Experts agree that {topic} will continue to evolve.", "visual": f"{topic} future", "duration": 12},
                {"narration": f"To summarize, {topic} is truly important.", "visual": topic, "duration": 8},
                {"narration": t["outro"], "visual": "subscribe like share", "duration": 8}
            ]
        else:  # medium
            scenes = [
                {"narration": t["intro"], "visual": f"{topic} introduction", "duration": 8},
                {"narration": f"What is {topic}? Let's explore.", "visual": topic, "duration": 12},
                {"narration": f"{topic} has become increasingly important in recent years.", "visual": f"{topic} modern", "duration": 15},
                {"narration": f"Key insights about {topic}.", "visual": f"{topic} facts", "duration": 10},
                {"narration": t["outro"], "visual": "subscribe like share", "duration": 8}
            ]
        
        return {
            "title": topic,
            "language": language,
            "tone": tone,
            "scenes": scenes
        }
    
    def search_pexels(self, query, media_type="video", per_page=3):
        """Search for free media on Pexels"""
        if not PEXELS_API_KEY:
            return []
        
        headers = {"Authorization": PEXELS_API_KEY}
        
        if media_type == "video":
            url = f"{PEXELS_VIDEO_URL}?query={query}&per_page={per_page}"
        else:
            url = f"{PEXELS_PHOTO_URL}?query={query}&per_page={per_page}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if media_type == "video":
                    return [v['video_files'][0]['link'] for v in data.get('videos', []) if v.get('video_files')]
                else:
                    return [p['src']['large'] for p in data.get('photos', [])]
            return []
        except Exception as e:
            print(f"Pexels search error: {e}")
            return []
    
    async def generate_tts(self, text, output_file, voice="uk-UA-PolinaNeural"):
        """Generate TTS audio using Edge TTS (free)"""
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)
            return output_file
        except Exception as e:
            print(f"TTS error: {e}")
            return None
    
    def create_text_slide(self, text, duration=5, size=(1920, 1080)):
        """Create a text slide image for video background"""
        # Create gradient background
        img = Image.new('RGB', size, color='#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        # Draw text (simple wrapping)
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > 30:
                lines.append(' '.join(current_line[:-1]))
                current_line = [current_line[-1]]
        if current_line:
            lines.append(' '.join(current_line))
        
        y = size[1] // 2 - (len(lines) * 40)
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (size[0] - text_width) // 2
            draw.text((x, y), line, fill='#ffffff', font=font)
            y += 80
        
        temp_path = f"{self.temp_dir}/slide_{datetime.now().strftime('%H%M%S')}.png"
        img.save(temp_path)
        return temp_path
    
    def download_media(self, url, output_path):
        """Download media from URL"""
        try:
            response = requests.get(url, timeout=30, stream=True)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return output_path
            return None
        except Exception as e:
            print(f"Download error: {e}")
            return None
    
    def build_video(self, script, title=None):
        """Build video from script"""
        scenes = script.get('scenes', [])
        if not scenes:
            return None
        
        clips = []
        
        for i, scene in enumerate(scenes):
            print(f"Processing scene {i+1}/{len(scenes)}...")
            
            # Generate TTS audio
            audio_path = f"{self.temp_dir}/audio/scene_{i}.mp3"
            try:
                asyncio.run(self.generate_tts(scene['narration'], audio_path))
            except:
                # Fallback: create silent audio
                audio_path = None
            
            # Get media duration
            audio_duration = scene['duration']
            if audio_path and os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                audio_duration = max(audio_clip.duration, 3)
                audio_clip.close()
            
            # Search for media
            media_url = None
            if PEXELS_API_KEY:
                # Try video first, then photo
                videos = self.search_pexels(scene['visual'], "video", 1)
                if videos:
                    media_url = videos[0]
                else:
                    photos = self.search_pexels(scene['visual'], "photo", 1)
                    if photos:
                        media_url = photos[0]
            
            # Create visual clip
            if media_url:
                media_path = f"{self.temp_dir}/media/scene_{i}.mp4"
                self.download_media(media_url, media_path)
                
                if os.path.exists(media_path) and os.path.getsize(media_path) > 0:
                    try:
                        clip = VideoFileClip(media_path)
                        # Resize to 1080p
                        clip = clip.resize(height=1080)
                        # Loop if needed
                        if clip.duration < audio_duration:
                            clip = clip.loop(duration=audio_duration)
                        else:
                            clip = clip.subclip(0, audio_duration)
                    except:
                        clip = None
                else:
                    clip = None
            else:
                clip = None
            
            # Fallback: text slide with Ken Burns effect
            if clip is None:
                slide_path = self.create_text_slide(scene['visual'], audio_duration)
                img = ImageClip(slide_path).set_duration(audio_duration)
                # Ken Burns: slow zoom
                img = img.resize(lambda t: 1 + 0.05 * t / audio_duration)
                img = img.set_position('center')
                clip = img
            
            # Add audio to clip
            if audio_path and os.path.exists(audio_path):
                audio = AudioFileClip(audio_path)
                clip = clip.set_audio(audio)
            
            clips.append(clip)
        
        # Concatenate all clips with crossfade
        if len(clips) > 1:
            final = concatenate_videoclips(clips, method="compose")
        else:
            final = clips[0] if clips else None
        
        if final is None:
            return None
        
        # Add title card if provided
        if title:
            title_slide = self.create_text_slide(title, 3, (1920, 1080))
            title_clip = ImageClip(title_slide).set_duration(3)
            final = concatenate_videoclips([title_clip, final], method="compose")
        
        # Export
        output_filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        final.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=24,
            preset='medium',
            threads=4,
            logger=None
        )
        
        # Cleanup
        final.close()
        for clip in clips:
            clip.close()
        
        return output_path
    
    def cleanup(self):
        """Clean temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir, exist_ok=True)


if __name__ == "__main__":
    # Test
    factory = VideoFactory()
    script = factory.generate_script("Artificial Intelligence", "educational", "short", "en")
    print(json.dumps(script, indent=2, ensure_ascii=False))

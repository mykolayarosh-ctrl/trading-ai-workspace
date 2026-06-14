# Video Factory — Автоматичний відеозавод 🎬

## Опис
Автоматична система створення відео для YouTube. Введи тему — отримай готове 1080p HD відео з озвучкою, відеорядом та субтитрами.

## Архітектура

### Pipeline:
```
Ідея/Тема → Сценарій → Пошук медіа (Pexels) → TTS (Edge) → Монтаж (MoviePy) → 1080p MP4
```

### Компоненти:
- `app.py` — Flask веб-сервер
- `video_generator.py` — генератор відео
- `templates/index.html` — веб-інтерфейс

## Безкоштовні джерела медіа

### Pexels (pexels.com)
- **API**: 200 requests/hour безкоштовно
- **Ліцензія**: Pexels License (можна монетизувати, без атрибуції)
- **Тип**: фото та відео
- **Як отримати API Key**: https://www.pexels.com/api/

### Pixabay (pixabay.com)
- **API**: безкоштовно
- **Ліцензія**: Pixabay License (можна монетизувати)
- **Тип**: фото, відео, музика
- **Як отримати API Key**: https://pixabay.com/api/docs/

### Mixkit (mixkit.co)
- **Безкоштовно**: відео та музика
- **Ліцензія**: Mixkit License (можна монетизувати)
- **Без API**: прямий доступ

## TTS (Text-to-Speech)

### Edge TTS (Microsoft Edge)
- **Ціна**: безкоштовно
- **Якість**: дуже висока
- **Мови**: українська, російська, англійська, 100+ інших
- **Голоси**: різні (чоловічі, жіночі, нейтральні)

**Приклади голосів:**
- `uk-UA-PolinaNeural` — українська, жіночий
- `ru-RU-SvetlanaNeural` — російська, жіночий
- `en-US-AriaNeural` — англійська, жіночий
- `en-US-GuyNeural` — англійська, чоловічий

## Формат відео
- **Роздільність**: 1920x1080 (Full HD)
- **Аспект**: 16:9
- **Кодек**: H.264 (video), AAC (audio)
- **Контейнер**: MP4
- **FPS**: 24
- **Тривалість**: 5-30 хвилин (залежить від налаштувань)

## Локальний запуск

```bash
# 1. Встанови залежності
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Встанови FFmpeg (для MoviePy)
# Ubuntu/Debian:
sudo apt-get install ffmpeg
# macOS:
brew install ffmpeg
# Windows: завантаж з https://ffmpeg.org/download.html

# 3. Додай Pexels API Key (опціонально, для медіа)
export PEXELS_API_KEY="your_api_key_here"

# 4. Запусти
python app.py
```

## Render деплой

### Налаштування:
1. **Build Command**:
```bash
apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt
```

2. **Start Command**:
```bash
python app.py
```

3. **Environment Variables**:
- `PEXELS_API_KEY` — для пошуку медіа (опціонально)

### Обмеження безкоштовного плану:
- Pexels: 200 requests/hour
- Тривалість генерації: ~5-15 хв/відео
- Тимчасові файли: ~500MB

## Використання

### 1. Веб-інтерфейс
Відкрий `/` в браузері. Введи:
- **Тема** — ідея для відео
- **Тональність** — навчальна, розважальна, драматична
- **Тривалість** — коротка, середня, довга
- **Мова** — українська, англійська, російська
- **Свій сценарій** — опціонально (якщо хочеш контролювати текст)

### 2. API

**Генерація відео:**
```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "History of Ancient Rome",
    "tone": "educational",
    "duration": "medium",
    "language": "en"
  }'
```

**Перевірка статусу:**
```bash
curl http://localhost:5000/api/status/job_20240614_123456
```

**Скачування:**
```bash
curl http://localhost:5000/api/download/job_20240614_123456 -o video.mp4
```

## Структура сценарію

```json
{
  "title": "History of Ancient Rome",
  "language": "en",
  "scenes": [
    {
      "scene_number": 1,
      "narration": "Welcome to our journey through Ancient Rome.",
      "visual_description": "ancient rome colosseum",
      "duration": 8
    }
  ]
}
```

## Функціональність

### ✅ Готово:
- Генерація сценарію (шаблонна + AI)
- Пошук медіа через Pexels API
- TTS через Edge TTS (безкоштовно)
- Монтаж через MoviePy
- Вивід у 1080p HD
- Веб-інтерфейс
- REST API
- Підтримка української, англійської, російської

### 🚧 В розробці:
- AI генерація сценаріїв (GPT-4)
- Субтитри
- Фонова музика
- Ken Burns effect для фото
- Більше переходів між сценами
- Пакетна обробка (генерація кількох відео)

### 📋 В планах:
- YouTube upload API
- Генерація thumbnails
- SEO optimization (title, description, tags)
- Автоматична публікація за розкладом
- A/B testing заголовків

## Ліцензія на вихідні відео

**Всі матеріали з Pexels/Pixabay/Mixkit:**
- ✅ Можна використовувати комерційно
- ✅ Можна монетизувати
- ❌ Не потрібна атрибуція
- ❌ Не можна продавати як є (stock)

**Вихідне відео:** належить тобі, можеш монетизувати на YouTube.

## Проблеми та рішення

### "No module named 'moviepy'"
```bash
pip install moviepy==1.0.3
```

### "FFmpeg not found"
Встанови FFmpeg для своєї ОС (див. розділ Локальний запуск).

### "Pexels API rate limit"
- Зачекай 1 годину (200 requests/hour)
- Або використовуй fallback (текстові слайди)

### Довга генерація
- Тривалість залежить від кількості сцен
- Типово: 5-15 хвилин на відео
- Для Render Free tier: обмеження по часу обробки

## Контакти
- Проєкт: `video-factory/`
- Скрінер: `../` (попередній проєкт)

# ComicCraft - AI Comic Story Creator

## Features
- FastAPI backend
- Gemini-powered 5-panel story generation
- Hugging Face image generation when HF_API_KEY is available
- Safe fallback panel images when Hugging Face is unavailable
- Jinja2 frontend
- PDF export
- JSON API
- Image test endpoint

## Windows setup

Open PowerShell inside the ComicCraftAI folder.

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create `.env` by copying `.env.example`, then add your keys.

Run:

```powershell
python -m uvicorn app.main:app --reload
```

Open:
http://127.0.0.1:8000

API docs:
http://127.0.0.1:8000/docs

## Important
Do not upload `.env` or API keys to GitHub.

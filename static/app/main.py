from pathlib import Path
from datetime import datetime
import json
import re

from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .gemini_service import generate_comic_content
from .image_generator import generate_image
from .pdf_exporter import create_pdf

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
PANELS_DIR = STATIC_DIR / "panels"
EXPORTS_DIR = STATIC_DIR / "exports"
TEMPLATES_DIR = BASE_DIR / "templates"

for folder in [STATIC_DIR, PANELS_DIR, EXPORTS_DIR, TEMPLATES_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="ComicCraft - AI Comic Story Creator", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class PromptRequest(BaseModel):
    story_prompt: str
    character_name: str = "Alex"
    setting: str = "enchanted forest"
    tone: str = "funny"
    art_style: str = "comic book"


def safe_filename(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "_", value)
    return value.strip("_")[:40] or "comic"


def build_layout(content: dict, image_paths: list[str]) -> list[dict]:
    layout = []
    for index, panel in enumerate(content["panels"]):
        layout.append({
            "number": panel["number"],
            "title": panel["title"],
            "scene": panel["scene"],
            "caption": panel["caption"],
            "narration": panel["narration"],
            "dialogue": panel["dialogue"],
            "image_prompt": panel["image_prompt"],
            "image_path": image_paths[index],
        })
    return layout


def run_generation(data: PromptRequest) -> tuple[list[dict], str]:
    content = generate_comic_content(
        story_prompt=data.story_prompt,
        character_name=data.character_name,
        setting=data.setting,
        tone=data.tone,
        art_style=data.art_style,
    )

    image_paths = []
    for panel in content["panels"]:
        image_path = generate_image(
            panel["image_prompt"],
            panel["number"],
            art_style=data.art_style,
        )
        image_paths.append(image_path)

    layout = build_layout(content, image_paths)
    pdf_name = f"{safe_filename(data.character_name)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = create_pdf(layout, EXPORTS_DIR / pdf_name)
    return layout, f"/static/exports/{pdf_name}"


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),
):
    try:
        data = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )
        layout, pdf_url = run_generation(data)
        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": layout,
                "pdf_url": pdf_url
        }
        )
    except Exception as exc:
        return templates.TemplateResponse(
           request=request,
           name="index.html",
           context={"error": str(exc)},
           status_code=500
        )


@app.post("/generate-comic/json")
async def generate_json(data: PromptRequest):
    try:
        layout, pdf_url = run_generation(data)
        return JSONResponse({"success": True, "layout": layout, "pdf_path": pdf_url})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={}
    )


@app.get("/test-image")
async def test_image(prompt: str = "A friendly fox exploring a magical forest, comic book style"):
    try:
        path = generate_image(prompt, 1, "comic book")
        return {"success": True, "image": path}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ComicCraft"}

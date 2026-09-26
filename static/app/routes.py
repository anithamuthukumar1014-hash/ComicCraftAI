import os
import re
from pathlib import Path

from fastapi import (
    APIRouter,
    Request,
    Form,
    HTTPException
)

from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse
)

from fastapi.templating import Jinja2Templates

from .models import PromptRequest
from .gemini_flash import generate_outline
from .gemini_pro import generate_story
from .image_generator import generate_image
from .layout_builder import build_comic_layout
from .exporters import save_pdf


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(
        BASE_DIR / "templates"
    )
)


def create_comic(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
    panel_count: int
):

    outline = generate_outline(
        story_prompt=story_prompt,
        character_name=character_name,
        setting=setting,
        tone=tone,
        art_style=art_style,
        panel_count=panel_count
    )

    stories = generate_story(
        outline=outline,
        character_name=character_name,
        tone=tone
    )

    image_paths = []

    for panel in outline:

        image_prompt = panel.get(
            "image_prompt",
            ""
        )

        image_path = generate_image(
            image_prompt=image_prompt,
            panel_number=panel.get(
                "panel_number",
                len(image_paths) + 1
            )
        )

        image_paths.append(
            image_path
        )

    layout = build_comic_layout(
        outline=outline,
        stories=stories,
        image_paths=image_paths
    )

    title = (
        f"{character_name}'s "
        f"Comic Adventure"
    )

    pdf_path = save_pdf(
        layout=layout,
        title=title
    )

    return {
        "title": title,
        "layout": layout,
        "pdf_path": pdf_path
    }


@router.get(
    "/",
    response_class=HTMLResponse
)
async def home(
    request: Request
):
    context={
        "request":request
    }

    return templates.TemplateResponse(

        request=request,
        name="index.html",
        context=context
    )


@router.post(
    "/generate",
    response_class=HTMLResponse
)
async def generate_comic(
    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(
        "Alex"
    ),

    setting: str = Form(
        "Fantasy Forest"
    ),

    tone: str = Form(
        "Funny"
    ),

    art_style: str = Form(
        "Comic Book"
    ),

    panel_count: int = Form(
        5
    )
):

    try:

        panel_count = max(
            1,
            min(panel_count, 8)
        )

        result = create_comic(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
            panel_count=panel_count
        )

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "request": request,
                "title": result["title"],
                "layout": result["layout"],
                "pdf_path": result["pdf_path"]
            }
        )

    except Exception as exc:

        print(
            f"[Generate Error] {exc}"
        )

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "error": (
                    "Something went wrong while "
                    "creating the comic. "
                    f"Error: {str(exc)}"
                )
            },
            status_code=500
        )


@router.post(
    "/generate-comic/json"
)
async def generate_comic_json(
    data: PromptRequest
):

    try:

        result = create_comic(
            story_prompt=data.story_prompt,
            character_name=data.character_name,
            setting=data.setting,
            tone=data.tone,
            art_style=data.art_style,
            panel_count=data.panel_count
        )

        return JSONResponse(
            content={
                "success": True,
                "title": result["title"],
                "panels": result["layout"],
                "pdf_path": result["pdf_path"]
            }
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


@router.get(
    "/test-image"
)
async def test_image():

    image_path = generate_image(
        "A cute superhero fox standing "
        "in a magical forest, comic book "
        "style, colorful, cinematic lighting",
        999
    )

    return {
        "success": True,
        "image_path": image_path
    }


@router.get(
    "/export-success",
    response_class=HTMLResponse
)
async def export_success(
    request: Request,
    pdf_path: str = ""
):

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "request": request,
            "pdf_path": pdf_path
        }
    )
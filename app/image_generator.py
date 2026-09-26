import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
PANELS_DIR = BASE_DIR / "static" / "panels"
PANELS_DIR.mkdir(parents=True, exist_ok=True)

HF_API_KEY = os.getenv("HF_API_KEY", "").strip()
HF_IMAGE_MODEL = os.getenv(
    "HF_IMAGE_MODEL",
    "stabilityai/stable-diffusion-xl-base-1.0"
)


def _fallback_image(prompt: str, panel_number: int) -> str:
    """Always creates a usable image if Hugging Face is unavailable."""
    path = PANELS_DIR / f"panel_{panel_number}.png"
    img = Image.new("RGB", (1024, 768), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle((25, 25, 999, 743), outline="black", width=8)
    draw.text((60, 70), f"COMIC PANEL {panel_number}", fill="black")
    short_prompt = prompt[:240].replace("\n", " ")
    draw.text((60, 150), "AI image service not available.", fill="black")
    draw.text((60, 210), "Add HF_API_KEY to enable image generation.", fill="black")
    draw.text((60, 300), short_prompt, fill="black")
    img.save(path)
    return f"/static/panels/{path.name}"


def generate_image(prompt: str, panel_number: int, art_style: str = "comic book") -> str:
    final_prompt = (
        f"{prompt}. Visual style: {art_style}. "
        "Clean comic illustration, expressive characters, strong composition, "
        "consistent character appearance, no text, no watermark."
    )

    if not HF_API_KEY:
        return _fallback_image(final_prompt, panel_number)

    try:
        from huggingface_hub import InferenceClient

        client = InferenceClient(token=HF_API_KEY)
        image = client.text_to_image(
            final_prompt,
            model=HF_IMAGE_MODEL,
        )

        path = PANELS_DIR / f"panel_{panel_number}.png"
        image.save(path)
        return f"/static/panels/{path.name}"

    except Exception:
        return _fallback_image(final_prompt, panel_number)

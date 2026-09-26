import json
import os
import re
from typing import List, Dict

from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
except ImportError:
    genai = None


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_FLASH_MODEL = os.getenv(
    "GEMINI_FLASH_MODEL",
    "gemini-3.8-flash"
)


def _extract_json(text: str):
    """
    Extract JSON from Gemini response even if it is wrapped
    inside markdown code fences.
    """
    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)

        if match:
            return json.loads(match.group(0))

        raise


def _fallback_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
    panel_count: int
) -> List[Dict]:
    """
    Fallback outline used if Gemini is not configured.
    This allows the application to run and demonstrate
    the complete UI workflow.
    """

    panels = []

    titles = [
        "The Beginning",
        "A Strange Discovery",
        "The Challenge",
        "The Big Moment",
        "A New Beginning",
        "The Unexpected Twist",
        "The Final Challenge",
        "The Ending"
    ]

    for i in range(panel_count):
        title = titles[i] if i < len(titles) else f"Adventure Part {i + 1}"

        if i == 0:
            scene = (
                f"{character_name} begins an exciting adventure in "
                f"{setting}. The story starts with the idea: "
                f"{story_prompt}."
            )
        elif i == panel_count - 1:
            scene = (
                f"{character_name} reaches the conclusion of the "
                f"adventure in {setting} and learns an important lesson."
            )
        else:
            scene = (
                f"{character_name} continues the adventure in {setting}. "
                f"A new event connected to '{story_prompt}' creates "
                f"a {tone.lower()} situation."
            )

        image_prompt = (
            f"{art_style} comic illustration, {character_name}, "
            f"{setting}, {scene}, expressive characters, cinematic "
            f"composition, detailed background, vibrant comic artwork"
        )

        panels.append(
            {
                "panel_number": i + 1,
                "title": title,
                "scene_description": scene,
                "image_prompt": image_prompt
            }
        )

    return panels


def generate_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
    panel_count: int = 5
) -> List[Dict]:

    if not GEMINI_API_KEY or genai is None:
        return _fallback_outline(
            story_prompt,
            character_name,
            setting,
            tone,
            art_style,
            panel_count
        )

    prompt = f"""
You are ComicCraft, an AI comic story planner.

Create a {panel_count}-panel comic outline.

User information:

Story idea:
{story_prompt}

Main character:
{character_name}

Setting:
{setting}

Story tone:
{tone}

Art style:
{art_style}

Return ONLY valid JSON.

The JSON must be an array.

Each item must contain exactly:

{{
    "panel_number": 1,
    "title": "Panel title",
    "scene_description": "Short scene description",
    "image_prompt": "Detailed visual prompt for an AI image generator"
}}

Rules:
- Create exactly {panel_count} panels.
- Keep the same main character throughout.
- Make the story flow naturally from panel to panel.
- Make every image prompt visually detailed.
- Do not use markdown.
"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model=GEMINI_FLASH_MODEL,
            contents=prompt
        )

        data = _extract_json(response.text)

        if not isinstance(data, list):
            raise ValueError("Gemini did not return a list.")

        return data

    except Exception as exc:
        print(f"[Gemini Flash Error] {exc}")
        print("Using fallback outline.")

        return _fallback_outline(
            story_prompt,
            character_name,
            setting,
            tone,
            art_style,
            panel_count
        )
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

GEMINI_PRO_MODEL = os.getenv(
    "GEMINI_PRO_MODEL",
    "gemini-3.8-pro"
)


def _extract_json(text: str):
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

        match = re.search(
            r"\[.*\]",
            text,
            re.DOTALL
        )

        if match:
            return json.loads(match.group(0))

        raise


def _fallback_story(
    outline: List[Dict],
    character_name: str,
    tone: str
) -> List[Dict]:

    result = []

    for panel in outline:

        number = panel.get("panel_number", 1)
        title = panel.get("title", f"Panel {number}")
        scene = panel.get("scene_description", "")

        if number == 1:
            dialogue = (
                f"{character_name}: "
                f"I have a feeling this adventure is going to be special!"
            )
        elif number == len(outline):
            dialogue = (
                f"{character_name}: "
                f"We made it! What an incredible adventure!"
            )
        else:
            dialogue = (
                f"{character_name}: "
                f"We have to keep going. There must be a way!"
            )

        result.append(
            {
                "panel_number": number,
                "title": title,
                "caption": f"Meanwhile, in the {tone.lower()} world...",
                "narration": scene,
                "dialogue": dialogue
            }
        )

    return result


def generate_story(
    outline: List[Dict],
    character_name: str,
    tone: str
) -> List[Dict]:

    if not GEMINI_API_KEY or genai is None:
        return _fallback_story(
            outline,
            character_name,
            tone
        )

    outline_json = json.dumps(
        outline,
        indent=2,
        ensure_ascii=False
    )

    prompt = f"""
You are a professional comic book writer.

Create narration and dialogue for this comic.

Main character:
{character_name}

Tone:
{tone}

Comic outline:
{outline_json}

Return ONLY valid JSON.

Return an array with one object per panel.

Each object must contain:

{{
    "panel_number": 1,
    "title": "Panel title",
    "caption": "Short comic caption",
    "narration": "Short narration",
    "dialogue": "Character dialogue"
}}

Rules:
- Keep the story coherent.
- Use the same character.
- Keep narration concise.
- Make dialogue sound natural.
- Match the requested tone.
- Do not include markdown.
"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model=GEMINI_PRO_MODEL,
            contents=prompt
        )

        data = _extract_json(response.text)

        if not isinstance(data, list):
            raise ValueError("Gemini returned invalid story data.")

        return data

    except Exception as exc:
        print(f"[Gemini Story Error] {exc}")
        print("Using fallback story.")

        return _fallback_story(
            outline,
            character_name,
            tone
        )
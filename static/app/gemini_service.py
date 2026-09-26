import json
import os
import re
import time

from dotenv import load_dotenv
from google import genai


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
).strip()

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
).strip()


# =========================================================
# CHECK API KEY
# =========================================================

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. "
        "Add it to your .env file and restart the server."
    )


# =========================================================
# CREATE GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# EXTRACT JSON FROM GEMINI RESPONSE
# =========================================================

def _extract_json(text: str) -> dict:

    if not text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    text = text.strip()

    # Remove ```json
    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove ```
    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    # Remove ending ```
    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    # Find beginning and ending of JSON
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "Gemini did not return valid JSON."
        )

    json_text = text[start:end + 1]

    try:
        return json.loads(json_text)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Gemini returned invalid JSON: {exc}"
        ) from exc


# =========================================================
# GENERATE COMIC CONTENT
# =========================================================

def generate_comic_content(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
) -> dict:

    prompt = f"""
Create a complete 5-panel comic story.

User story idea:
{story_prompt}

Main character:
{character_name}

Setting:
{setting}

Tone:
{tone}

Art style:
{art_style}

Return ONLY valid JSON in exactly this structure:

{{
  "title": "short comic title",
  "panels": [
    {{
      "number": 1,
      "title": "panel title",
      "scene": "short scene description",
      "caption": "short caption",
      "narration": "2-3 sentences of narration",
      "dialogue": "character dialogue",
      "image_prompt": "detailed visual prompt for an AI image generator"
    }}
  ]
}}

Rules:

- Exactly 5 panels.
- Panel numbers must be 1, 2, 3, 4 and 5.
- Keep the same main character across all panels.
- Make the story have a clear beginning, middle and ending.
- Keep narration and dialogue family-friendly.
- Image prompts must describe characters, setting, action,
  lighting and composition.
- Do not put Markdown around the JSON.
- Return JSON only.
"""

    # =====================================================
    # GEMINI RETRY SYSTEM
    # =====================================================

    max_attempts = 3

    for attempt in range(1, max_attempts + 1):

        try:

            print(
                f"Generating comic with "
                f"{GEMINI_MODEL} "
                f"(attempt {attempt}/{max_attempts})..."
            )

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )

            response_text = getattr(
                response,
                "text",
                None
            )

            # Extract JSON
            data = _extract_json(
                response_text
            )

            # =================================================
            # VALIDATE RESPONSE
            # =================================================

            if not isinstance(data, dict):
                raise ValueError(
                    "Gemini response is not a JSON object."
                )

            if "title" not in data:
                raise ValueError(
                    "Gemini response is missing the comic title."
                )

            if not isinstance(
                data.get("panels"),
                list
            ):
                raise ValueError(
                    "Gemini response does not contain panels."
                )

            if len(data["panels"]) != 5:
                raise ValueError(
                    "Gemini returned an invalid "
                    "5-panel structure."
                )

            # =================================================
            # VALIDATE EACH PANEL
            # =================================================

            for index, panel in enumerate(
                data["panels"],
                start=1
            ):

                if not isinstance(panel, dict):
                    raise ValueError(
                        f"Panel {index} is invalid."
                    )

                # Force correct panel number
                panel["number"] = index

                # Add missing fields safely
                panel.setdefault(
                    "title",
                    f"Panel {index}"
                )

                panel.setdefault(
                    "scene",
                    ""
                )

                panel.setdefault(
                    "caption",
                    ""
                )

                panel.setdefault(
                    "narration",
                    ""
                )

                panel.setdefault(
                    "dialogue",
                    ""
                )

                panel.setdefault(
                    "image_prompt",
                    ""
                )

            print(
                "Comic generated successfully."
            )

            return data

        # =====================================================
        # ERROR HANDLING
        # =====================================================

        except Exception as exc:

            error_message = str(exc)

            print(
                f"Gemini attempt "
                f"{attempt}/{max_attempts} failed:"
            )

            print(
                error_message
            )

            # -------------------------------------------------
            # Check whether this is a temporary error
            # -------------------------------------------------

            temporary_error = (
                "503" in error_message
                or "UNAVAILABLE" in error_message
                or "high demand"
                in error_message.lower()
                or "temporarily unavailable"
                in error_message.lower()
                or "429" in error_message
            )

            # -------------------------------------------------
            # Retry temporary errors
            # -------------------------------------------------

            if (
                temporary_error
                and attempt < max_attempts
            ):

                wait_time = attempt * 5

                print(
                    f"Gemini is temporarily unavailable."
                )

                print(
                    f"Retrying in "
                    f"{wait_time} seconds..."
                )

                time.sleep(
                    wait_time
                )

                continue

            # -------------------------------------------------
            # Stop if it is not a temporary error
            # -------------------------------------------------

            raise RuntimeError(
                f"Gemini generation failed: "
                f"{error_message}"
            ) from exc

    # =====================================================
    # FINAL FALLBACK
    # =====================================================

    raise RuntimeError(
        "Unable to generate the comic after "
        "multiple attempts."
    )
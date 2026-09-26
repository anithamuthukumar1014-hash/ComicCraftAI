import os
import re
import uuid
from pathlib import Path

from fpdf import FPDF  # type: ignore[import-not-found]


BASE_DIR = Path(__file__).resolve().parent.parent

EXPORT_DIR = (
    BASE_DIR /
    "static" /
    "exports"
)

EXPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def _clean_text(text: str) -> str:

    if not text:
        return ""

    # FPDF built-in fonts don't support every Unicode character.
    replacements = {
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "•": "-",
    }

    for old, new in replacements.items():
        text = text.replace(
            old,
            new
        )

    return text.encode(
        "latin-1",
        "replace"
    ).decode(
        "latin-1"
    )


def save_pdf(
    layout,
    title: str = "ComicCraft Comic"
) -> str:

    filename = (
        f"comiccraft_"
        f"{uuid.uuid4().hex[:10]}.pdf"
    )

    output_path = EXPORT_DIR / filename

    pdf = FPDF(
        orientation="P",
        unit="mm",
        format="A4"
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=15
    )

    pdf.set_title(
        _clean_text(title)
    )

    for panel in layout:

        pdf.add_page()

        # Title
        pdf.set_font(
            "Arial",
            "B",
            20
        )

        panel_title = (
            f"Panel {panel['panel_number']}: "
            f"{panel['title']}"
        )

        pdf.multi_cell(
            0,
            12,
            _clean_text(panel_title)
        )

        pdf.ln(3)

        # Image
        image_path = panel.get(
            "image_path"
        )

        if image_path:

            if image_path.startswith(
                "/static/"
            ):
                relative = image_path[
                    len("/static/"):
                ]

                full_image_path = (
                    BASE_DIR /
                    "static" /
                    relative
                )

            else:
                full_image_path = (
                    BASE_DIR /
                    image_path
                )

            if full_image_path.exists():

                try:
                    pdf.image(
                        str(full_image_path),
                        x=15,
                        y=45,
                        w=180,
                        h=110
                    )

                except Exception as exc:
                    print(
                        f"PDF image error: {exc}"
                    )

        pdf.ln(115)

        # Scene
        pdf.set_font(
            "Arial",
            "I",
            11
        )

        pdf.multi_cell(
            0,
            7,
            _clean_text(
                panel.get(
                    "scene_description",
                    ""
                )
            )
        )

        pdf.ln(3)

        # Caption
        if panel.get("caption"):

            pdf.set_font(
                "Arial",
                "B",
                11
            )

            pdf.multi_cell(
                0,
                7,
                "Caption: " +
                _clean_text(
                    panel["caption"]
                )
            )

        pdf.ln(2)

        # Narration
        if panel.get("narration"):

            pdf.set_font(
                "Arial",
                "",
                11
            )

            pdf.multi_cell(
                0,
                7,
                "Narration: " +
                _clean_text(
                    panel["narration"]
                )
            )

        pdf.ln(2)

        # Dialogue
        if panel.get("dialogue"):

            pdf.set_font(
                "Arial",
                "B",
                11
            )

            pdf.multi_cell(
                0,
                7,
                "Dialogue: " +
                _clean_text(
                    panel["dialogue"]
                )
            )

    pdf.output(
        str(output_path)
    )

    return f"/static/exports/{filename}"
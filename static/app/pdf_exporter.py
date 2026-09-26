from pathlib import Path
from fpdf import FPDF


def clean_text(text):
    """Make text safe for the PDF."""

    if text is None:
        return ""

    text = str(text)

    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u00a0": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.encode(
        "latin-1",
        "replace"
    ).decode("latin-1")


def create_pdf(layout, output_path):
    """
    Create a PDF from the ComicCraft panel layout.
    """

    output_path = Path(output_path)

    # Create output folder if necessary
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    pdf = FPDF(
        orientation="P",
        unit="mm",
        format="A4"
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=15
    )

    # --------------------------------------------------
    # Create pages
    # --------------------------------------------------

    for panel in layout:

        pdf.add_page()

        # -----------------------------
        # Panel title
        # -----------------------------

        pdf.set_font(
            "Helvetica",
            "B",
            18
        )

        panel_number = panel.get(
            "number",
            ""
        )

        panel_title = panel.get(
            "title",
            "Comic Panel"
        )

        title = clean_text(
            f"Panel {panel_number}: {panel_title}"
        )

        usable_width = (
            pdf.w
            - pdf.l_margin
            - pdf.r_margin
        )

        pdf.multi_cell(
            usable_width,
            10,
            title
        )

        pdf.ln(5)

        # -----------------------------
        # Panel image
        # -----------------------------

        image_path = panel.get("image")

        if image_path:

            image_path = Path(
                image_path
            )

            if image_path.exists():

                image_width = 170

                x_position = (
                    pdf.w - image_width
                ) / 2

                pdf.image(
                    str(image_path),
                    x=x_position,
                    w=image_width
                )

                pdf.ln(8)

        # -----------------------------
        # Narration
        # -----------------------------

        narration = panel.get(
            "narration",
            ""
        )

        if narration:

            pdf.set_font(
                "Helvetica",
                "B",
                12
            )

            pdf.multi_cell(
                usable_width,
                8,
                "Narration:"
            )

            pdf.set_font(
                "Helvetica",
                "",
                11
            )

            pdf.multi_cell(
                usable_width,
                7,
                clean_text(narration)
            )

            pdf.ln(4)

        # -----------------------------
        # Dialogue
        # -----------------------------

        dialogue = panel.get(
            "dialogue",
            ""
        )

        if dialogue:

            pdf.set_font(
                "Helvetica",
                "B",
                12
            )

            pdf.multi_cell(
                usable_width,
                8,
                "Dialogue:"
            )

            pdf.set_font(
                "Helvetica",
                "",
                11
            )

            pdf.multi_cell(
                usable_width,
                7,
                clean_text(dialogue)
            )

    # --------------------------------------------------
    # Empty layout
    # --------------------------------------------------

    if not layout:

        pdf.add_page()

        pdf.set_font(
            "Helvetica",
            "B",
            18
        )

        pdf.cell(
            0,
            10,
            "ComicCraft",
            new_x="LMARGIN",
            new_y="NEXT",
            align="C"
        )

        pdf.set_font(
            "Helvetica",
            "",
            12
        )

        pdf.multi_cell(
            0,
            10,
            "No comic panels were generated."
        )

    # --------------------------------------------------
    # Save PDF
    # --------------------------------------------------

    pdf.output(
        str(output_path)
    )

    return str(output_path)


# Compatibility alias
# This also allows code using save_pdf() to work.
save_pdf = create_pdf
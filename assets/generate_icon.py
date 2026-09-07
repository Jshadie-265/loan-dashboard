"""Generate a multi-resolution application icon for Loan Manager.

Produces assets/app_icon.ico with sizes 16×16 through 256×256.
Requires Pillow (already installed via streamlit dependency).
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BRAND_GREEN = "#146356"
ACCENT_GOLD = "#D4AF37"
SIZES = [16, 32, 48, 64, 128, 256]


def _draw_icon(size: int) -> Image.Image:
    """Draw a single icon frame at the requested pixel size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded-rect background
    margin = max(1, size // 16)
    radius = max(2, size // 5)
    draw.rounded_rectangle(
        [margin, margin, size - margin - 1, size - margin - 1],
        radius=radius,
        fill=BRAND_GREEN,
    )

    # Dollar sign in the centre
    font_size = int(size * 0.55)
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    text = "$"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    draw.text((x, y), text, fill=ACCENT_GOLD, font=font)

    return img


def generate_icon(out_path: Path | str | None = None) -> Path:
    """Create an .ico file containing all standard sizes."""
    out = Path(out_path) if out_path else Path(__file__).parent / "app_icon.ico"
    out.parent.mkdir(parents=True, exist_ok=True)

    frames = [_draw_icon(s) for s in SIZES]
    # Save ICO with multiple sizes — Pillow requires the first image's save()
    # and the remaining images passed via append_images.
    frames[-1].save(
        str(out),
        format="ICO",
        append_images=frames[:-1],
    )
    print(f"Icon saved -> {out}  ({out.stat().st_size:,} bytes)")
    return out


if __name__ == "__main__":
    generate_icon()

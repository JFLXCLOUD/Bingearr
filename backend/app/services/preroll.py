"""Generate a short promo-preroll video for a marathon.

Pillow renders a 1080p card (the playlist's poster art, darkened, with a
call-to-action) and ffmpeg turns it into a ~6s H.264 MP4 with a silent audio
track — a valid preroll for Plex via NeXroll.
"""

from __future__ import annotations

import io
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 1920, 1080
MARGIN = 150
ACCENT = (34, 211, 197)   # Bingearr aqua
BG = (14, 15, 19)

_FONT_CANDIDATES = {
    True: ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    False: ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES[bold]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap(draw, text, font, max_width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines[:3]  # never let a long title blow out the card


def render_card(title: str, server_name: str, subtitle: str | None, poster_bytes: bytes | None) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)

    if poster_bytes:
        try:
            poster = Image.open(io.BytesIO(poster_bytes)).convert("RGB")
            poster = ImageOps.fit(poster, (W, H), method=Image.LANCZOS)
            poster = poster.filter(ImageFilter.GaussianBlur(14))
            img.paste(poster, (0, 0))
            img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), 0.58)
        except Exception:
            img = Image.new("RGB", (W, H), BG)

    draw = ImageDraw.Draw(img)

    # Left accent rule
    draw.rectangle([MARGIN, 360, MARGIN + 90, 368], fill=ACCENT)
    draw.text((MARGIN, 300), "CHECK OUT", font=_font(56), fill=ACCENT)

    # Title (wrapped)
    title_font = _font(108)
    y = 392
    for line in _wrap(draw, title, title_font, W - 2 * MARGIN):
        draw.text((MARGIN, y), line, font=title_font, fill=(255, 255, 255))
        y += 124

    draw.text((MARGIN, y + 24), f"Now streaming on {server_name}", font=_font(58, bold=False), fill=(233, 235, 240))
    if subtitle:
        draw.text((MARGIN, y + 110), subtitle, font=_font(40, bold=False), fill=(165, 173, 184))

    # Bingearr wordmark (play badge + text) bottom-left
    by = H - 150
    draw.rounded_rectangle([MARGIN, by, MARGIN + 56, by + 56], radius=14, fill=ACCENT)
    draw.polygon([(MARGIN + 22, by + 16), (MARGIN + 42, by + 28), (MARGIN + 22, by + 40)], fill=BG)
    draw.text((MARGIN + 74, by + 6), "Bingearr", font=_font(44), fill=(255, 255, 255))

    return img


def generate_promo(
    out_path: str,
    title: str,
    server_name: str,
    subtitle: str | None = None,
    poster_bytes: bytes | None = None,
    seconds: int = 6,
    ffmpeg: str = "ffmpeg",
) -> str:
    """Render the card and encode a short MP4 promo at out_path."""
    card = render_card(title, server_name, subtitle, poster_bytes)
    png_fd, png_path = tempfile.mkstemp(suffix=".png")
    os.close(png_fd)
    card.save(png_path)
    try:
        cmd = [
            ffmpeg, "-y",
            "-loop", "1", "-i", png_path,
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t", str(seconds), "-r", "30",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest",
            out_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {proc.stderr[-500:]}")
    finally:
        try:
            os.remove(png_path)
        except Exception:
            pass
    return out_path

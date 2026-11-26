"""Square 1200x1200 cover image per article (used for LinkedIn image posts and og:image)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONTS = Path(__file__).resolve().parent / "assets" / "fonts"
GREEN, GOLD, WHITE, DARK = "#0f3d2e", "#d4a843", "#ffffff", "#0b2e22"


def _font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def _wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_cover(title, tool_name, out_path):
    W = H = 1200
    img = Image.new("RGB", (W, H), GREEN)
    d = ImageDraw.Draw(img)
    # brand row
    d.rounded_rectangle((80, 80, 170, 170), radius=18, fill=GOLD)
    d.text((125, 125), "R", font=_font("DejaVuSerif-Bold.ttf", 64), fill=DARK, anchor="mm")
    d.text((195, 125), "Retirement Plan Karo", font=_font("DejaVuSans-Bold.ttf", 44), fill=WHITE, anchor="lm")
    # title: largest size that fits in the box
    box_w, box_top, box_bottom = W - 160, 250, 880
    for size in range(96, 40, -4):
        f = _font("DejaVuSans-Bold.ttf", size)
        lines = _wrap(d, title, f, box_w)
        lh = int(size * 1.22)
        if lh * len(lines) <= box_bottom - box_top:
            break
    y = box_top + ((box_bottom - box_top) - lh * len(lines)) // 2
    for ln in lines:
        d.text((80, y), ln, font=f, fill=WHITE)
        y += lh
    d.rectangle((80, 905, 260, 913), fill=GOLD)
    if tool_name:
        d.text((80, 950), f"{tool_name}  →  retirementplankaro.com",
               font=_font("DejaVuSans-Bold.ttf", 36), fill=GOLD)
    d.rectangle((0, H - 110, W, H), fill=DARK)
    d.text((W // 2, H - 55), "Padhein: blog.retirementplankaro.com", font=_font("DejaVuSans.ttf", 36),
           fill=WHITE, anchor="mm")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=88)

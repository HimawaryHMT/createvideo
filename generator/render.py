import os
import shutil
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1440
FPS = 30
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

FADE_IN = 0.35
FADE_OUT = 0.30
CROSSFADE = 0.35
DRIFT_Y = 20

STYLES = {
    "question": {
        "en_color": (255, 255, 255),
        "vi_color": (232, 197, 122),
        "label": True,
    },
    "quote_dark": {
        "en_color": (255, 255, 255),
        "vi_color": (220, 220, 225),
        "label": True,
    },
    "quote_gold": {
        "en_color": (255, 248, 231),
        "vi_color": (255, 217, 138),
        "label": True,
    },
    "outro": {
        "en_color": (255, 255, 255),
        "vi_color": (255, 217, 138),
        "label": False,
    },
}


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    path = os.path.join(FONT_DIR, "BeVietnamPro-%s.ttf" % weight)
    if not os.path.exists(path):
        path = os.path.join(FONT_DIR, "BeVietnamPro-Regular.ttf")
    return ImageFont.truetype(path, size)


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if not cur or draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_text(draw, text, weight, start_size, max_width, max_height, min_size, line_height):
    size = start_size
    font = None
    lines = []
    while size > min_size:
        font = _font(weight, size)
        lines = wrap_text(draw, text, font, max_width)
        block_h = len(lines) * size * line_height
        if block_h <= max_height:
            return font, lines, block_h
        size -= 3
    font = _font(weight, min_size)
    lines = wrap_text(draw, text, font, max_width)
    return font, lines, len(lines) * min_size * line_height


def draw_text_alpha(base, xy, text, font, fill_rgb, alpha, anchor_center_x=None):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if anchor_center_x is not None:
        x = anchor_center_x - d.textlength(text, font=font) / 2
        xy = (x, xy[1])
    d.text(xy, text, font=font, fill=(*fill_rgb, int(alpha)))
    base.alpha_composite(layer)


def draw_dark_card(base, alpha):
    """Vẽ một lớp thẻ tối mờ bán trong suốt (glassmorphic dark box) để bảo đảm chữ luôn nổi bật trên bất kỳ video nền nào."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    card_alpha = int(140 * (alpha / 255.0))
    # Bo góc thẻ giữa màn hình
    margin_x = 70
    card_w = W - margin_x * 2
    card_h = 760
    card_y = (H - card_h) // 2
    d.rounded_rectangle(
        [margin_x, card_y, margin_x + card_w, card_y + card_h],
        radius=36,
        fill=(15, 20, 28, card_alpha),
        outline=(255, 255, 255, int(30 * (alpha / 255.0))),
        width=2
    )
    base.alpha_composite(layer)


def _scene_alpha(t_rel, dur):
    a = 255.0
    if t_rel < FADE_IN:
        a *= t_rel / FADE_IN
    if t_rel > dur - FADE_OUT:
        a *= max(0.0, (dur - t_rel) / FADE_OUT)
    return max(0, min(255, int(a)))


def _scene_drift(t_rel, dur):
    p = min(1.0, max(0.0, t_rel / max(dur, 0.001)))
    return int((1.0 - p) * DRIFT_Y * 0.9 - DRIFT_Y * 0.45)


def render_block_text(block, t_rel, dur, base):
    s = STYLES.get(block["style"], STYLES["quote_dark"])
    alpha = _scene_alpha(t_rel, dur)
    if alpha <= 0:
        return
    drift = _scene_drift(t_rel, dur)
    draw = ImageDraw.Draw(base)
    style = block["style"]

    # Vẽ dark card mờ phía sau để chữ nét đẹp và cân đối
    draw_dark_card(base, alpha)

    if style == "outro":
        en_font = _font("Black", 76)
        vi_font = _font("SemiBold", 44)
        en_lines = wrap_text(draw, block["en"], en_font, W - 220)
        vi_lines = wrap_text(draw, block["vi"], vi_font, W - 280)
        en_h = len(en_lines) * 76 * 1.2
        vi_h = len(vi_lines) * 44 * 1.35
        total_h = en_h + 50 + vi_h
        y = (H - total_h) / 2 + drift
        for line in en_lines:
            draw_text_alpha(base, (0, y), line, en_font, s["en_color"], alpha, W / 2)
            y += 76 * 1.2
        y += 50
        for line in vi_lines:
            draw_text_alpha(base, (0, y), line, vi_font, s["vi_color"], alpha, W / 2)
            y += 44 * 1.35
        return

    if s.get("label"):
        label_font = _font("Bold", 26)
        label = "TIẾNG ANH GIAO TIẾP"
        draw_text_alpha(base, (0, (H - 760) // 2 + 50 + drift), label, label_font, (232, 197, 122), alpha, W / 2)

    if style == "question":
        en_font = _font("ExtraBold", 68)
        vi_font = _font("SemiBold", 44)
        en_lines = wrap_text(draw, block["en"], en_font, W - 220)
        vi_lines = wrap_text(draw, block["vi"], vi_font, W - 280)
        en_h = len(en_lines) * 68 * 1.25
        vi_h = len(vi_lines) * 44 * 1.4
        total_h = en_h + 45 + vi_h
        y = (H - total_h) / 2 - 20 + drift
        for line in en_lines:
            draw_text_alpha(base, (0, y), line, en_font, s["en_color"], alpha, W / 2)
            y += 68 * 1.25
        y += 45
        for line in vi_lines:
            draw_text_alpha(base, (0, y), line, vi_font, s["vi_color"], alpha, W / 2)
            y += 44 * 1.4
        return

    en_font, en_lines, en_h = fit_text(draw, block["en"], "ExtraBold", 66, W - 220, 360, 36, 1.25)
    vi_font, vi_lines, vi_h = fit_text(draw, block["vi"], "Medium", 42, W - 280, 240, 28, 1.4)
    gap = 45
    total_h = en_h + gap + vi_h
    y = (H - total_h) / 2 - 10 + drift
    for line in en_lines:
        draw_text_alpha(base, (0, y), line, en_font, s["en_color"], alpha, W / 2)
        y += en_font.size * 1.25
    y += gap
    for line in vi_lines:
        draw_text_alpha(base, (0, y), line, vi_font, s["vi_color"], alpha, W / 2)
        y += vi_font.size * 1.4


def render(scenes, outro, frame_dir):
    if os.path.exists(frame_dir):
        shutil.rmtree(frame_dir)
    os.makedirs(frame_dir, exist_ok=True)
    blocks = scenes + [outro]
    n_blocks = len(blocks)
    total = blocks[-1]["end"]
    n_frames = int(total * FPS)
    for i in range(n_frames):
        t = i / FPS
        idx = None
        for j, b in enumerate(blocks):
            if b["start"] <= t < b["end"]:
                idx = j
                break
        if idx is None:
            idx = n_blocks - 1
        base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        t_rel = t - blocks[idx]["start"]
        render_block_text(blocks[idx], t_rel, blocks[idx]["end"] - blocks[idx]["start"], base)
        base.save(os.path.join(frame_dir, "frame_%05d.png" % i))
    return total


import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1440
FPS = 30
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

FADE_IN = 0.35
FADE_OUT = 0.30
CROSSFADE = 0.35
DRIFT_Y = 26

STYLES = {
    "question": {
        "top": (26, 18, 12),
        "bottom": (51, 39, 26),
        "en_color": (255, 255, 255),
        "vi_color": (232, 197, 122),
        "label": True,
    },
    "quote_dark": {
        "top": (46, 47, 53),
        "bottom": (78, 80, 88),
        "en_color": (255, 255, 255),
        "vi_color": (217, 217, 222),
        "label": True,
    },
    "quote_gold": {
        "top": (107, 79, 30),
        "bottom": (169, 131, 58),
        "en_color": (255, 248, 231),
        "vi_color": (255, 217, 138),
        "label": True,
    },
    "outro": {
        "top": (250, 250, 250),
        "bottom": (236, 234, 228),
        "en_color": (20, 20, 20),
        "vi_color": (138, 106, 31),
        "label": False,
    },
}


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    path = os.path.join(FONT_DIR, "BeVietnamPro-%s.ttf" % weight)
    if not os.path.exists(path):
        path = os.path.join(FONT_DIR, "BeVietnamPro-Regular.ttf")
    return ImageFont.truetype(path, size)


def make_gradient(top_rgb, bottom_rgb):
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(top_rgb[i] + (bottom_rgb[i] - top_rgb[i]) * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=c)
    return img


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
        size -= 4
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


def render_block_gradient(block):
    s = STYLES[block["style"]]
    return make_gradient(s["top"], s["bottom"])


def render_block_text(block, t_rel, dur, base, prev_grad):
    s = STYLES[block["style"]]
    alpha = _scene_alpha(t_rel, dur)
    if alpha <= 0:
        return
    drift = _scene_drift(t_rel, dur)
    draw = ImageDraw.Draw(base)
    style = block["style"]

    if style == "outro":
        en_font = _font("Black", 118)
        vi_font = _font("SemiBold", 64)
        en_lines = wrap_text(draw, block["en"], en_font, W - 160)
        vi_lines = wrap_text(draw, block["vi"], vi_font, W - 240)
        en_h = len(en_lines) * 118 * 1.2
        vi_h = len(vi_lines) * 64 * 1.35
        total_h = en_h + 70 + vi_h
        y = (H - total_h) / 2 + drift
        for line in en_lines:
            draw_text_alpha(base, (0, y), line, en_font, s["en_color"], alpha, W / 2)
            y += 118 * 1.2
        y += 70
        for line in vi_lines:
            draw_text_alpha(base, (0, y), line, vi_font, s["vi_color"], alpha, W / 2)
            y += 64 * 1.35
        return

    if s["label"]:
        label_font = _font("Medium", 34)
        label = "TIẾNG ANH GIAO TIẾP"
        draw_text_alpha(base, (0, 150 + drift), label, label_font, (201, 160, 74), alpha, W / 2)

    if style == "question":
        en_font = _font("ExtraBold", 96)
        vi_font = _font("SemiBold", 60)
        en_lines = wrap_text(draw, block["en"], en_font, W - 140)
        vi_lines = wrap_text(draw, block["vi"], vi_font, W - 220)
        en_h = len(en_lines) * 96 * 1.25
        vi_h = len(vi_lines) * 60 * 1.4
        total_h = en_h + 60 + vi_h
        y = (H - total_h) / 2 - 60 + drift
        for line in en_lines:
            draw_text_alpha(base, (0, y), line, en_font, s["en_color"], alpha, W / 2)
            y += 96 * 1.25
        y += 60
        for line in vi_lines:
            draw_text_alpha(base, (0, y), line, vi_font, s["vi_color"], alpha, W / 2)
            y += 60 * 1.4
        return

    en_font, en_lines, en_h = fit_text(draw, block["en"], "ExtraBold", 92, W - 150, 480, 48, 1.25)
    vi_font, vi_lines, vi_h = fit_text(draw, block["vi"], "Medium", 56, W - 230, 330, 36, 1.4)
    gap = 70
    total_h = en_h + gap + vi_h
    y = (H - total_h) / 2 - 40 + drift
    for line in en_lines:
        draw_text_alpha(base, (0, y), line, en_font, s["en_color"], alpha, W / 2)
        y += en_font.size * 1.25
    y += gap
    for line in vi_lines:
        draw_text_alpha(base, (0, y), line, vi_font, s["vi_color"], alpha, W / 2)
        y += vi_font.size * 1.4


def render(scenes, outro, frame_dir):
    os.makedirs(frame_dir, exist_ok=True)
    gradients = [render_block_gradient(sc) for sc in scenes] + [render_block_gradient(outro)]
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
        base = gradients[idx].convert("RGBA")
        if idx > 0 and t < blocks[idx]["start"] + CROSSFADE:
            p = (t - blocks[idx]["start"]) / CROSSFADE
            base = Image.blend(gradients[idx - 1], gradients[idx], p).convert("RGBA")
        t_rel = t - blocks[idx]["start"]
        render_block_text(blocks[idx], t_rel, blocks[idx]["end"] - blocks[idx]["start"], base, None)
        base.convert("RGB").save(os.path.join(frame_dir, "frame_%05d.png" % i))
    return total

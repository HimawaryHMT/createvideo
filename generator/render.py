import os
import shutil
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
S = 2  # 2x Supersampling for ultra-crisp anti-aliasing
W_S, H_S = W * S, H * S

FPS = 30
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

FADE_IN = 0.35
FADE_OUT = 0.30
CROSSFADE = 0.35
DRIFT_Y = 24 * S

STYLES = {
    "question": {
        "en_color": (255, 255, 255),
        "vi_color": (232, 197, 122),
        "label": True,
    },
    "quote_dark": {
        "en_color": (255, 255, 255),
        "vi_color": (225, 228, 235),
        "label": True,
    },
    "quote_gold": {
        "en_color": (255, 250, 235),
        "vi_color": (255, 218, 140),
        "label": True,
    },
    "outro": {
        "en_color": (255, 255, 255),
        "vi_color": (255, 218, 140),
        "label": False,
    },
}


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    path = os.path.join(FONT_DIR, "BeVietnamPro-%s.ttf" % weight)
    if not os.path.exists(path):
        path = os.path.join(FONT_DIR, "BeVietnamPro-Regular.ttf")
    return ImageFont.truetype(path, size * S)


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
        block_h = len(lines) * (size * S) * line_height
        if block_h <= max_height:
            return font, lines, block_h, size
        size -= 2
    font = _font(weight, min_size)
    lines = wrap_text(draw, text, font, max_width)
    return font, lines, len(lines) * (min_size * S) * line_height, min_size


def draw_text_alpha(base, xy, text, font, fill_rgb, alpha, anchor_center_x=None, shadow=True):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = xy
    if anchor_center_x is not None:
        x = anchor_center_x - d.textlength(text, font=font) / 2
        xy = (x, y)

    # Subtle text drop shadow for cinematic depth & clarity
    if shadow and alpha > 30:
        shadow_alpha = int(alpha * 0.45)
        d.text((x + 2 * S, y + 3 * S), text, font=font, fill=(0, 0, 0, shadow_alpha))

    d.text(xy, text, font=font, fill=(*fill_rgb, int(alpha)))
    base.alpha_composite(layer)


def draw_dark_card(base, alpha, has_badge=True):
    """Vẽ một lớp thẻ glassmorphic siêu nét với viền tinh tế và badge."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    card_alpha = int(165 * (alpha / 255.0))
    border_alpha = int(45 * (alpha / 255.0))

    margin_x = 64 * S
    card_w = W_S - margin_x * 2
    card_h = 1080 * S
    card_y = (H_S - card_h) // 2

    # Card nền tối bán trong suốt
    d.rounded_rectangle(
        [margin_x, card_y, margin_x + card_w, card_y + card_h],
        radius=44 * S,
        fill=(10, 14, 22, card_alpha),
        outline=(255, 255, 255, border_alpha),
        width=3 * S
    )

    # Pill badge phía trên nếu có
    if has_badge and alpha > 20:
        badge_text = "TIẾNG ANH GIAO TIẾP"
        badge_font = _font("Bold", 24)
        text_w = d.textlength(badge_text, font=badge_font)
        pill_pad_x = 28 * S
        pill_pad_y = 12 * S
        pill_w = text_w + pill_pad_x * 2
        pill_h = 24 * S + pill_pad_y * 2
        pill_x = (W_S - pill_w) // 2
        pill_y = card_y + 48 * S

        d.rounded_rectangle(
            [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
            radius=20 * S,
            fill=(232, 197, 122, int(35 * (alpha / 255.0))),
            outline=(232, 197, 122, int(100 * (alpha / 255.0))),
            width=2 * S
        )
        d.text((pill_x + pill_pad_x, pill_y + pill_pad_y - 2 * S), badge_text, font=badge_font, fill=(232, 197, 122, int(alpha)))

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
    return int((1.0 - p) * DRIFT_Y * 0.85 - DRIFT_Y * 0.42)


def render_block_text(block, t_rel, dur, base_hires):
    s = STYLES.get(block["style"], STYLES["quote_dark"])
    alpha = _scene_alpha(t_rel, dur)
    if alpha <= 0:
        return
    drift = _scene_drift(t_rel, dur)
    draw = ImageDraw.Draw(base_hires)
    style = block["style"]

    has_badge = s.get("label", True)
    draw_dark_card(base_hires, alpha, has_badge=has_badge)

    max_text_w = W_S - 240 * S
    card_h = 1080 * S
    card_y = (H_S - card_h) // 2
    content_center_y = card_y + (card_h // 2) + (35 * S if has_badge else 0)

    if style == "outro":
        en_font = _font("Black", 80)
        vi_font = _font("SemiBold", 46)
        en_lines = wrap_text(draw, block["en"], en_font, max_text_w)
        vi_lines = wrap_text(draw, block["vi"], vi_font, max_text_w - 80 * S)
        en_h = len(en_lines) * (80 * S) * 1.25
        vi_h = len(vi_lines) * (46 * S) * 1.4
        gap = 55 * S
        total_h = en_h + gap + vi_h
        y = content_center_y - (total_h / 2) + drift

        for line in en_lines:
            draw_text_alpha(base_hires, (0, y), line, en_font, s["en_color"], alpha, W_S / 2)
            y += (80 * S) * 1.25
        y += gap
        for line in vi_lines:
            draw_text_alpha(base_hires, (0, y), line, vi_font, s["vi_color"], alpha, W_S / 2)
            y += (46 * S) * 1.4
        return

    if style == "question":
        en_font, en_lines, en_h, _ = fit_text(draw, block["en"], "ExtraBold", 68, max_text_w, 420 * S, 40, 1.28)
        vi_font, vi_lines, vi_h, _ = fit_text(draw, block["vi"], "SemiBold", 46, max_text_w - 60 * S, 280 * S, 32, 1.42)
        gap = 50 * S
        total_h = en_h + gap + vi_h
        y = content_center_y - (total_h / 2) + drift

        for line in en_lines:
            draw_text_alpha(base_hires, (0, y), line, en_font, s["en_color"], alpha, W_S / 2)
            y += en_font.size * 1.28
        y += gap
        for line in vi_lines:
            draw_text_alpha(base_hires, (0, y), line, vi_font, s["vi_color"], alpha, W_S / 2)
            y += vi_font.size * 1.42
        return

    en_font, en_lines, en_h, _ = fit_text(draw, block["en"], "ExtraBold", 68, max_text_w, 450 * S, 38, 1.28)
    vi_font, vi_lines, vi_h, _ = fit_text(draw, block["vi"], "Medium", 44, max_text_w - 60 * S, 300 * S, 30, 1.42)
    gap = 50 * S
    total_h = en_h + gap + vi_h
    y = content_center_y - (total_h / 2) + drift

    for line in en_lines:
        draw_text_alpha(base_hires, (0, y), line, en_font, s["en_color"], alpha, W_S / 2)
        y += en_font.size * 1.28
    y += gap
    for line in vi_lines:
        draw_text_alpha(base_hires, (0, y), line, vi_font, s["vi_color"], alpha, W_S / 2)
        y += vi_font.size * 1.42


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

        # 1. Khởi tạo canvas độ phân giải cao 2x
        base_hires = Image.new("RGBA", (W_S, H_S), (0, 0, 0, 0))
        t_rel = t - blocks[idx]["start"]
        render_block_text(blocks[idx], t_rel, blocks[idx]["end"] - blocks[idx]["start"], base_hires)

        # 2. Downsample với Lanczos filter tạo chất lượng siêu nét không răng cưa
        frame_final = base_hires.resize((W, H), resample=Image.Resampling.LANCZOS)
        frame_final.save(os.path.join(frame_dir, "frame_%05d.png" % i))

    return total

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


def draw_karaoke_lines(base, start_y, lines, font, normal_rgb, alpha, word_timings=None, t_voice=None, line_spacing=1.28):
    """Ve text tieng Anh voi hieu ung Karaoke Word-by-Word Highlight ruc sang."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    active_idx = -1
    if word_timings and t_voice is not None and t_voice >= 0:
        for idx, w in enumerate(word_timings):
            w_start = w.get("offset_s", 0.0)
            w_dur = w.get("dur_s", 0.0)
            if w_start <= t_voice < (w_start + w_dur + 0.08):
                active_idx = idx
                break
            elif t_voice >= (w_start + w_dur):
                active_idx = idx

    space_w = d.textlength(" ", font=font)
    line_h = font.size * line_spacing
    cur_y = start_y
    global_word_idx = 0

    for line in lines:
        words = line.split()
        if not words:
            cur_y += line_h
            continue
        word_lens = [d.textlength(w, font=font) for w in words]
        line_w = sum(word_lens) + space_w * (len(words) - 1)
        cur_x = (W_S - line_w) / 2

        for i, w in enumerate(words):
            w_len = word_lens[i]
            is_active = (global_word_idx == active_idx and active_idx != -1)
            is_past = (global_word_idx < active_idx and active_idx != -1)

            # Drop shadow
            if alpha > 30:
                shadow_alpha = int(alpha * (0.6 if is_active else 0.42))
                d.text((cur_x + 2 * S, cur_y + 3 * S), w, font=font, fill=(0, 0, 0, shadow_alpha))

            if is_active:
                # Pill highlight badge ruc ro phia sau tu dang phat am
                pad_x = 10 * S
                pad_y = 6 * S
                pill_alpha = int(90 * (alpha / 255.0))
                border_alpha = int(220 * (alpha / 255.0))
                d.rounded_rectangle(
                    [cur_x - pad_x, cur_y - pad_y, cur_x + w_len + pad_x, cur_y + font.size + pad_y],
                    radius=12 * S,
                    fill=(232, 197, 122, pill_alpha),
                    width=2 * S
                )
                # Text vang neon phat sang
                d.text((cur_x, cur_y), w, font=font, fill=(255, 235, 60, int(alpha)))
            elif is_past:
                # Tu da doc: trang tinh net
                d.text((cur_x, cur_y), w, font=font, fill=(*normal_rgb, int(alpha)))
            else:
                # Tu sap doc: trang diu nhe
                dimmed_alpha = int(alpha * (0.85 if active_idx != -1 else 1.0))
                d.text((cur_x, cur_y), w, font=font, fill=(*normal_rgb, dimmed_alpha))

            cur_x += w_len + space_w
            global_word_idx += 1

        cur_y += line_h

    base.alpha_composite(layer)


def draw_dark_card(base, alpha, has_badge=True):
    """Ve mot lop the glassmorphic sieu net voi vien tinh te va badge."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    card_alpha = int(165 * (alpha / 255.0))
    border_alpha = int(45 * (alpha / 255.0))

    margin_x = 64 * S
    card_w = W_S - margin_x * 2
    card_h = 1080 * S
    card_y = (H_S - card_h) // 2

    # Card nen toi ban trong suot
    d.rounded_rectangle(
        [margin_x, card_y, margin_x + card_w, card_y + card_h],
        radius=44 * S,
        fill=(10, 14, 22, card_alpha),
        outline=(255, 255, 255, border_alpha),
        width=3 * S
    )

    # Pill badge phia tren neu co
    if has_badge and alpha > 20:
        badge_text = "TIÂ!NG ANH GIAO TIỎP"
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

    # Tinh toan thoi diem giong noi dang phat de highlight Karaoke
    voice_at_scene = block.get("voice_at", block["start"]) - block["start"]
    t_voice = t_rel - voice_at_scene
    word_timings = block.get("word_timings", [])

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

        # Karaoke Highlight cho cau tieng Anh
        draw_karaoke_lines(base_hires, y, en_lines, en_font, s["en_color"], alpha, word_timings=word_timings, t_voice=t_voice, line_spacing=1.28)
        y += en_h + gap

        for line in vi_lines:
            draw_text_alpha(base_hires, (0, y), line, vi_font, s["vi_color"], alpha, W_S / 2)
            y += vi_font.size * 1.42
        return

    en_font, en_lines, en_h, _ = fit_text(draw, block["en"], "ExtraBold", 68, max_text_w, 450 * S, 38, 1.28)
    vi_font, vi_lines, vi_h, _ = fit_text(draw, block["vi"], "Medium", 44, max_text_w - 60 * S, 300 * S, 30, 1.42)
    gap = 50 * S
    total_h = en_h + gap + vi_h
    y = content_center_y - (total_h / 2) + drift

    # Karaoke Highlight cho cau tieng Anh
    draw_karaoke_lines(base_hires, y, en_lines, en_font, s["en_color"], alpha, word_timings=word_timings, t_voice=t_voice, line_spacing=1.28)
    y += en_h + gap

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

        # 1. Khoi tao canvas do phan giai cao 2x
        base_hires = Image.new("RGBA", (W_S, H_S), (0, 0, 0, 0))
        t_rel = t - blocks[idx]["start"]
        render_block_text(blocks[idx], t_rel, blocks[idx]["end"] - blocks[idx]["start"], base_hires)

        # 2. Downsample voi Lanczos filter tao chat luong sieu net khong rang cua
        frame_final = base_hires.resize((W, H), resample=Image.Resampling.LANCZOS)
        frame_final.save(os.path.join(frame_dir, "frame_%05d.png" % i))

    return total

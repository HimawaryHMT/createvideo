import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time

from generator import tts, render, assemble, background

sys.stdout.reconfigure(encoding="utf-8")

PAD_BEFORE = 0.35
PAD_AFTER = 0.55
MIN_SCENE = 2.8
OUTRO_DUR = 2.2
FPS = 30
DEFAULT_VOICE = "en-US-ChristopherNeural"


def slug(text):
    return re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-") or "video"


def tts_cache_name(index, voice, text):
    key = hashlib.md5((voice + "|" + text).encode("utf-8")).hexdigest()[:10]
    return "tts_%02d_%s" % (index, key)


def main():
    parser = argparse.ArgumentParser(description="Tao video TikTok kieu Tieng Anh giao tiep")
    parser.add_argument("input", nargs="?", default="input.json")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--work-dir", default="work")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    scenes = data["scenes"]
    if not scenes:
        raise SystemExit("input.json: can it nhat 1 scene")

    voice = data.get("voice", DEFAULT_VOICE)
    word = data.get("word", "")
    word_vi = data.get("word_vi", "")
    caption = data.get("caption", "")
    hashtags = data.get("hashtags", "")
    bg_query = data.get("bg_query", "")

    os.makedirs(args.work_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)

    print("[1/5] Lay video phong nen background (Coverr/Pexels)...")
    bg_seed = "%s|%s" % (word, bg_query)
    bg_video_path = background.get_background_video(args.work_dir, query=bg_query, seed=bg_seed)

    print("[2/5] Tao giong doc (edge-tts)...")
    wavs = []
    durations = []
    for i, sc in enumerate(scenes):
        base = tts_cache_name(i, voice, sc["en"])
        mp3 = os.path.join(args.work_dir, base + ".mp3")
        if not os.path.exists(mp3) or os.path.getsize(mp3) == 0:
            tts.synth(sc["en"], voice, mp3)
        wav = assemble.mp3_to_wav(mp3, os.path.join(args.work_dir, base + ".wav"))
        durations.append(assemble.get_duration(wav))
        wavs.append(wav)
        print("    scene %d: '%.40s' %.2fs" % (i + 1, sc["en"], durations[i]))

    blocks = []
    t = 0.0
    for i, sc in enumerate(scenes):
        dur = max(durations[i] + PAD_BEFORE + PAD_AFTER, MIN_SCENE)
        blocks.append({
            "style": sc.get("style", "quote_dark" if i % 2 == 0 else "quote_gold"),
            "en": sc["en"],
            "vi": sc.get("vi", ""),
            "start": t,
            "end": t + dur,
            "voice_at": t + PAD_BEFORE,
            "voice_wav": wavs[i],
        })
        print("    timeline scene %d: %.2f -> %.2f (voice at %.2f)" % (i + 1, t, t + dur, t + PAD_BEFORE))
        t += dur

    outro = {
        "style": "outro",
        "en": word or scenes[0]["en"],
        "vi": word_vi,
        "start": t,
        "end": t + OUTRO_DUR,
    }
    total = outro["end"]
    print("[3/5] Render %d frames (%.1fs)..." % (int(total * FPS), total))
    frame_dir = os.path.join(args.work_dir, "frames")
    render.render(blocks, outro, frame_dir)

    print("[4/5] Ghep audio...")
    audio_wav = os.path.join(args.work_dir, "audio.wav")
    items = [(b["voice_wav"], b["voice_at"]) for b in blocks]
    assemble.build_audio(items, total, audio_wav)

    print("[5/5] Encode MP4 voi video background...")
    out_path = os.path.join(args.output_dir, "%s_%d.mp4" % (slug(word), int(time.time())))
    assemble.encode_video(frame_dir, audio_wav, out_path, FPS, bg_video_path=bg_video_path, duration=total)


    if not args.keep_work:
        shutil.rmtree(frame_dir, ignore_errors=True)
        for i, sc in enumerate(scenes):
            p = os.path.join(args.work_dir, tts_cache_name(i, voice, sc["en"]) + ".wav")
            if os.path.exists(p):
                os.remove(p)
        if os.path.exists(audio_wav):
            os.remove(audio_wav)

    print()
    print("Video da tao xong: %s" % out_path)
    print("Do dai: %.1f giay | 1080x1440 | 30fps" % total)
    full_caption = " ".join(x for x in [caption, hashtags] if x)
    if full_caption:
        print("Caption dang TikTok:")
        print(full_caption)


if __name__ == "__main__":
    main()

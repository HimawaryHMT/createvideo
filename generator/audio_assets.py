import os
import math
import wave
import struct
import random
import urllib.request

SR = 48000
CH = 2
SW = 2

LOFI_MUSIC_URLS = [
    "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=lofi-study-112191.mp3",
    "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3?filename=chill-abstract-intention-12099.mp3",
]


def ensure_sfx(work_dir: str) -> dict:
    """Tao hoac lay file hieu ung am thanh (SFX) chuan 48kHz stereo."""
    os.makedirs(work_dir, exist_ok=True)
    whoosh_path = os.path.join(work_dir, "sfx_whoosh.wav")
    pop_path = os.path.join(work_dir, "sfx_pop.wav")

    if not os.path.exists(whoosh_path) or os.path.getsize(whoosh_path) == 0:
        _generate_whoosh(whoosh_path)
    if not os.path.exists(pop_path) or os.path.getsize(pop_path) == 0:
        _generate_pop(pop_path)

    return {
        "whoosh": whoosh_path,
        "pop": pop_path,
    }


def _generate_whoosh(filename: str, dur: float = 0.32):
    """Tao am thanh Whoosh luot gio muot ma cho chuyen canh."""
    n_samples = int(dur * SR)
    with wave.open(filename, "wb") as w:
        w.setnchannels(CH)
        w.setsampwidth(SW)
        w.setframerate(SR)
        frames = bytearray()
        for i in range(n_samples):
            t = i / SR
            p = i / n_samples
            env = (math.sin(math.pi * p) ** 2)
            freq = 300.0 + 1000.0 * math.sin(math.pi * p)
            noise = (random.random() * 2.0 - 1.0)
            tone = math.sin(2.0 * math.pi * freq * t)
            sig = (tone * 0.35 + noise * 0.65) * env * 0.38
            val = int(max(-1.0, min(1.0, sig)) * 32767)
            frames.extend(struct.pack("<hh", val, val))
        w.writeframes(frames)


def _generate_pop(filename: str, dur: float = 0.18):
    """Tao am thanh Pop/Ding nhe nhang khi tu khoa hoac the xuat hien."""
    n_samples = int(dur * SR)
    with wave.open(filename, "wb") as w:
        w.setnchannels(CH)
        w.setsampwidth(SW)
        w.setframerate(SR)
        frames = bytearray()
        for i in range(n_samples):
            t = i / SR
            env = math.exp(-22.0 * t)
            freq = 480.0 + 320.0 * math.exp(-35.0 * t)
            harm = math.sin(2.0 * math.pi * (freq * 2.0) * t) * 0.25
            fund = math.sin(2.0 * math.pi * freq * t) * 0.75
            sig = (fund + harm) * env * 0.5
            val = int(max(-1.0, min(1.0, sig)) * 32767)
            frames.extend(struct.pack("<hh", val, val))
        w.writeframes(frames)


def get_lofi_bgm(work_dir: str) -> str:
    """Tai va luu cache 1 track nhac Lofi chill nhe nhang."""
    os.makedirs(work_dir, exist_ok=True)
    bgm_path = os.path.join(work_dir, "lofi_bgm.mp3")
    if os.path.exists(bgm_path) and os.path.getsize(bgm_path) > 100000:
        return bgm_path

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    for url in LOFI_MUSIC_URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp, open(bgm_path, "wb") as f:
                f.write(resp.read())
            if os.path.exists(bgm_path) and os.path.getsize(bgm_path) > 100000:
                print("    [BGM] Tai thanh cong nhac nen Lofi: %s" % bgm_path)
                return bgm_path
        except Exception as e:
            print("    [BGM] Khong tai duoc %s (%s), thu link tiep theo..." % (url, e))

    return ""

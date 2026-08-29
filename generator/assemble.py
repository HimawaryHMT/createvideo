import os
import shutil
import subprocess
import wave
from array import array

SR = 48000
CH = 2
SW = 2

_KNOWN_DIRS = [
    r"C:\Users\huynh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.WinGet.Source_8wekyb3e8bbwe\ffmpeg-9.0-full_build\bin",
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"),
    r"C:\ffmpeg\bin",
]


def _find_exe(name):
    exe = shutil.which(name)
    if exe:
        return exe
    for d in _KNOWN_DIRS:
        if os.path.isdir(d):
            for root, _, files in os.walk(d):
                if name + ".exe" in files:
                    return os.path.join(root, name + ".exe")
    return name


def ffmpeg():
    return _find_exe("ffmpeg")


def ffprobe():
    return _find_exe("ffprobe")


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "Command failed (%d): %s\nis\n+%s"
            % (proc.returncode, " ".join(cmd), proc.stdout[-2000:], proc.stderr[-2000:])
        )


def mp3_to_wav(mp3_path, wav_path):
    run([ffmpeg(), "-y", "-v", "error", "-i", mp3_path, "-ac", str(CH), "-ar", str(SR), "-acodec", "pcm_s16le", wav_path])
    return wav_path


def get_duration(wav_path):
    out = subprocess.run(
        [ffprobe(), "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", wav_path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def build_audio(items, total_dur, out_wav, sfx_items=None):
    """Ghep cac doan giong doc +SFX chuyen canh vao dung moc thoi gian."""
    total_samples = int(total_dur * SR)
    buf = array("h", [0]) * (total_samples * CH)
    all_items = list(items) + list(sfx_items or [])

    for wav_path, offset in all_items:
        if not wav_path or not os.path.exists(wav_path):
            continue
        with wave.open(wav_path, "rb") as w:
            if w.getframerate() != SR or w.getnchannels() != CH or w.getsampwidth() != SW:
                continue
            data = array("h")
            data.frombytes(w.readframes(w.getnframes()))
        start = int(offset * SR) * CH

        n = min(len(data), total_samples * CH - start)
        for k in range(n):
            idx = start + k
            mixed = buf[idx] + data[k]
            buf[idx] = max(-32768, min(32767, mixed))

    with wave.open(out_wav, "wb") as w:
        w.setnchannels(CH)
        w.setsampwidth(SW)
        w.setframerate(SR)
        w.writeframes(buf.tobytes())
    return out_wav


def encode_video(frame_dir, audio_wav, out_mp4, fps=30, bg_video_path=None, duration=None, bgm_path=None):
    """Ma hoa video Full HD 1080x1920 sac net cao + BGM Lofi chill + SFX."""
    has_bgm = bool(bgm_path and os.path.exists(bgm_path))

    if bg_video_path and os.path.exists(bg_video_path):
        video_filter = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos+accurate_rnd,"
            "crop=1080:1920,"
            "eq=brightness=-0.05:contrast=1.08:saturation=1.12,"
            "unsharp=3:3:0.5:3:3:0.0,"
            "fps=%d[scaled_bg];"
            "[scaled_bg][1:v]overlay=0:0:format=auto[v]"
        ) % fps

        cmd = [
            ffmpeg(), "-y", "-v", "error",
            "-stream_loop", "-1",
            "-i", bg_video_path,
            "-framerate", str(fps),
            "-i", os.path.join(frame_dir, "frame_%05d.png"),
            "-i", audio_wav,
        ]

        if has_bgm:
            cmd += ["-stream_loop", "-1", "-i", bgm_path]
            fade_st = max(0.0, (duration - 1.5) if duration else 10.0)
            audio_filter = (
                "[3:a]volume=0.18,afade=t=out:st=%.2f:d=1.5[bgm];"
                "[2:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            ) % fade_st
            filter_complex = video_filter + ";" + audio_filter
            audio_map = "[aout]"
        else:
            filter_complex = video_filter
            audio_map = "2:a"

        cmd += [
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", audio_map,
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "15",
            "-profile:v", "high",
            "-level", "4.2",
            "-pix_fmt", "yuv420p",
            "-colorspace", "bt709",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-color_range", "tv",
            "-b:v", "15M",
            "-maxrate", "22M",
            "-bufsize", "30M",
            "-c:a", "aac",
            "-b:a", "320k",
            "-ar", "48000",
            "-movflags", "+faststart",
        ]
        if duration:
            cmd += ["-t", str(duration)]
        cmd.append(out_mp4)
        run(cmd)
    else:
        cmd = [
            ffmpeg(), "-y", "-v", "error",
            "-framerate", str(fps),
            "-i", os.path.join(frame_dir, "frame_%05d.png"),
            "-i", audio_wav,
        ]
        if has_bgm:
            cmd += ["-stream_loop", "-1", "-i", bgm_path]
            fade_st = max(0.0, (duration - 1.5) if duration else 10.0)
            audio_filter = (
                "[2:a]volume=0.18,afade=t=out:st=%.2f:d=1.5[bgm];"
                "[1:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            ) % fade_st
            cmd += ["-filter_complex", audio_filter, "-map", "0:v", "-map", "[aout]"]
        else:
            cmd += ["-map", "0:v", "-map", "1:a"]

        cmd += [
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "15",
            "-profile:v", "high",
            "-level", "4.2",
            "-pix_fmt", "yuv420p",
            "-colorspace", "bt709",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-color_range", "tv",
            "-b:v", "15M",
            "-maxrate", "22M",
            "-bufsize", "30M",
            "-c:a", "aac",
            "-b:a", "320k",
            "-ar", "48000",
            "-movflags", "+faststart",
        ]
        if duration:
            cmd += ["-t", str(duration)]
        else:
            cmd += ["-shortest"]
        cmd.append(out_mp4)
        run(cmd)
    return out_mp4


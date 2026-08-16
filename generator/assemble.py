import os
import shutil
import subprocess
import wave
from array import array

SR = 44100
CH = 2
SW = 2

_KNOWN_DIRS = [
    r"C:\Users\huynh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin",
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
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def mp3_to_wav(mp3_path, wav_path):
    run([ffmpeg(), "-y", "-v", "error", "-i", mp3_path, "-ac", str(CH), "-ar", str(SR), "-acodec", "pcm_s16le", wav_path])
    return wav_path


def get_duration(wav_path):
    out = subprocess.run(
        [ffprobe(), "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", wav_path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def build_audio(items, total_dur, out_wav):
    total_samples = int(total_dur * SR)
    buf = array("h", [0]) * (total_samples * CH)
    for wav_path, offset in items:
        with wave.open(wav_path, "rb") as w:
            assert w.getframerate() == SR
            assert w.getnchannels() == CH
            assert w.getsampwidth() == SW
            data = array("h")
            data.frombytes(w.readframes(w.getnframes()))
        start = int(offset * SR) * CH
        n = min(len(data), total_samples * CH - start)
        if n > 0:
            buf[start:start + n] = data[:n]
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(CH)
        w.setsampwidth(SW)
        w.setframerate(SR)
        w.writeframes(buf.tobytes())
    return out_wav


def encode_video(frame_dir, audio_wav, out_mp4, fps=30):
    run([
        ffmpeg(), "-y", "-v", "error",
        "-framerate", str(fps),
        "-i", os.path.join(frame_dir, "frame_%05d.png"),
        "-i", audio_wav,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-shortest",
        out_mp4,
    ])
    return out_mp4

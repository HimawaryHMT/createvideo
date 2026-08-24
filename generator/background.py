import os
import random
import hashlib
import urllib.request
import urllib.parse
import re
import html
import subprocess
import json
import shutil

# Bộ sưu tập video Full HD 1080p phân loại theo chủ đề (Aesthetic & Relaxing Cinematic Backgrounds)
THEMED_STOCK_VIDEOS = {
    "coffee": [
        "https://assets.mixkit.co/videos/42581/42581-1080.mp4",
        "https://assets.mixkit.co/videos/4836/4836-1080.mp4",
    ],
    "nature": [
        "https://assets.mixkit.co/videos/1188/1188-1080.mp4",
        "https://assets.mixkit.co/videos/42416/42416-1080.mp4",
        "https://assets.mixkit.co/videos/42426/42426-1080.mp4",
    ],
    "sunset": [
        "https://assets.mixkit.co/videos/26070/26070-1080.mp4",
    ],
    "ocean": [
        "https://assets.mixkit.co/videos/5016/5016-1080.mp4",
    ],
    "study": [
        "https://assets.mixkit.co/videos/42777/42777-1080.mp4",
        "https://assets.mixkit.co/videos/34487/34487-1080.mp4",
        "https://assets.mixkit.co/videos/43529/43529-1080.mp4",
    ],
    "city": [
        "https://assets.mixkit.co/videos/41668/41668-1080.mp4",
        "https://assets.mixkit.co/videos/4028/4028-1080.mp4",
    ],
    "cozy": [
        "https://assets.mixkit.co/videos/42542/42542-1080.mp4",
        "https://assets.mixkit.co/videos/42540/42540-1080.mp4",
    ],
    "rain": [
        "https://assets.mixkit.co/videos/41459/41459-1080.mp4",
    ],
    "space": [
        "https://assets.mixkit.co/videos/1610/1610-1080.mp4",
        "https://assets.mixkit.co/videos/41270/41270-1080.mp4",
    ],
}

# Fallback collection gồm các video 1080p đa năng, đẹp mắt
FALLBACK_STOCK_VIDEOS = [
    "https://assets.mixkit.co/videos/42581/42581-1080.mp4",
    "https://assets.mixkit.co/videos/26070/26070-1080.mp4",
    "https://assets.mixkit.co/videos/42777/42777-1080.mp4",
    "https://assets.mixkit.co/videos/1188/1188-1080.mp4",
    "https://assets.mixkit.co/videos/42416/42416-1080.mp4",
    "https://assets.mixkit.co/videos/5016/5016-1080.mp4",
    "https://assets.mixkit.co/videos/34487/34487-1080.mp4",
    "https://assets.mixkit.co/videos/41668/41668-1080.mp4",
    "https://assets.mixkit.co/videos/42542/42542-1080.mp4",
    "https://assets.mixkit.co/videos/1610/1610-1080.mp4",
    "https://assets.mixkit.co/videos/41459/41459-1080.mp4",
    "https://assets.mixkit.co/videos/43529/43529-1080.mp4",
    "https://assets.mixkit.co/videos/42540/42540-1080.mp4",
]


def _find_ffprobe():
    exe = shutil.which("ffprobe")
    if exe:
        return exe
    known = [
        r"C:\Users\huynh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"),
        r"C:\ffmpeg\bin",
    ]
    for d in known:
        if os.path.isdir(d):
            for root, _, files in os.walk(d):
                if "ffprobe.exe" in files:
                    return os.path.join(root, "ffprobe.exe")
    return "ffprobe"


def check_video_quality(path, min_w=1280, min_h=720):
    """Kiểm tra video có đúng chuẩn HD/Full HD không bằng ffprobe."""
    try:
        cmd = [
            _find_ffprobe(), "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,codec_name",
            "-of", "json", path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        streams = data.get("streams", [])
        if not streams:
            return False, 0, 0
        w = int(streams[0].get("width", 0))
        h = int(streams[0].get("height", 0))
        # Cho phép cả video dọc (1080x1920 / 720x1280) lẫn video ngang (1920x1080 / 1280x720)
        is_hd = (w >= min_w and h >= min_h) or (w >= min_h and h >= min_w) or (w >= 1080 or h >= 1080)
        return is_hd, w, h
    except Exception as e:
        print("    [Background] ffprobe check loi: %s" % e)
        return False, 0, 0


def download_file(url, out_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "*/*",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response, open(out_path, "wb") as out_file:
        out_file.write(response.read())
    return out_path


def fetch_stock_videos_by_query(query="nature"):
    results = []
    if not query:
        return results

    q_lower = query.lower()
    # 1. Khớp từ khóa với bộ sưu tập 1080p theo chủ đề
    for key, urls in THEMED_STOCK_VIDEOS.items():
        if key in q_lower or q_lower in key:
            results.extend(urls)

    # 2. Khớp các từ đồng nghĩa thông dụng
    synonyms = {
        "conversation": ["study", "coffee", "city"],
        "talk": ["study", "coffee", "city"],
        "communication": ["study", "coffee"],
        "motivation": ["sunset", "nature", "space", "study"],
        "mindset": ["nature", "ocean", "space", "cozy"],
        "learn": ["study", "coffee"],
        "english": ["study", "coffee", "city"],
        "work": ["study", "coffee"],
        "peace": ["ocean", "nature", "cozy", "sunset"],
        "calm": ["ocean", "nature", "rain", "cozy"],
        "dark": ["space", "city", "cozy"],
    }
    for word, categories in synonyms.items():
        if word in q_lower:
            for cat in categories:
                if cat in THEMED_STOCK_VIDEOS:
                    results.extend(THEMED_STOCK_VIDEOS[cat])

    # 3. Cào bổ sung từ Coverr nếu có
    try:
        search_url = "https://coverr.co/s?q=%s" % urllib.parse.quote(query)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            page_html = resp.read().decode("utf-8", errors="ignore")
        matches = re.findall(r'https://[^\"]+?\.mp4[^\"]*', page_html)
        if matches:
            # Ưu tiên các link chứa 1080p hoặc 720p hoặc direct download
            hd_matches = [m for m in matches if ("1080" in m or "720" in m or "download" in m)]
            results.extend(hd_matches or matches)
    except Exception as e:
        print("    [Background] Khong tim duoc tren web voi '%s': %s" % (query, e))

    return results


def _build_pool(query):
    pool = []
    if query:
        pool.extend(fetch_stock_videos_by_query(query))
    pool.extend(FALLBACK_STOCK_VIDEOS)
    seen = set()
    uniq = []
    for u in pool:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def get_background_video(work_dir, query="", seed=None):
    seed_key = seed or (query or "default")
    h = hashlib.md5(seed_key.encode("utf-8")).hexdigest()
    cache_name = "bg_1080p_%s.mp4" % h[:12]
    out_path = os.path.join(work_dir, cache_name)

    if os.path.exists(out_path) and os.path.getsize(out_path) > 300000:
        is_hd, w, h_dim = check_video_quality(out_path)
        if is_hd:
            print("    [Background] Dung video nen Full HD da co (cache %dx%d): %s" % (w, h_dim, out_path))
            return out_path
        else:
            print("    [Background] Cache cu %dx%d khong dat chuan HD, se tai lai..." % (w, h_dim))
            try:
                os.remove(out_path)
            except Exception:
                pass

    pool = _build_pool(query)
    if not pool:
        raise RuntimeError("Khong co nguon video nen nao.")

    start = int(h[:8], 16) % len(pool)
    order = pool[start:] + pool[:start]
    print("    [Background] Chon video nen Full HD cho '%s' (tu %d nguon)..." % (seed_key, len(order)))
    
    for url in order:
        try:
            print("    [Background] Dang tai Full HD: %s..." % url.split("/")[-1])
            download_file(url, out_path)
            if os.path.exists(out_path) and os.path.getsize(out_path) > 200000:
                is_hd, w, h_dim = check_video_quality(out_path)
                if is_hd:
                    print("    [Background] Tai thanh cong Full HD (%dx%d): %s" % (w, h_dim, out_path))
                    return out_path
                else:
                    print("    [Background] Video tai ve (%dx%d) chua dat chuan HD, thu video tiep theo..." % (w, h_dim))
                    if os.path.exists(out_path):
                        os.remove(out_path)
        except Exception as e:
            print("    [Background] Link khong kha dung (%s), thu tiep..." % e)

    raise RuntimeError("Khong the tai video nen Full HD tu bat ky nguon nao.")

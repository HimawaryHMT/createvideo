import os
import random
import hashlib
import urllib.request
import urllib.parse
import re
import html

# Bo suu tap video stock du phong (da kiem chung tai duoc, chu de coffee/aesthetic)
FALLBACK_STOCK_VIDEOS = [
    "https://media.istockphoto.com/id/1133015837/video/coffee-mixing-with-milk-slow-motion.mp4?b=1&s=192_srp&k=20&c=MojpSn7i4gjCizu-q_9NMdcrb9Dw71-CpAAw7L7tILQ=",
    "https://media.istockphoto.com/id/1491165438/video/coffee-drink-in-white-cup-close-up-brewing-fresh-beverage-of-aromatic-arabica-with-milk-cream.mp4?b=1&s=192_srp&k=20&c=vdlv1vRrHopVw_S7p7r-BLOktcZZQngCKj5bMJC9E5w=",
    "https://media.istockphoto.com/id/1269721081/video/close-up-of-seeds-of-coffee-fragrant-coffee-beans-are-roasted-smoke-comes-from-coffee-beans.mp4?b=1&s=192_srp&k=20&c=JYL12VhH24I9s4BdU8em7DtHNQ6Sfqut9tzcxuY7tVo=",
    "https://media.istockphoto.com/id/1401297500/video/grinding-roasted-coffee-beans-in-burr-grinder-table-top-view.mp4?b=1&s=192_srp&k=20&c=xNdry2zmIeuvs3jHzyNqyoxJH1FLeONr8GBF3r6NDm0=",
    "https://media.istockphoto.com/id/2176636157/video/super-slow-motion-shot-of-pouring-milk-into-black-coffee.mp4?b=1&s=192_srp&k=20&c=L8pfC_-rKBMGG0OgVPV50HnflTTvDGnH1Zuf9nryBSE=",
]


def download_file(url, out_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://coverr.co/",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response, open(out_path, "wb") as out_file:
        out_file.write(response.read())
    return out_path


def fetch_stock_videos_by_query(query="nature"):
    try:
        search_url = "https://coverr.co/s?q=%s" % urllib.parse.quote(query)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            page_html = resp.read().decode("utf-8", errors="ignore")
        matches = re.findall(r'https://[^\"]+?\.mp4[^\"]*', page_html)
        if matches:
            return list(set(html.unescape(m) for m in matches))
    except Exception as e:
        print("    [Background] Khong tim duoc theo tu khoa '%s': %s" % (query, e))
    return []


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
    random.shuffle(uniq)
    return uniq


def get_background_video(work_dir, query="", seed=None):
    seed_key = seed or (query or "default")
    h = hashlib.md5(seed_key.encode("utf-8")).hexdigest()
    cache_name = "bg_%s.mp4" % h[:12]
    out_path = os.path.join(work_dir, cache_name)

    if os.path.exists(out_path) and os.path.getsize(out_path) > 100000:
        print("    [Background] Dung video nen da co (cache): %s" % out_path)
        return out_path

    pool = _build_pool(query)
    if not pool:
        raise RuntimeError("Khong co nguon video nen nao.")

    start = int(h[:8], 16) % len(pool)
    order = pool[start:] + pool[:start]
    print("    [Background] Chon video nen cho '%s' (tu %d nguon)..." % (seed_key, len(order)))
    for url in order:
        try:
            print("    [Background] Dang tai: %s..." % url[:70])
            download_file(url, out_path)
            if os.path.exists(out_path) and os.path.getsize(out_path) > 100000:
                print("    [Background] Tai thanh cong: %s" % out_path)
                return out_path
        except Exception as e:
            print("    [Background] Link khong kha dung (%s), thu tiep..." % e)

    raise RuntimeError("Khong the tai video nen tu bat ky nguon nao.")

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main as gen


def _progress_path(root):
    return os.path.join(root, "work", ".last_idx")


def load_progress(root):
    try:
        with open(_progress_path(root), "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return -1


def save_progress(root, idx):
    os.makedirs(os.path.join(root, "work"), exist_ok=True)
    with open(_progress_path(root), "w", encoding="utf-8") as f:
        f.write(str(idx))


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    pool_path = os.path.join(root, "content_pool.json")
    with open(pool_path, encoding="utf-8") as f:
        items = json.load(f)

    last = load_progress(root)
    idx = (last + 1) % len(items)
    save_progress(root, idx)
    item = items[idx]

    with open(os.path.join(root, "input.json"), "w", encoding="utf-8") as f:
        json.dump(item, f, ensure_ascii=False, indent=2)

    print("=== [%s] Chon chu de #%d/%d: %s (bg: %s) ===" % (
        datetime.date.today().isoformat(), idx + 1, len(items),
        item.get("word", "?"), item.get("bg_query", ""),
    ))

    sys.argv = ["main.py", "input.json"]
    gen.main()


if __name__ == "__main__":
    main()

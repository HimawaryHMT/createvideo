import asyncio
import json
import os
import edge_tts

VOICES = {
    "en": "en-US-ChristopherNeural",
    "vi": "vi-VN-HoaiMyNeural",
}


async def _synth_with_timings(text: str, voice: str, out_path: str, rate: str, pitch: str) -> list:
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    words = []
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "offset_s": chunk["offset"] / 10000000.0,
                    "dur_s": chunk["duration"] / 10000000.0,
                    "text": chunk["text"],
                })
    return words


def synth(text: str, voice: str, out_path: str, timing_json: str = None, rate: str = "+0%", pitch: str = "+0Hz") -> list:
    """Sinh audio MP3 va cap nhat moc thoi gian tung tu (WordBoundary)."""
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        if timing_json and os.path.exists(timing_json):
            try:
                with open(timing_json, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

    words = asyncio.run(_synth_with_timings(text, voice, out_path, rate, pitch))
    if timing_json:
        with open(timing_json, "w", encoding="utf-8") as f:
            json.dump(words, f, ensure_ascii=False, indent=2)
    return words

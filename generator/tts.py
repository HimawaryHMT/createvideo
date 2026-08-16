import asyncio
import edge_tts

VOICES = {
    "en": "en-US-ChristopherNeural",
    "vi": "vi-VN-HoaiMyNeural",
}


async def _synth(text: str, voice: str, out_path: str, rate: str, pitch: str) -> None:
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(out_path)


def synth(text: str, voice: str, out_path: str, rate: str = "+0%", pitch: str = "+0Hz") -> str:
    asyncio.run(_synth(text, voice, out_path, rate, pitch))
    return out_path

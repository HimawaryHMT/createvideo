# CreateVideo — Tạo video TikTok tiếng Anh giao tiếp tự động

Cong cu dong lenh tao video TikTok kieu kenh "Tieng Anh giao tiep online":
mot tu vung tieng Anh + nghia tieng Viet, giong doc tu dong (edge-tts), nen video
stock, text noi bat tren the toi. Xuat ra MP4 doc 1080x1440, 30fps, san sang dang TikTok.

---

## 1. Tong quan

| Hang muc | Mo ta |
|---|---|
| Dau ra | output/<tu>_<timestamp>.mp4 (1080x1440, 30fps, H.264 + AAC) |
| Giong doc | edge-tts (mien phi), giong EN: en-US-ChristopherNeural |
| Nen video | Video stock tu Coverr (tim theo tu khoa) + fallback iStock |
| Noi dung | Do nguoi dung dinh nghia trong input.json / content_pool.json |
| Tu dong | Task Scheduler chay run_daily.bat luc 16:00 moi ngay |
| Ngon ngu code | Python 3.12, Pillow, edge-tts, FFmpeg |

---

## 2. Cau truc du an

CreateVideo/
├── main.py                # Chuong trinh chinh: doc input.json -> tao 1 video
├── input.json             # Noi dung cua video (bi ghi de khi chay tu dong)
├── content_pool.json      # Danh sach 110 tu vung de xoay vong tu dong
├── run_daily.py           # Chon 1 tu theo luot -> ghi input.json -> goi main.py
├── run_daily.bat          # Launcher cho Task Scheduler (tim python, cd thu muc)
├── requirements.txt       # pillow, edge-tts
├── .gitignore             # bo qua work/, output/, __pycache__/
├── generator/
│   ├── __init__.py
│   ├── tts.py             # edge-tts: sinh file MP3 tung cau
│   ├── render.py          # PIL: ve khung hinh PNG trong suot + the toi
│   ├── assemble.py        # FFmpeg + wave: ghep audio + encode MP4
│   ├── background.py      # Tai video nen theo tu khoa, cache theo noi dung
│   └── fonts/             # Be Vietnam Pro (ho tro tieng Viet)
├── work/                  # File tam (frame, wav, cache TTS, video nen, .last_idx)
└── output/                # Video thanh pham

Luu y: work/ va output/ nam trong .gitignore — khong push len git.

---

## 3. Quy trinh tao video (pipeline)

main.py chay 5 buoc:

1. Lay video nen (background.get_background_video)
   - Tim kiem Coverr theo bg_query, ket hop danh sach fallback iStock.
   - Chon 1 video xac dinh theo hash(word|bg_query), luu work/bg_<hash>.mp4 (nho cache).

2. Tao giong doc (tts.synth + assemble.mp3_to_wav)
   - Voi moi scene: edge-tts sinh MP3, chuyen sang WAV 44100Hz stereo.
   - Cache theo hash(voice|text) -> doi text thi tu sinh lai, khong dung file cu.

3. Render khung hinh (render.render)
   - Ve PNG trong suot (RGBA) 1080x1440 @ 30fps: text EN to o giua, nghia VN ben duoi,
     the toi bo goc mo phia sau de chu luon noi bat tren moi nen.
   - Text fade-in/out, drift nhe. Moi scene = 1 nhan label rieng.

4. Ghep audio (assemble.build_audio)
   - Dat tung doan giong doc vao dung thoi diem (nhan he so kenh stereo).

5. Encode MP4 (assemble.encode_video)
   - FFmpeg: loop video nen (scale/crop 1080x1440) -> overlay khung PNG -> ghep audio -> cat dung do dai (-t).

Luu y ky thuat da fix:
- Output luon bi ep ve 30fps (fps=30 tren filter nen) va cat bang -t duration
  (vì -shortest khong dung duoc voi -stream_loop -1).
- Audio dat dung vi tri nho nhan x CH (so kenh).
- render() xoa work/frames truoc khi ve de khong lot frame cu.

---

## 4. Dinh dang input.json

{
  "word": "Confident",
  "word_vi": "Tu tin",
  "bg_query": "coffee",
  "scenes": [
    { "style": "question", "en": "What is confidence?", "vi": "Tu tin la gi?" },
    { "style": "quote_dark", "en": "Confidence is not \"they will like me\".", "vi": "..." },
    { "style": "quote_gold", "en": "Confidence is \"I'll be fine if they don't\".", "vi": "..." }
  ],
  "caption": "Tu tin la gi ?",
  "hashtags": "#english #talkenglish #motivation #dongluc #dongluchoctap #cogang",
  "voice": "en-US-ChristopherNeural"
}

| Truong | Y nghia |
|---|---|
| word / word_vi | Tu vung + nghia (hien o scene cuoi + dung lam seed chon nen) |
| bg_query | Tu khoa tim video nen (coffee, nature, rain, city, ocean, forest...) |
| scenes | Danh sach canh. Moi canh: style + cau en + nghia vi |
| style | question (canh mo dau) / quote_dark / quote_gold (2 canh quote) |
| caption | Tieu de dang TikTok (in ra cuoi) |
| hashtags | Hashtag dinh kem caption |
| voice | Giong edge-tts (doi en-US-JennyNeural cho giong nu) |

So canh tuy y (toi thieu 1). Do dai video tu dong theo giong doc.

---

## 5. Chay thu cong

python main.py                 # hoac: python main.py input.json
python main.py input2.json    # dung file noi dung khac
python main.py --keep-work     # giu work/ de debug (frame, wav)

Video ra output/.

---

## 6. Tu dong hoa (xoay vong tu vung)

content_pool.json la mang cac object giong cau truc input.json (hien co 110 tu,
moi tu 1 bg_query rieng -> nen khac nhau).

run_daily.py moi lan chay:
1. Doc work/.last_idx (lan truoc dung o tu nao).
2. Chon tu ke tiep ((last + 1) % len) -> ghi de input.json.
3. Goi main.py tao video.

-> Moi lan click run_daily.bat (hoac moi 16:00) sinh 1 tu + 1 nen khac voi lan truoc,
xoay vong qua toan bo 110 tu roi moi lap lai.

Khoi dong lai vong: xoa work/.last_idx.

### Len lich Task Scheduler (da cai san)

- Task: CreateVideoDaily — chay run_daily.bat luc 16:00 hang ngay.
- Quan ly:
  schtasks /Query  /TN CreateVideoDaily
  schtasks /Delete /TN CreateVideoDaily /F
- Dang ky lai (neu can):
  schtasks /Create /TN "CreateVideoDaily" /TR '"D:\Project Individual\CreateVideo\run_daily.bat"' /SC DAILY /ST 16:00 /F
- run_daily.bat tu tim python hop le (path codex-runtime -> python -> py -3),
  roi cd vao thu muc du an nen khong can quan tam duong dan tuong doi.

Luu y: Task chi chay khi ban da dang nhap may. Neu tat may luc 16:00, video ngay do bo qua.

---

## 7. Them / sua noi dung

- Them tu moi: them 1 object vao mang content_pool.json (copy cau truc input.json,
  dat bg_query khac de co nen rieng).
- Doi giong doc: sua truong "voice" (vd en-US-JennyNeural, en-US-AriaNeural, vi-VN-HoaiMyNeural...).
- Doi nen thu cong: sua bg_query cua tu do, hoac xoa work/bg_<hash>.mp4 de tai lai.

---

## 8. Xu tri su co

| Hien tuong | Nguyen nhan / Xu ly |
|---|---|
| Giong doc cu du da doi text | Cache TTS theo hash text -> doi text la tu sinh lai. Neu van cu, xoa work/tts_*.mp3 |
| Nen luon 1 cai | background.py cache theo hash noi dung; doi word/bg_query se lay nen khac |
| Video dai hon 15s / giat | Da fix bang fps=30 + -t; neu gap lai kiem tra generator/assemble.py |
| Khong tai duoc nen | Coverr/iStock loi mang -> script tu thu link tiep; het link bao loi (khong tu fallback nen den) |
| Task khong chay | May chua login luc 16:00, hoac python bi doi path (.bat co fallback, nhung neu ca 3 khong co package thi bao loi) |
| Chu tieng Viet bi tofu | Thieu font Be Vietnam Pro trong generator/fonts/ |

---

## 9. Phu thuoc

pip install -r requirements.txt   # pillow, edge-tts
# FFmpeg da cai qua: winget install Gyan.FFmpeg

Cai lan dau can ket noi internet (edge-tts sinh giong, background tai video).

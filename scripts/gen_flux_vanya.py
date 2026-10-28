#!/usr/bin/env python3
"""「바냐 아저씨」(안톤 체호프) Flux 무드 이미지 배치 생성

1890년대 러시아 시골 영지 → 정원의 사모바르·차 → 은퇴 교수와 젊은 아내 엘레나의 도착 → 바냐의 환멸·고백
→ 숲을 지키는 의사 아스트로프·소냐의 짝사랑 → 폭풍 전야의 밤(→ 실내 램프·낮 그늘로) → 영지 매각 선언 → 총성·불발
→ 떠나는 마차 → 남겨진 바냐와 소냐, 다시 장부 앞에. 「우린 쉬게 될 거예요」.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 장부·지도·편지·책 펼침면 금지(글씨가 붙는다), 닫힌 장부만.
인물은 「Russian … in 1890s clothes」 명시. ⚠️ 19세기 삽화풍은 모서리 서명이 붙는다(15소년 19장) → 사진풍 영화 스틸로.
★ 배경은 장면별로만(BASE 금지). 밤 장면 금지(b<60). 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_vanya.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-19 /health 로 9010 확인
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Uncle_Vanya_flux"))   # 검수 후 옮긴다

BASE = ("quiet naturalistic period film still, 35mm photograph, soft natural daylight, bright enough to see clearly, not dark, "
        "muted palette of birch white, faded green, linen beige and pale gold, shallow depth of field, gentle film grain, "
        "melancholy, tender, wistful mood, no signature, no watermark, no signs, no logos, no labels, no text, no letters, no numbers, no writing anywhere")

VA = "a weary Russian man of forty-seven with untidy brown hair and a short beard in a rumpled 1890s linen suit"
SO = "a plain earnest Russian young woman with dark hair in a simple braid and a modest 1890s grey dress"
EL = "a beautiful languid Russian woman of twenty-seven with pinned-up chestnut hair in an elegant pale 1890s dress"
AS = "a lean Russian country doctor in his late thirties with a moustache in a 1890s dark coat"
PR = "an elderly Russian professor with white hair and gold-rimmed spectacles in a heavy 1890s overcoat, sour face"

SCENES = [
    "a wide view of a 19th century Russian country estate with a white wooden manor house among birch trees, summer afternoon",
    "a long tree-lined avenue of old lime trees leading to a Russian manor house, dappled sunlight",
    "a garden table under old trees with a brass samovar, glass tea cups and a white tablecloth, afternoon light",
    "an old Russian nanny in a headscarf knitting on a wooden garden bench, calm face, soft daylight",
    f"{AS} sitting at a garden tea table talking, tired thoughtful face, summer light",
    f"{VA} yawning as he steps out onto a wooden veranda after a nap, afternoon",
    f"{PR} walking slowly in a garden leaning on a cane",
    f"{EL} walking slowly through a sunlit birch grove holding a parasol",
    f"{VA} looking longingly at a woman in a pale dress across a garden, shallow focus",
    "close-up of a hand-written ledger closed on a wooden desk beside an abacus and a candle, no visible writing",
    f"{VA} sitting at a desk with a closed ledger, head in his hand, pale morning light from a window",
    f"{SO} working at a wooden table with an abacus beside a window, determined face",
    "a dense summer birch and pine forest with sunbeams, untouched Russian woodland",
    "a felled stretch of forest with tree stumps on a hillside, overcast pale light, loss",
    f"{AS} standing in a forest clearing looking up at tall pines, passionate expression",
    f"{SO} looking up at a man with quiet hope in a sunlit parlour, shallow focus on her face",
    f"{PR} sitting in an armchair wrapped in a plaid blanket, complaining, lamp-lit drawing room, warm and bright",
    "heavy grey storm clouds gathering over a Russian estate and fields, wind bending birch trees, daylight",
    "rain streaming down old window panes of a manor house, soft grey daylight inside",
    f"{EL} and {SO} sitting close together on a sofa talking softly, warm lamplight, reconciliation",
    "an upright piano with its lid closed in an old Russian drawing room, soft afternoon light",
    f"{VA} and {AS} sitting by a table with a carafe and glasses, slightly drunk, warm lamplight",
    f"{EL} standing by a tall window gazing out, bored and lonely, soft daylight",
    f"{AS} and {EL} in a close embrace in a sunlit drawing room, a door half-open behind them",
    f"{VA} standing in a doorway holding a bouquet of autumn roses, stricken face",
    f"{PR} addressing a seated family in a drawing room with a raised finger, formal, daylight",
    f"{VA} shouting in anger in a drawing room, fists clenched, others recoiling",
    "close-up of an old 19th century revolver lying on a wooden floor, soft light",
    f"{VA} slumped in a chair in despair, a revolver dropped at his feet, daylight",
    "a small glass medicine vial in a trembling hand, extreme close-up, soft light",
    "a horse-drawn carriage with luggage leaving a Russian manor house down a lime tree avenue, autumn morning",
    f"{AS} riding away alone in a small cart along a country road through fields, autumn",
    "an autumn Russian estate garden with yellow birch leaves falling, quiet and empty, soft light",
    f"{VA} and {SO} sitting side by side at a desk with closed ledgers by a lamp, calm resignation, warm bright light",
    f"{SO} kneeling beside a seated weary man, holding his hands, gentle consoling face, soft warm light",
]


def generate(prompt: str, seed: int) -> bytes | None:
    body = json.dumps({
        "prompt": prompt, "width": 1920, "height": 1080, "steps": 4, "seed": seed
    }).encode()
    req = urllib.request.Request(FLUX, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return base64.b64decode(json.loads(r.read())["image_base64"])
    except Exception as e:
        print(f"   ❌ {e}", flush=True)
        return None


def main() -> None:
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    OUT.mkdir(parents=True, exist_ok=True)
    made = 0
    t0 = time.time()
    for i, scene in enumerate(SCENES, 1):
        prompt = f"{BASE}. {scene}"
        for k in range(per):
            seed = int(os.environ.get("SEED_BASE", "41000")) + i * 100 + k * 7
            img = generate(prompt, seed)
            if not img:
                continue
            path = OUT / f"mood_f{i:02d}_{k+1}.jpg"
            path.write_bytes(img)
            made += 1
            print(f"[{made}] {path.name}  ({time.time()-t0:.0f}s)  {scene[:50]}", flush=True)
    print(f"\n✅ {made}장 생성 / {time.time()-t0:.0f}초", flush=True)


if __name__ == "__main__":
    main()

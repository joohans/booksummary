#!/usr/bin/env python3
"""「지하로부터의 수기」(도스토옙스키) Flux 무드 이미지 배치 생성

1860년대 페테르부르크, 지하 방, 촛불, 진눈깨비, 수정궁, 장교, 즈베르코프 송별회, 리자.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 거리·술집 정면은 간판이 붙는다. 거리는 안개·진눈깨비로 흐리게, 실내는 얕은 심도·민무늬 벽·클로즈업.
→ 책·편지·신문은 글씨가 붙으니 「빈 종이」「뒤에서」만. 음울한 책이지만 처음부터 밝은 톤(밝기 ≥60).
→ 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_underground.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-16 /health 로 9010 확인
OUT = Path("assets/images/Notes_from_Underground_flux")   # 검수 후 옮긴다

BASE = ("painterly 19th century Russian film still, Saint Petersburg in the 1860s, soft diffused pale daylight, "
        "muted blue-grey and warm candle amber palette, bright enough to see clearly, not dark, "
        "extreme shallow depth of field, soft bokeh, plain bare walls, gentle film grain, melancholic and introspective mood, "
        "no logos, no text, no letters, no numbers, no writing anywhere")

SCENES = [
    # 지하 인간
    "a pale thin man around forty with unkempt hair and a shabby dressing gown sitting alone in a small bare room, sardonic expression, close-up portrait",
    "a man clutching his side in pain on a narrow bed in a cramped bare room, refusing help, soft window light",
    "a cramped low-ceilinged corner room with a single small window and a worn armchair, dust in the light, empty",
    "a candle burning on a bare wooden table beside an empty inkwell and a quill, close-up, soft light",
    "a man's hand writing with a quill on blank paper by candlelight, close-up, no visible words",
    # 과잉 의식
    "a man pacing back and forth in a narrow room, motion blur, restless, seen from the doorway",
    "a man staring at his own reflection in a cracked small mirror, bitter half smile, close-up",
    "a mouse peeking out from a crack in a wooden floorboard, close-up, soft light",
    "a man holding his jaw in pain with a strange smile, close-up, candle glow",
    # 수정궁 · 이성
    "a vast glittering palace made entirely of glass and iron under a bright sky, utopian, seen from afar",
    "a glass palace reflected in a puddle with a dark figure standing outside it, contrast",
    "close-up of piano keys with a single finger pressing one key, shallow focus, soft light",
    "abacus beads and brass weighing scales on a plain table, close-up, cold light",
    "a man turning his back on a shining glass palace, walking away into fog",
    # 진눈깨비 · 장교
    "wet snow falling over a misty Saint Petersburg canal with old iron railings, soft grey light, no signs",
    "a lone man in a worn overcoat walking through wet sleet on a misty street at dusk, seen from behind, blurred background",
    "a tall broad-shouldered officer in a 19th century Russian uniform with a mustache, standing in a dim billiard room, close-up, contemptuous",
    "a green billiard table with ivory balls under a hanging lamp, close-up, no people",
    "a small man lying awake in bed at night imagining revenge, face lit by moonlight",
    "two men's shoulders colliding on a crowded misty boulevard in the 1860s, motion, close-up, no signs",
    # 즈베르코프 송별회
    "a group of young men in 19th century frock coats laughing and toasting with wine glasses around a dinner table, warm lamp light",
    "a lonely man in a shabby coat sitting apart at the end of a long dinner table while others ignore him",
    "a man pacing alone along the wall of a private dining room while young men laugh at the table, warm light",
    "spilled wine and empty glasses on a white tablecloth after a dinner, close-up",
    # 리자
    "a young Russian woman of twenty with pale face and simple dress sitting on the edge of a bed in a dim room, sad eyes, close-up, candle light",
    "a young woman crying silently in candle light, close-up, soft focus",
    "a horse-drawn sleigh rushing through the snowy night street, lanterns glowing, motion blur",
    "a man scribbling on a scrap of blank paper and handing it to a young woman, close-up of hands",
    # 리자의 방문 · 결말
    "an old grumpy manservant with grey hair standing stiffly in a bare doorway, close-up",
    "a young woman embracing a weeping man in a bare small room, tender, soft daylight",
    "a man's hand pressing a crumpled blue banknote into a young woman's hand, close-up, no visible printing",
    "a crumpled blue paper note left alone on a bare wooden table, close-up, soft light",
    "a young woman in a shawl walking away into falling wet snow on an empty street, seen from behind, misty",
    "a man standing bareheaded in falling wet snow at night, looking into empty distance, lamp glow",
    "a single candle burning down to the end on a windowsill with snow outside, close-up",
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
            seed = 95000 + i * 100 + k * 7
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

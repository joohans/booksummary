#!/usr/bin/env python3
"""「너도 하늘말나리야」(이금이) Flux 무드 이미지 배치 생성

충북 산골 마을 달밭, 열세 살 미르·소희·바우. 느티나무, 진료소장 엄마, 할머니, 그림 그리는 바우, 꽃바구니, 하늘말나리.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 황만근(10/16) 방식: 자연·들판·클로즈업 위주(66장 중 7장 폐기). 진료소·학교·마을회관 정면은 간판이 붙으니 넣지 않는다.
→ 부정어는 일반어만(구체 물체 이름 금지 — 눈먼 자들의 도시 신호등 교훈). 출산 장면은 그리지 않는다.
→ 처음부터 밝은 톤. 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_skylily.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-13 /health 로 9010 확인
OUT = Path("assets/images/You_Are_a_Sky_Lily_Too_flux")   # 검수 후 옮긴다

BASE = ("cinematic film still, mountain village in rural South Korea, soft natural daylight, fresh greens, warm orange and sky blue palette, "
        "gentle film grain, tender coming-of-age mood, shallow depth of field, "
        "no logos, no text, no letters, no numbers, no writing anywhere")

SCENES = [
    # 하늘말나리
    "close-up of a single orange sky lily flower facing straight up toward a bright blue sky, spotted petals, mountain meadow",
    "a cluster of drooping orange lilies with one lily facing upward to the sky, close-up, soft sunlight",
    # 달밭 · 느티나무
    "a huge old zelkova tree standing at the entrance of a small mountain village in early spring, low houses and fields, soft morning light",
    "a quiet mountain valley village with terraced fields and stone walls, spring haze, seen from a hill",
    # 미르
    "a sulky twelve-year-old Korean city girl with headphones sitting in the back seat of a car looking out at mountains, close-up, soft light",
    "a Korean woman in her late thirties in a white nurse coat smiling gently at a sulky daughter, bright plain room",
    "a twelve-year-old Korean girl standing alone at the edge of a school playground, other children blurred in the distance, lonely",
    "a twelve-year-old girl in a different colored tracksuit standing apart from classmates in matching tracksuits, sad, sunny field",
    "a girl crying alone under a big tree, knees pulled up, soft afternoon light",
    # 소희
    "a mature calm twelve-year-old Korean girl with a ponytail writing in a small diary at a low wooden table, warm lamp light, close-up",
    "an elderly Korean grandmother in simple clothes peeling chestnuts on a wooden porch beside her granddaughter, warm sunset light",
    "close-up of a girl's hand writing in a diary with a pencil, blank lined pages, soft light",
    "a girl looking at an old family photograph with the faces cut out, close-up, melancholy",
    # 바우
    "a quiet twelve-year-old Korean boy sketching wildflowers with colored pencils by a stream, absorbed, soft light",
    "close-up of a child's colorful drawing of mountain wildflowers on white paper, no writing",
    "a boy and his father standing by a grass-covered grave mound on a hillside placing red spider lilies, morning mist",
    "red spider lilies blooming in a misty forest, close-up",
    "a strong farmer father in his forties with a weathered face working in a vegetable field, kind eyes",
    # 꽃바구니 · 오해
    "a beautiful basket of red roses on a small table in a bare room, soft light",
    "a crushed basket of roses scattered on the ground, petals everywhere, close-up, emotional",
    "a boy finally speaking to a girl under a big tree, both surprised, soft golden light",
    "three twelve-year-old children sitting together on a stone wall by a field, laughing, summer light",
    # 엄마를 이해함
    "a mother and daughter walking along a dark country path at night with a flashlight, stars above, determined",
    "a warm lit window of a lonely farmhouse at night in the mountains, peaceful",
    "a nurse mother hugging her daughter at dawn, both exhausted and moved, soft first light",
    "dawn light spreading over misty mountain fields, hopeful",
    # 이별
    "an empty wooden porch of a rural house in winter with a pair of old rubber shoes, snow, quiet mourning",
    "a twelve-year-old girl holding a small suitcase on a snowy country road, looking back at the village, soft winter light",
    "a boy handing a rolled painting to a girl under a bare winter tree, close-up of hands",
    "a girl unrolling a painting of an orange lily facing the sky, close-up, tears and smile",
    "three children waving goodbye on a country road, seen from behind, snow-covered fields",
    "an orange lily blooming among rocks on a mountain ridge against a vast blue sky, hopeful",
    "a wide summer meadow full of wildflowers in a mountain valley, bright and peaceful",
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
            seed = 90000 + i * 100 + k * 7
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

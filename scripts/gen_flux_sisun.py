#!/usr/bin/env python3
"""「시선으로부터,」(정세랑) Flux 무드 이미지 배치 생성

한국전쟁 속 홀로 남은 소녀 시선 → 1950년대 하와이 농장 → 유럽 화실(붓·빈 캔버스) → 화가이자 작가로 살아간 시선
→ 10주기, 하와이에 모인 가족 → 파도·무지개·도넛과 커피·깃털·산호·화산·바다 거품 → 해 질 녘 해변의 제사.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 간판·포장지·그림 완성작(서명)·책·현판 금지, 자연·바다·인물 위주.
★ 35mm film still BASE. 배경은 장면별로만. 밤 장면 금지(밝기 ≥60). 한국 인물은 「Korean … black hair」 명시.

    SEED_BASE=46000 .venv/bin/python scripts/gen_flux_sisun.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/From_Sisun_Onward_flux"))   # 검수 후 옮긴다

BASE = ("35mm film still, soft natural daylight, bright enough to see clearly, not dark, "
        "warm palette of ocean turquoise, hibiscus red, sand beige and leafy green, shallow depth of field, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no signs, no numbers, no writing anywhere, no watermark, no signature")

GIRL = "a thin Korean girl about fifteen with black hair in a short bob, in a plain worn 1950s cotton dress"
YW = "a young Korean woman about twenty with black hair tied back, in a simple 1950s cotton dress"
ART = "a Korean woman artist in her forties with short black hair, in a paint-stained linen smock, 1970s"
OLD = "an elegant elderly Korean woman about eighty with short silver hair, in a simple dark linen dress, sharp clever eyes"
FAM = "a Korean family of three generations with black hair in casual summer clothes"
W1 = "a Korean woman in her sixties with short black hair, in a linen shirt and sun hat"
G1 = "a Korean woman about thirty with long black hair, in a loose summer shirt"
G2 = "a Korean young woman about twenty-five with black hair in a ponytail, in a wetsuit"

SCENES = [
    # 1 전쟁 속에서 홀로 남다
    f"{GIRL} walking alone along a dirt road between bare hills, 1950s Korea, grey overcast daylight, somber",
    f"close-up of {GIRL} with a determined tearful face, wind in her hair, overcast",
    "an empty rural Korean field with distant mountains under a pale grey sky, 1950s, desolate",
    # 2 젊은 날의 하와이
    "a 1950s sugarcane plantation in Hawaii with green mountains behind, bright sun",
    f"{YW} working in a sugarcane field in Hawaii wearing a straw hat, bright sun, sweat",
    f"{YW} standing alone on a quiet Hawaiian beach looking out at the ocean, 1950s, golden afternoon",
    "a wooden plantation workers' cottage under palm trees in Hawaii, 1950s, bright day",
    # 3 유럽의 화실과 상처
    "a large bright empty artist studio in 1950s Germany with tall windows, easels holding blank white canvases",
    f"close-up of {YW}'s hands holding a paintbrush over a blank canvas, palette of colors, window light",
    f"{YW} sitting alone by a tall window in a European studio, hugging her knees, sad, soft grey light",
    "a grey rainy European city street of the 1950s seen through a wet window, blurred",
    # 4 화가이자 작가로
    f"{ART} painting energetically with bold colors on a large abstract canvas, sunny studio, seen from behind",
    "close-up of thick bright oil paint strokes in red, blue and yellow, abstract texture",
    f"{ART} laughing with friends around a wooden table in a sunny courtyard, 1970s Korea",
    f"{OLD} sitting in a garden chair under a tree with a cup of tea, confident smile, bright afternoon",
    f"close-up portrait of {OLD}, wise and witty expression, soft window light",
    # 5 십 주기의 제안
    f"{FAM} gathered around a wooden dining table in a bright modern apartment, discussing, daylight",
    f"{W1} speaking firmly to her family at a table, raising one hand, bright room",
    "an airplane wing above white clouds over the blue Pacific Ocean, bright sky",
    # 6 하와이에 모인 가족
    "an aerial view of a green Hawaiian island coastline with turquoise water and white surf",
    f"{FAM} walking together along a wide sandy Hawaiian beach, laughing, bright sun",
    f"{FAM} sitting on a lanai veranda of a beach house with palm trees, relaxed, afternoon",
    "red hibiscus flowers and green leaves close-up with sunlight, Hawaii",
    "tall palm trees swaying against a bright blue sky, low angle",
    # 7 저마다의 기쁜 순간
    f"{G2} paddling a surfboard out into turquoise waves, bright sun, seen from behind",
    "a surfer riding a perfect curling turquoise wave, spray of white foam, bright sunlight",
    "white sea foam on wet golden sand at the edge of the waves, close-up, bright",
    f"{G1} looking up at a bright rainbow over green Hawaiian mountains after rain, hopeful",
    "a vivid rainbow arching over lush green Hawaiian cliffs and the sea, bright day after rain",
    "fresh glazed malasada donuts on a plain white plate on a wooden table, soft daylight",
    "a cup of black coffee on a wooden railing with a view of green coffee trees on a hillside, Hawaii morning",
    "a handful of colorful bird feathers held in an open palm, soft light, close-up",
    "colorful coral and tropical fish under clear turquoise water, sunlight rays",
    "a black lava field meeting the blue ocean with steam rising, Hawaii, bright overcast",
    f"a Korean teenage boy with black hair crouching on a beach watching a green sea turtle resting on the sand, bright day",
    f"{G1} sitting alone on a rock by the sea writing nothing, just thinking, wind in her hair, afternoon",
    # 8 시선의 말들
    f"{OLD} standing on a beach long ago looking at the ocean, seen from behind, wind in her silver hair, soft light",
    f"close-up of an elderly Korean woman's hands resting on her lap, a thin silver ring, soft light",
    # 9 해변의 제사
    f"{FAM} gathering on a beach at golden hour, each holding a small object, gentle smiles",
    "a simple low wooden tray on the sand with a donut, a coffee cup, feathers, a seashell and a small jar of sea foam, golden hour beach",
    f"{FAM} standing in a row facing the ocean at golden hour, seen from behind, quiet",
    f"{W1} wiping a tear while smiling on the beach at golden hour",
    "the sun setting over the calm Pacific ocean in warm orange and pink light, still bright",
    "footprints of many people on wet sand leading toward the sea, golden light",
]

assert len(SCENES) == 44, len(SCENES)


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
            seed = int(os.environ.get("SEED_BASE", "46000")) + i * 100 + k * 7
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

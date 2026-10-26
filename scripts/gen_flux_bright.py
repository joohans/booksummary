#!/usr/bin/env python3
"""「밝은 밤」(최은영) Flux 무드 이미지 배치 생성

현재: 이혼한 지연(32)이 바닷가 도시 희령으로 → 언덕 위 할머니와 재회 → 할머니 집에서 옛이야기·사진·편지.
과거: 1930년대 황해도 소녀 삼천(백정의 딸) → 개성으로 시집 → 새비 아주머니와의 우정 → 새비 아저씨의 일본행·병
→ 한국전쟁 대구 피난(한 지붕 아래 여자들) → 할머니 영옥의 홀로 키운 딸.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]). ★ 배경은 장면별로만(BASE 금지, 초정리 편지 10/21).
→ 1930~50년대 거리·관아·가게는 한자 현판이 붙는다 → 들판·마당·맨벽 실내·클로즈업으로. 현대 희령도 거리 대신 바다·언덕.
→ 인물마다 「Korean … black hair」 명시. 밤 장면 금지(지구 끝의 온실 10/22 b<60) — 제목이 「밤」이어도 낮 그늘·노을 직전까지만.
→ 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_bright.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-19 /health 로 9010 확인
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Bright_Night_flux"))   # 검수 후 옮긴다

BASE = ("quiet literary film still, soft natural daylight, bright enough to see clearly, not dark, "
        "muted pastel palette of soft sea blue, warm cream and pale gold, extreme shallow depth of field, soft bokeh, gentle film grain, "
        "tender, quietly hopeful mood, no signboards, no signs, no logos, no labels, no text, no letters, no numbers, no writing anywhere")

KW = "a Korean woman with black hair"
KG = "a Korean girl with black hair"
GM = "an elderly Korean grandmother"
SCENES = [
    # 현재 — 희령
    f"{KW} in her early thirties with tired eyes sitting alone by a train window, landscape of the sea passing, soft daylight, close-up",
    "a quiet Korean seaside town seen from a green hill, calm blue sea, soft hazy daylight, distant low houses, no signs",
    f"{KW} in her early thirties standing on a windy hill above the sea, hair blowing, lonely, soft daylight",
    f"{GM} with short white permed hair and a kind wrinkled face looking up in surprise on a hillside path, soft daylight",
    f"{KW} in her early thirties and {GM} standing awkwardly facing each other on a hill path, wind, soft daylight",
    f"a small bare Korean apartment room with a single futon and moving boxes, plain white walls, soft afternoon light, lonely",
    f"{GM} pouring barley tea into two cups at a low wooden table, warm afternoon light, close-up of hands",
    f"{KW} in her early thirties and {GM} sitting at a low table talking, warm light from a window, plain walls",
    "close-up of an old faded black-and-white photograph of two young women in hanbok held by wrinkled hands, faces blurred, soft light",
    "a stack of old yellowed letters tied with faded ribbon in a wooden box, blank backs only, soft daylight, no writing",
    f"{KW} in her early thirties crying quietly alone on the floor of a bare room, soft grey daylight, close-up",
    "a small brown mixed-breed dog sleeping on a blanket by a sunny window, warm and gentle",
    # 과거 — 삼천
    f"{KG} of seventeen in a plain white hanbok and braided black hair standing in a wide barley field in 1930s rural Korea, worried face, soft daylight",
    f"a Korean mother in a worn white hanbok embracing her teenage daughter in a rural yard of a thatched-roof house, tearful farewell, soft daylight",
    f"{KG} of seventeen in hanbok walking away along a dirt country road with a cloth bundle, seen from behind, hills, soft overcast light",
    f"close-up of a young Korean woman's face in 1930s hanbok, lowered eyes, quiet sorrow, soft window light, plain wall",
    "a traditional Korean tiled-roof courtyard house with an empty earthen yard, soft daylight, no signboards, no plaques",
    f"a young Korean woman in 1930s hanbok washing clothes alone at a stream, other women far away blurred, soft daylight",
    # 새비 아주머니
    f"two young Korean women in 1930s hanbok sitting together on a wooden veranda laughing softly, warm afternoon light, sisterly",
    f"two young Korean women in 1930s hanbok walking together through a field of autumn grass, holding hands, soft golden daylight",
    f"close-up of two women's hands clasped together on a hanbok skirt, warmth, soft light",
    f"a young Korean man in 1930s plain clothes with a small bag saying goodbye to his pregnant wife in a yard, soft overcast light",
    f"a thin pale young Korean man lying sick on a sleeping mat in a plain room, his wife sitting beside him, soft window light",
    f"a young Korean woman in 1930s hanbok holding a baby wrapped in cloth, tender, soft daylight, plain wall",
    "two little Korean girls with black bobbed hair in 1940s simple clothes playing together in a dirt yard, soft daylight",
    # 전쟁·피난
    f"a line of Korean refugees in 1950 walking along a dirt road with bundles on their heads, hills, hazy overcast daylight, distant",
    f"several Korean women of different ages in 1950s simple clothes sewing together in a small crowded room, soft window light, plain walls",
    f"an old Korean woman in 1950s clothes at a sewing machine, warm light, close-up of hands and fabric",
    f"two Korean teenage girls in simple 1950s clothes sharing a bowl of food on a floor, soft light, warm",
    # 할머니·엄마
    f"a young Korean woman in 1960s clothes holding a little daughter's hand on a seaside road, seen from behind, soft daylight",
    f"a stern Korean woman in her sixties with short black hair sitting stiffly on a sofa, cold distant expression, soft daylight",
    # 결말
    f"{GM} and {KW} in her early thirties walking side by side along a quiet beach at dusk with soft warm light, seen from behind",
    "warm small lights of houses on a seaside hill at early dusk, sky still bright blue, gentle and hopeful",
    "a calm sea at golden hour with sunlight sparkling on the water, warm and hopeful",
    "a bright pale sky with soft clouds over the sea, a single gull, peaceful",
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

#!/usr/bin/env python3
"""「황만근은 이렇게 말했다」(성석제) Flux 무드 이미지 배치 생성

한국 농촌 마을 신대리, 반편이라 불린 농부 황만근, 어머니, 토끼와 세 가지 소원, 궐기대회, 고장 난 경운기로 백 리, 유골 항아리, 묘비명.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 자연·들판·클로즈업 위주. 마을회관·면사무소·읍내 장터는 간판이 붙으니 넣지 않는다. 묘비는 글자 없는 돌로.
→ ⚠️ 눈먼 자들의 도시(10/15)에서 부정 프롬프트의 「traffic light」가 실내에 신호등을 불러냈다 — 부정어에 구체 물체 이름을 쓰지 않는다.
→ 처음부터 밝은 톤. 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_hwang.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-13 /health 로 9010 확인
OUT = Path("assets/images/What_Hwang_Man_geun_Said_flux")   # 검수 후 옮긴다

BASE = ("cinematic film still, rural South Korea countryside, soft natural daylight, warm earthy greens, straw gold and pale blue sky, "
        "gentle film grain, humble and warm yet melancholy mood, shallow depth of field, "
        "no logos, no text, no letters, no numbers, no writing anywhere")

SCENES = [
    # 실종 · 마을
    "a quiet Korean farming village at dawn with low-roofed houses among rice paddies and mountains, mist, seen from a hill",
    "an empty muddy country road between harvested rice fields under a grey sky, nobody there",
    "a group of weathered Korean farmers in work clothes grumbling together outdoors by a field, middle-aged men, overcast light",
    # 황만근
    "a simple-hearted Korean farmer in his late forties with a sunburned face and a shy innocent smile, close-up portrait, soft daylight",
    "a Korean farmer carrying a heavy A-frame back carrier loaded with firewood along a field path, seen from behind",
    "close-up of rough work-worn hands holding a hoe in dark soil, warm light",
    "a farmer bending to plant rice seedlings in a flooded paddy reflecting the sky, early morning",
    "an elderly Korean woman sitting lazily on a wooden porch while a middle-aged son brings her a bowl of rice, warm afternoon light",
    "a farmer laughing alone in a golden barley field, wind blowing, carefree",
    "a white enamel bowl of milky rice wine on a low wooden table, close-up, warm light",
    # 토끼 · 소원
    "a huge brown wild rabbit facing a young Korean man on a moonlit mountain path, folktale mood, magical",
    "a young man kneeling on a mountain path under a full moon making a wish with closed eyes, folktale",
    "a young woman standing at the edge of a river bank at dusk, despair, a man running toward her from behind, soft light",
    "a small boy riding on his father's back across a field at sunset, warm and tender",
    # 궐기대회 전날
    "a farmer sitting on a wooden step at night under a single warm bulb, speaking earnestly with a serious face, close-up",
    "a small two-wheeled walking tractor parked in a farmyard at dawn, old and rusty, plain body without marks",
    "close-up of an old farmer's hand on the steering handle of a rusty walking tractor, morning light",
    # 백 리 길
    "a lone farmer driving a slow old walking tractor along the shoulder of a long empty country highway, seen from far behind, vast sky",
    "a slow walking tractor on a country road being passed by a blurred truck, motion blur, lonely",
    "cold rain falling over empty rice paddies at dusk, grey and lonely",
    "a crowd of farmers' umbrellas in the rain seen from above, blurred, no banners",
    "an overturned rusty walking tractor in a frozen muddy rice paddy at dawn, frost, no people, silent tragedy",
    "frost on dry rice stubble in a winter paddy at sunrise, close-up, silent",
    # 귀향 · 묘비명
    "a young man walking along a country road carrying a plain earthenware jar wrapped in white cloth in his arms, seen from behind, grey morning",
    "a plain earthenware burial jar on a low table beside a candle in a bare room, soft light, mourning",
    "a man in his forties with glasses sitting alone at a low table at night writing with a brush on a blank paper, face lit by lamp, focused",
    "a small blank uncarved stone standing on a grassy hillside grave mound under a wide sky, no inscription",
    "a man with a backpack walking away from a village along a country road toward distant hills, seen from behind",
    "wild cosmos flowers swaying on a hill above a village in autumn sunlight",
    "a lone persimmon tree with orange fruit against a clear autumn sky in a farming village",
    "golden sunset over terraced rice fields and low mountains, peaceful and elegiac",
    "an old wooden gate of a rural house left open, empty yard, soft afternoon light",
    "a white heron standing in a green rice paddy, close-up, serene",
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
            seed = 89000 + i * 100 + k * 7
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

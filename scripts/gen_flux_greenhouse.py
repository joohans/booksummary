#!/usr/bin/env python3
"""「지구 끝의 온실」(김초엽) Flux 무드 이미지 배치 생성

더스트 시대(붉은 먼지·돔·떠도는 자매) → 프림 빌리지(숲속 마을·유리 온실·레이첼·지수·푸른 덩굴)
→ 습격과 흩어짐(씨앗) → 재건 이후(아영·해월의 덩굴·랑가노의 자매) → 푸른 지구.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
★ 배경은 BASE 에 넣지 않는다 — 넣으면 모든 장면을 덮어쓴다(초정리 편지 10/21). 장면마다 지정.
→ 돔·연구소·도시는 간판·표지판 위험 → 먼 실루엣·안개로. 인물마다 Korean/국적 명시. 밝은 톤.
→ 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_greenhouse.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-19 /health 로 9010 확인
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Greenhouse_at_the_End_of_the_Earth_flux"))   # 검수 후 옮긴다

BASE = ("cinematic painterly science fiction film still, soft natural light, bright enough to see clearly, not dark, "
        "palette of misty sage green, soft teal and warm amber, extreme shallow depth of field, soft bokeh, gentle film grain, "
        "quiet hopeful mood, no signboards, no signs, no logos, no labels, no screens with text, no text, no letters, no numbers, no writing anywhere")

K = "East Asian Korean people with black hair"
SCENES = [
    # 더스트 시대
    "a ruined empty city skyline far away shrouded in thick reddish dust haze, silent, wide shot, no signs",
    "fine glittering reddish dust particles drifting in a beam of sunlight, macro close-up, ominous yet beautiful",
    "a giant transparent dome over a distant city on a dusty plain, seen from far outside, hazy amber light",
    "people in simple masks and goggles walking in a line through a dusty wasteland, seen from behind, silhouettes",
    "two young Black African sisters in worn scarves and goggles walking hand in hand across a dusty plain, seen from behind",
    "a teenage Black African girl with a scarf over her mouth looking out from a ruined shelter, determined eyes, close-up",
    "an abandoned overgrown highway with rusted cars covered in dust, plants beginning to grow, soft light, no signs, no license plates",
    # 프림 빌리지
    "a small hidden village of wooden cabins in a deep misty forest, soft morning light, peaceful",
    "a beautiful old glass greenhouse on a forested hill above a small village, glowing warm light inside, misty",
    "inside a lush glass greenhouse full of green plants and hanging vines, sunlight through glass panes, serene",
    "a calm woman cyborg botanist with smooth pale synthetic skin and a mechanical arm tending plants in a greenhouse, close-up, gentle",
    f"a Korean woman mechanic in her thirties with short black hair repairing a cyborg's mechanical arm on a workbench, focused, close-up, {K}",
    f"a Korean woman and a cyborg woman standing close together among plants in a greenhouse, tender quiet moment, {K}",
    f"villagers working together in vegetable gardens in a forest clearing, soft light, children nearby, diverse people",
    "a teenage Korean girl singing alone on a hillside at sunset, eyes closed, wind in her hair, East Asian",
    "close-up of glossy dark green three-lobed ivy leaves on a creeping vine, dew drops, detailed",
    "a creeping ivy vine spreading over the ground and climbing a wooden fence, lush, morning light",
    "a forest village at night with creeping vines glowing soft blue everywhere, magical, serene, starry sky",
    "glowing blue particles rising from a dark ivy vine at night, magical, close-up",
    "a huge reddish dust storm approaching a forest village, dramatic sky, villagers watching",
    f"a Korean woman planting ivy cuttings in the soil around a village, hands in dirt, close-up, {K}",
    # 습격과 흩어짐
    "smoke rising from a burning forest village at dusk, distant, sorrowful",
    "people fleeing along a forest road at dawn carrying bundles, seen from behind",
    "close-up of hands placing small seeds into another person's palm, soft light",
    "small cloth pouches of seeds and cuttings of ivy packed into a traveler's bag, close-up",
    "a lone traveler planting a vine cutting in a dusty field far from home, wide shot, hopeful",
    "green ivy spreading across a dusty barren hillside over time, wide shot, soft light",
    "an Ethiopian highland lake landscape at dawn, soft mist, peaceful",
    # 재건 이후
    f"a Korean woman ecologist in her thirties with a field notebook kneeling to examine creeping ivy in a Korean mountain village, {K}",
    f"a little Korean girl standing in a garden at night watching faint blue lights glowing among weeds, wonder, {K}",
    f"an old Korean woman with grey hair sitting quietly in her overgrown garden, gentle smile, warm afternoon light, {K}",
    "a bright modern research laboratory with plant samples in glass jars, clean, soft daylight, no labels",
    f"a Korean woman scientist and an elderly Black African woman talking at a wooden table by a lakeside house, warm light, {K}",
    "an elderly cyborg woman sitting alone in a sunlit room full of plants, looking out the window, peaceful, close-up",
    "a lush green Earth landscape with forests and rivers under a clear blue sky, restored, hopeful, wide shot",
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

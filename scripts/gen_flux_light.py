#!/usr/bin/env python3
"""「우리가 빛의 속도로 갈 수 없다면」(김초엽) Flux 무드 이미지 배치 생성

표제작(낡은 우주 정거장의 할머니 과학자) → 순례자들(평화로운 마을·순례·지구) → 관내분실(마인드 도서관·엄마)
→ 공생가설(아기·옹알이·류드밀라의 행성) → 감정의 물성(감정을 담은 물건) → 스펙트럼·나의 우주 영웅(우주).
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 우주선·정거장 내부는 계기판·표시등 글자가 붙는다 → 「plain smooth panels, no displays, no screens with text」.
→ 도서관은 「glowing orbs of light」로 추상화. 인물마다 Korean 명시. 처음부터 밝은 톤.
→ 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_light.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-19 /health 로 9010 확인
OUT = Path("assets/images/If_We_Cannot_Move_at_the_Speed_of_Light_flux")   # 검수 후 옮긴다

BASE = ("luminous dreamy painterly science fiction film still, soft bright light, "
        "pastel cosmic palette of soft violet, pale blue and warm peach, bright enough to see clearly, not dark, "
        "extreme shallow depth of field, soft bokeh, gentle film grain, lonely yet tender mood, "
        "plain smooth panels, no displays, no screens with text, no signs, no logos, no text, no letters, no numbers, no writing anywhere")

K = "East Asian Korean people with black hair"
SCENES = [
    # 표제작 — 정거장의 할머니 과학자
    f"an elderly Korean woman scientist with white hair sitting alone by a large round window of an old quiet space station, looking out at distant stars, {K}",
    "an old abandoned space station floating in soft pastel space, faint light from one window, lonely",
    f"close-up of an elderly woman's wrinkled hand pressed against a round window with stars outside, {K}",
    "a distant blue planet seen through a round window, soft glow, far away",
    "a small old shuttle waiting at a docking bay of an empty space station, quiet, soft light, no markings",
    "a shimmering wormhole tunnel of light in deep space, luminous, awe",
    # 순례자들
    "a peaceful utopian village of white houses among green hills and flowers under a soft sky, gentle",
    f"a Korean teenage girl of eighteen in simple clothes standing at the edge of a meadow looking at the sky, curious, {K}",
    f"a young person in old-fashioned travel clothes boarding a sleek white transport ship at dawn, seen from behind, {K}",
    f"a returning young traveler weeping quietly while villagers look on, soft light, {K}",
    "a hidden archive room with rows of glowing glass panels and soft light, mysterious, no text",
    f"a young woman with a large scar on her face looking at her reflection, quiet strength, close-up, {K}",
    f"a Korean girl writing a letter on plain paper by a window at night, close-up of hands, no visible words, {K}",
    "Earth seen from space at dawn, luminous, hopeful",
    # 관내분실
    "a vast futuristic library hall filled with floating glowing orbs of light instead of books, serene, no text",
    f"a pregnant young Korean woman standing among floating orbs of light in a quiet library, searching, {K}",
    "a single orb of light flickering and fading among thousands of glowing orbs, lonely",
    f"a young Korean woman holding an old faded photograph of a woman's face, no visible text, close-up, {K}",
    f"a young Korean woman looking through dusty boxes of old belongings in a small apartment, soft daylight, {K}",
    f"a pregnant Korean woman placing a hand on her belly, gentle sunlight, close-up, {K}",
    # 공생가설
    f"a sleeping Korean baby in soft white blankets, gentle light, close-up, {K}",
    "a baby's head with soft glowing light patterns swirling like galaxies inside, surreal, dreamy",
    f"two Korean researchers in white lab coats looking at softly glowing brainwave patterns on a plain wall, amazed, {K}",
    "a painting of a beautiful alien landscape with violet skies and floating islands on an easel in a sunlit studio",
    "an alien planet with violet skies, two moons and floating islands, luminous, nostalgic",
    f"a young girl with dark hair painting an alien landscape, absorbed, warm light, {K}",
    # 감정의 물성
    "small smooth colorful stones and candles arranged on a white shelf like a shop display, soft light, no labels",
    "close-up of a hand holding a small dark grey smooth stone, melancholy, soft light, no labels",
    f"a young Korean woman sitting alone on a bed holding a small glowing stone, sad, soft window light, {K}",
    f"a Korean man watching a door close in a quiet apartment, regret, soft light, {K}",
    # 스펙트럼 · 우주 영웅
    "a lonely planet with five moons in a pastel sky, strange alien vegetation, dreamy",
    f"a Korean woman astronaut in a simple white suit standing on an alien shore looking up at many moons, {K}",
    f"a middle-aged Korean woman in a simple white spacesuit diving into a luminous ocean of light, surreal, {K}",
    # 결말
    "a tiny silver ship sailing slowly into an endless starry ocean, hopeful, luminous",
    "countless stars and soft nebula colors in deep space, peaceful, luminous",
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
            seed = 39000 + i * 100 + k * 7
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

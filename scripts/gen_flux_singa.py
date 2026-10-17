#!/usr/bin/env python3
"""「그 많던 싱아는 누가 다 먹었을까」(박완서) Flux 무드 이미지 배치 생성

1930년대 개풍 박적골 → 서울 현저동 산동네 → 인왕산 싱아 → 일제 말기 → 해방 → 6·25 → 텅 빈 서울.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 근대 도시 거리·가게·역은 간판 지옥(서울 1964·광문자전 교훈). 시골·산·풀·산동네 지붕·실내 맨벽·클로즈업 위주.
→ 인물마다 Korean 명시(메리골드 교훈). 처음부터 밝은 톤(밝기 ≥60).
→ 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_singa.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-17 /health 로 9010 확인
OUT = Path("assets/images/Who_Ate_Up_All_the_Shinga_flux")   # 검수 후 옮긴다

BASE = ("luminous nostalgic painterly film still, rural and old Korea in the 1930s to 1950s, bright soft daylight, "
        "warm faded film colors, soft green, ochre and pale sky blue, bright enough to see clearly, not dark, "
        "extreme shallow depth of field, soft bokeh, gentle film grain, tender nostalgic mood, "
        "no signboards, no signs, no calligraphy, no logos, no text, no letters, no numbers, no writing anywhere")

K = "Korean people with black hair"
SCENES = [
    # 박적골 유년
    "a small Korean thatched-roof farmhouse village nestled in green hills with rice paddies, 1930s, bright summer, no signs",
    f"a little Korean girl of six in a simple hanbok running through a green meadow with wildflowers, joyful, {K}",
    f"an old Korean grandfather in white hanbok and gat hat holding the hand of his little granddaughter on a country path, warm, {K}",
    f"a kind old Korean grandmother in white hanbok hugging a little girl on a wooden porch of a thatched house, {K}",
    "close-up of tall wild sorrel plants with reddish jointed stems and small white flowers on a sunny hillside",
    f"a little Korean girl peeling the reddish stem of a wild plant and tasting it, smiling, close-up, {K}",
    f"Korean village children in old simple clothes playing by a stream in summer, laughing, {K}",
    # 엄마와 상경
    f"a determined young Korean mother in plain hanbok with her hair in a bun, gazing into the distance, close-up, {K}",
    f"a little Korean girl crying silently while saying goodbye to her grandmother, tearful, soft light, {K}",
    f"a Korean mother holding her little daughter's hand walking along a long dirt road toward a distant city, seen from behind, {K}",
    "view from a moving old train window of passing green hills and fields, motion blur, no signs",
    # 현저동 산동네
    "a hillside slum of tiny tiled and tin roofs crowded on a steep slope in old Seoul, 1930s, seen from above, no signs",
    "a narrow steep stone alley stairway between earthen walls in an old hillside neighborhood, bright, no signs",
    f"a little Korean girl sitting alone on a doorstep of a tiny rented room, looking lonely, {K}",
    "a granite mountain ridge with pine trees above an old city, bright sky, no buildings with signs",
    # 아카시아 · 싱아
    "close-up of white acacia flower clusters hanging from branches in late spring sunlight",
    f"Korean schoolgirls picking and eating white acacia flowers on a hillside, laughing, {K}",
    f"a little Korean girl searching desperately through grass and bushes on a rocky mountain slope, anxious, {K}",
    f"a little Korean girl feeling sick and dizzy under a yellow sky on a mountainside, swaying, dreamy blur, {K}",
    "an empty patch of grass on a rocky hillside with no plants, wind, lonely",
    # 일제 말기 · 학교 · 책
    f"a Korean schoolgirl in loose work trousers and a plain blouse standing in a schoolyard, 1940s, serious face, no text, {K}",
    f"Korean schoolgirls crouching with hands over their heads during an air raid drill in a dusty schoolyard, {K}",
    f"a Korean family arguing quietly around a low table in a dim room, tense, 1940s, {K}",
    f"a Korean teenage girl absorbed in reading a book by the window, soft daylight, close-up, no visible text on pages, {K}",
    "a stack of old worn books on a wooden floor beside a window, close-up, no visible titles",
    # 해방 · 대학 · 전쟁
    f"joyful Korean crowd waving their hands in the street in August 1945, celebration, no flags with text, no signs, {K}",
    f"a young Korean woman of twenty in a plain blouse and skirt walking through a university campus lawn in spring, hopeful, no signs, {K}",
    "distant smoke rising over hills in summer 1950, ominous, no buildings with signs",
    f"a young Korean man in tattered clothes with a hollow exhausted face sitting against a wall, broken, {K}",
    f"a Korean family being questioned harshly by stern men in a bare room, fearful, 1950, {K}",
    # 1·4후퇴 · 텅 빈 서울 · 예감
    f"a long line of Korean refugees with bundles walking across a frozen river in winter, seen from afar, {K}",
    "an empty snowy hillside neighborhood of small roofs with no people, silent, winter daylight",
    f"a young Korean woman in a winter coat looking down from a hill at an empty silent snowy city, seen from behind, {K}",
    f"a young Korean woman's face, eyes suddenly resolute, close-up, winter light, {K}",
    "a single tall wild sorrel plant swaying in the wind on a bright hillside, hopeful, close-up",
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

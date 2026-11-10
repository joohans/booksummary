#!/usr/bin/env python3
"""「너무 한낮의 연애」(김금희) Flux 무드 이미지 배치 생성

좌천된 필용(시설관리팀 지하 사무실) → 한낮 도심을 걸어 패스트푸드점 창가에서 혼자 먹는 점심
→ 16년 전 어학원 강의실과 점심 테이블, 말이 많은 필용과 듣기만 하는 양희 → 「사랑하죠, 오늘도」
→ 사랑이 없어졌다는 말, 한낮 거리를 울며 걷는 필용 → 소극장 참여형 연극의 인공 어둠
→ 시골 마을 어귀의 거대한 느티나무 → 담담한 회상.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 간판·메뉴판·포스터·현수막·로고·화면 금지,
현대 한국 장면은 얕은 심도·민무늬 벽. 한국 인물은 「Korean … black hair」를 인물마다 명시.

    SEED_BASE=68000 .venv/bin/python scripts/gen_flux_midday.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Too_Bright_Outside_for_Love_flux"))   # 검수 후 옮긴다

BASE = ("cinematic film still, quiet Korean literary drama, soft natural daylight, bright enough to see clearly, not dark, "
        "shallow depth of field, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no numbers, no signs, no labels, no posters, no writing anywhere, no watermark, no signature")

PIL = "a tired Korean man of forty with short black hair in a plain grey suit without a tie"
YPIL = "a talkative Korean young man of twenty-four with black hair in a plain white shirt"
YANG = "a calm quiet Korean young woman of twenty-two with straight black shoulder-length hair in a plain beige sweater"
OYANG = "a calm Korean woman of thirty-eight with black hair tied back, in a plain black coat"

SCENES = [
    # 좌천
    f"{PIL} sitting alone at a plain grey metal desk in a bare basement office with concrete walls, fluorescent light, bright",
    f"{PIL} walking down a long plain concrete corridor carrying a toolbox, soft light, from behind",
    "close-up of a man's hands holding a plain ring of keys against a plain concrete wall, soft light",
    f"{PIL} standing on a rooftop at noon looking over a hazy city, bright midday sun",
    # 한낮의 점심
    f"{PIL} walking alone on a wide sunny city sidewalk at noon, crowd blurred, strong midday sun",
    f"{PIL} sitting alone by a large window eating a burger, bright noon light, blurred background, plain wall",
    "close-up of a paper-wrapped burger and a cup of coffee on a plain tray by a sunny window, no logos",
    "bright midday sunlight streaming through a large window onto empty plastic tables, soft focus",
    f"{PIL} looking up in surprise across a sunny street, blurred buildings behind",
    # 16년 전 — 어학원
    "a plain bright classroom with rows of desks and large windows, young students from behind, soft light",
    f"{YPIL} and {YANG} sitting side by side in a bright classroom, soft window light",
    f"{YPIL} and {YANG} sitting across from each other at a small table with trays by a sunny window, he talks, she listens",
    f"{YPIL} talking animatedly with his hands, bright window light, blurred background",
    f"{YANG} resting her chin on her hand, listening quietly, soft noon light, blurred background",
    f"close-up of {YANG}, calm unreadable expression, soft natural light",
    "two paper cups and crumpled napkins on a plain table in bright afternoon light, close-up",
    f"{YPIL} and {YANG} walking side by side on a sunny street in late summer, from behind, blurred city",
    # 고백
    f"{YANG} saying something simply across a table, calm face, warm noon light",
    f"{YPIL} frozen in surprise holding a cup, warm noon light, blurred background",
    f"{YANG} smiling faintly, looking down, soft light",
    "bright noon sun through a window making long shadows on a plain table, peaceful",
    f"{YPIL} and {YANG} standing on a sidewalk at noon facing each other, shy, shallow depth of field",
    # 사랑이 없어졌다
    f"{YANG} looking away out a window, calm and distant, soft grey light",
    f"{YPIL} walking alone on a crowded sunny street with tears on his face, crowd blurred",
    f"{YPIL} sitting alone on a stone step by a city stream at dusk, soft warm light",
    "an empty seat across a small table by a bright window, melancholy, soft focus",
    # 소극장
    "a small black box theater with a few rows of seats, warm stage light on a bare wooden stage, bright enough to see",
    f"{OYANG} standing quietly at the back of a small theater, warm soft light",
    f"{PIL} sitting in a small audience in a dim theater lit by warm stage light, his face half lit",
    "a single warm spotlight on an empty wooden chair on a bare stage",
    "audience members holding hands in soft warm light in a small theater, faces blurred",
    f"{PIL} and {OYANG} glancing at each other across a softly lit small theater",
    # 느티나무와 시골 마을
    "a huge old zelkova tree at the entrance of a quiet Korean countryside village, bright summer daylight",
    "close-up of thick peeling bark of an ancient zelkova tree, warm sunlight",
    "a low old house with a tiled roof in a country village after heavy rain, puddles, soft bright light",
    "a muddy village lane after a flood with clear blue sky, bright daylight",
    f"{YANG} pointing at a giant tree at the edge of a village, from behind, bright daylight",
    f"{YPIL} and {YANG} standing under a huge zelkova tree, small figures, bright summer light",
    "sunlight through the dense green leaves of a giant tree, looking up",
    # 현재와 회상
    f"{PIL} standing alone on a quiet street at noon, looking at the sky, bright",
    f"{PIL} riding a city bus by the window, sunlight on his face, blurred city outside",
    f"{OYANG} walking away along a sunlit tree-lined street, from behind",
    "a quiet sunlit city street at noon with trees and long shadows, no signs",
    f"{PIL} sitting under a big tree in a city park in bright afternoon light, thoughtful",
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
            seed = int(os.environ.get("SEED_BASE", "68000")) + i * 100 + k * 7
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

#!/usr/bin/env python3
"""「이중나선」(제임스 왓슨) Flux 무드 이미지 배치 생성

1951~53년 케임브리지·런던, 디엔에이 구조 경쟁 → 연구소·모형·엑스선 사진·인물·케임브리지 풍경.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 칠판(수식)·논문·책·신문·간판·라벨은 전부 글자다. 화면에 넣지 않는다.
   모형·도구·사진은 「blank」「unlabeled」로, 인물은 얼굴·손·뒷모습, 풍경은 강·자전거·안개.
→ 렌더러가 어둡게 처리하므로 처음부터 밝은 낮빛으로 받는다(서울 1964년 겨울 교훈, 숙향전에서 밝기 ≥90 확인).
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_doublehelix.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-13 /health 로 9010 확인
OUT = Path("assets/images/The_Double_Helix_flux")   # 검수 후 옮긴다

BASE = ("bright cinematic film still, early 1950s England, soft natural daylight, warm cream, teal and brass palette, "
        "gentle film grain, hopeful and curious mood, shallow depth of field, "
        "no blackboards, no papers with writing, no books, no newspapers, no signs, no labels, "
        "no text, no letters, no numbers, no equations, no writing anywhere")

SCENES = [
    # 도입 · 사진 51
    "close-up of a young man's astonished face with wide eyes and parted lips, crew cut hair, 1950s, bright window light",
    "a glowing X-shaped diffraction pattern of dark spots on a round photographic film held up against a bright window, close-up, no markings",
    "a woman scientist's hands in a lab coat carefully mounting a thin fiber in a brass X-ray camera, bright lab light",
    # 케임브리지 도착
    "a young lanky American man in a tweed jacket riding a bicycle along a quiet riverside path in Cambridge on a bright autumn morning",
    "punts drifting on a calm river past willow trees and old stone college walls in soft morning mist, bright",
    "two men in 1950s tweed jackets talking excitedly while walking across a sunny grass courtyard of an old stone college, seen from behind",
    "close-up of a tall man in his thirties with a big grin, gesturing animatedly while talking, 1950s, warm light",
    # 연구실 · 모형 만들기
    "a cluttered bright 1950s laboratory with wooden benches, glass flasks and brass instruments, sunlight streaming in, nobody there",
    "two young scientists in shirtsleeves bending over a tall metal scaffold model of interlinked rods and balls, bright lab",
    "close-up of hands joining small metal plates and rods with clamps to build a molecular model, warm light",
    "a three-stranded twisted metal molecular model standing on a lab bench, slightly lopsided, bright daylight",
    # 프랭클린 · 킹스 칼리지
    "a serious young woman scientist with dark hair in a white lab coat looking through the eyepiece of a large X-ray apparatus, focused, bright lab",
    "close-up portrait of a confident young woman scientist in the early 1950s, intelligent eyes, short dark hair, soft daylight",
    "a woman scientist with folded arms frowning at two young men standing beside a metal model, tense, bright room",
    # 금지 · 실망
    "a stern elderly professor with a white mustache in a dark suit shaking his head in a sunny wood-panelled office",
    "two young men sitting dejected on a bench by a river, hands in pockets, bright cloudy afternoon",
    # 폴링 · 경쟁
    "a distinguished older American chemist with white hair and a warm smile, close-up portrait, bright sunny background",
    "a young man laughing with relief while holding a blank envelope in a sunny corridor, 1950s",
    "a fast steam train crossing the green English countryside on a bright winter day, motion blur",
    # 런던 · 사진을 봄
    "a quiet bright lab office in London, a middle-aged man in glasses holding up a photographic film to show a young visitor, both lit by window light",
    "extreme close-up of a crisp X-shaped pattern of dark dots on a glowing photographic plate, scientific beauty",
    "a young man walking briskly along the platform of a busy 1950s railway station with steam and sunlight, determined",
    # 마분지 염기 · 발견
    "close-up of hands cutting flat geometric shapes out of plain grey cardboard with scissors on a wooden desk, morning light",
    "plain unmarked cardboard puzzle-like shapes being fitted together in pairs on a clean wooden desk, bright window light, close-up",
    "a young man's face lighting up with sudden realization, bright morning light, 1950s",
    "a beautiful tall double helix metal model of rods and plates gleaming in a sunlit lab, elegant spiral",
    "two scientists standing proudly beside a tall double helix model, smiling, warm afternoon light",
    # 이글 펍 · 생명의 비밀
    "a cozy old English pub interior at lunchtime, wooden beams, warm light, a tall man raising a glass with excitement, no signs",
    "two pints of beer on a wooden pub table in warm sunlight, close-up",
    # 발표 · 노벨상
    "a glowing abstract double helix spiral of light rising through soft clouds, luminous and hopeful",
    "an elegant formal ceremony hall with chandeliers and men in white tie tails, bright and grand, 1960s, no text",
    "a gold medal glinting in soft light on dark velvet, close-up, blank surface without any engraving",
    # 프랭클린의 부재 · 에필로그
    "an empty lab stool beside an X-ray apparatus in a quiet bright lab, a white lab coat hanging on a hook",
    "a woman in a 1950s coat walking alone along a misty riverside path in soft morning light, seen from behind",
    "a single white rose lying on a lab bench in soft window light, close-up",
    # 생명 · 현대
    "a glowing blue and gold double helix spiraling upward against a bright white background, abstract, clean",
    "a cell dividing under a microscope view, soft glowing colors, abstract and beautiful",
    "a newborn baby's tiny hand gripping an adult finger, soft bright light, close-up",
    "sunlight through tall trees in a green forest with dust motes, life and growth",
    "an old man with white hair looking thoughtfully at a double helix model in a bright modern room, seen in profile",
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
            seed = 81000 + i * 100 + k * 7
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

#!/usr/bin/env python3
"""「새의 선물」 Flux 무드 이미지 배치 생성 (스톡 보충용)

1969년 남도 소읍은 무료 스톡에 거의 없다 → 장면을 Flux 로 채운다.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 이 작품의 핵심 소재가 「편지」「양장점·테라·미장원·사진관 가겟집」「읍내 버스」「산부인과」지만
   편지·책·간판·상점가·버스·병원 건물은 장면에서 아예 뺀다. Flux 는 인물·마당·들판·눈길·불빛만 그린다.
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).
"""
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

FLUX = "http://192.168.0.150:9010/generate"   # 포트는 /health 로 확인(2026-10-05 9010 정상)
OUT = Path("assets/images/The_Birds_Gift_flux")   # 스톡 AI 검증이 Flux 까지 깎지 않도록 따로 받아 검수 후 옮긴다

BASE = ("nostalgic painterly film still, rural South Korea in the late 1960s, a small southern country town, "
        "soft natural light, faded warm amber and muted teal palette, film grain, bittersweet coming-of-age mood, "
        "no text, no signboards, no letters, no writing, no posters, no banners")

SCENES = [
    # 열두 살 진희 · 두 개의 나
    "a sharp-eyed twelve-year-old Korean girl with short bobbed hair sitting on a wooden veranda, watching adults with a knowing look",
    "a twelve-year-old girl in a 1960s school uniform standing alone under a persimmon tree heavy with orange fruit",
    "a young girl's face half in shadow beside a paper-screen door, one eye watching quietly",
    "a girl smiling politely at adults while her shadow on the courtyard ground looks still and serious",
    # 감나무집
    "a traditional tile-roofed house with a courtyard, a stone well in the center and a large persimmon tree, autumn afternoon",
    "laundry drying on lines across a hanok courtyard on a bright windy Sunday, white sheets glowing",
    "an elderly Korean grandmother in plain hanbok squatting by a stone well washing vegetables, warm light",
    "a stone well in a courtyard at dusk with a bucket on its rim, persimmon leaves on the ground",
    # 이웃들
    "a tired young Korean woman in a 1960s dress standing alone on a dusty country road as a cloud of dust settles, empty road ahead",
    "a vintage black sewing machine on a wooden table by a window, scraps of colorful fabric, soft light, no text",
    "a gossiping middle-aged Korean woman leaning over a low stone wall talking to a neighbor, 1960s clothing",
    "a chubby innocent Korean boy in shorts playing with a hoop in a dirt alley, afternoon",
    # 이모 · 첫사랑
    "a naive pretty Korean woman in her early twenties with a 1960s hairstyle, daydreaming by a window, cheeks flushed",
    "a young woman standing outside a military camp fence holding a cloth-wrapped lunch box, waiting nervously",
    "a young woman crying alone on the edge of a wooden veranda at night, a single lamp",
    "a slim young man in a white shirt playing a harmonica on a grassy hill at sunset, seen as a silhouette, a goat grazing beside him",
    "a twelve-year-old girl stopping on a hillside path at sunset, listening to distant harmonica music",
    "a gentle young man in a white shirt talking softly with a young woman under a persimmon tree, a little girl watching from a doorway",
    # 공장 화재
    "a distant factory burning at night beyond rice fields, orange glow and smoke against a dark sky, villagers' silhouettes watching",
    "a young woman kneeling in grief in a dark yard lit by a faraway orange fire glow",
    # 눈길
    "a snowy country road at dusk, a young woman collapsed in the snow and a small girl kneeling beside her",
    "a rough young man carrying a weak young woman on his back through falling snow along a rural road, a little girl following",
    "an empty snow-covered country road between bare fields, grey winter sky, lonely",
    # 끝 · 서른여덟
    "a woman in her late thirties driving at night on a highway, city lights blurred, reflective face",
    "an old green parrot on a branch offering a sunflower seed toward a setting sun, surreal and poetic",
    "sunflowers wilting in a small courtyard garden at the end of summer, golden light",
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
            seed = 34000 + i * 100 + k * 7
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

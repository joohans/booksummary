#!/usr/bin/env python3
"""「대온실 수리 보고서」(김금희) Flux 무드 이미지 배치 생성

창경궁 대온실(1909, 흰 철골 + 유리 온실)의 안팎 → 보수공사 현장(비계·유리 패널·발굴 흙)
→ 건축사사무소의 도면 작업 → 2003년 원서동의 중학생 영두와 낙원하숙(마당·작은 방·할머니)
→ 1900년대 대온실을 짓는 일본인 원예가와 열대 식물 → 춘당지 버드나무·궁궐 숲의 사계절 → 화해와 봄.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 현판 달린 궁궐 건물·간판 거리 금지,
인물은 전부 「Korean … black hair」 명시(서양인 방지), 도면·종이는 「blank」.

    SEED_BASE=71000 .venv/bin/python scripts/gen_flux_grand_greenhouse.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Grand_Greenhouse_Repair_Report_flux"))   # 검수 후 옮긴다

BASE = ("cinematic film still, contemporary Korean drama film, soft natural daylight, shallow depth of field, "
        "bright enough to see clearly, not dark, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no numbers, no signs, no labels, no writing anywhere, no watermark, no signature")

YD = "a quiet Korean woman in her thirties with shoulder-length black hair in a plain grey cardigan"
GIRL = "a thin fourteen-year-old Korean girl with short black hair in a plain white school shirt"
LISA = "a sharp-eyed fourteen-year-old Korean girl with long black hair tied back in a plain navy sweater"
GRAN = "a dignified elderly Korean woman with neat short white hair in a plain beige blouse"
FUKU = "a serious young Japanese gardener with short black hair in a plain 1900s dark work jacket"
GH = "an old white-painted iron and glass Victorian-style greenhouse"

SCENES = [
    # 대온실
    f"{GH} standing in a quiet palace garden among tall trees, bright spring morning",
    f"inside {GH}, lush tropical plants and palm leaves under white iron arches, sunlight through glass",
    "close-up of white-painted curved iron frames and old glass panes of a greenhouse roof, blue sky, bright",
    "close-up of a cracked old glass pane in a white iron frame, sunlight, shallow focus",
    f"{GH} reflected in a still pond with willow trees, bright day",
    "a large fan palm and ferns inside a sunlit glass greenhouse, soft green light",
    # 보수공사
    f"{GH} partly covered with scaffolding and white protective sheets, construction workers in plain helmets, bright day",
    f"{YD} in a plain white safety helmet standing inside a greenhouse under repair, looking up at the iron roof, bright",
    "workers in plain grey uniforms carefully removing old glass panes from a white iron greenhouse frame, bright",
    "an archaeological dig pit inside a greenhouse floor, exposed brown soil and old brick foundations, soft daylight",
    "close-up of hands in white gloves brushing soil from an old buried brick wall with a small brush, shallow focus",
    f"{YD} kneeling at the edge of an excavation pit, staring down in shock, soft daylight",
    "a small old glass bottle half buried in brown soil, close-up, soft light",
    # 사무소와 일상
    f"{YD} at a wooden desk in a bright architecture office, looking at plain blank architectural sketches, window light",
    "close-up of a pencil and a blank sheet of tracing paper on a drafting table, soft window light",
    f"{YD} walking along a long old stone palace wall under trees, autumn leaves, bright afternoon",
    f"{YD} sitting alone on a bench in a palace garden, lost in thought, soft daylight",
    f"{YD} and a Korean woman friend with black hair and her small daughter eating dinner together at a small home table, warm light, plain walls",
    # 2003년 원서동·낙원하숙
    "a narrow quiet old Seoul alley with low tiled-roof houses beside a long stone wall, no signs, bright summer afternoon",
    "the small courtyard of an old Korean house with potted plants and a wooden porch, plain walls, bright morning",
    f"{GIRL} carrying a heavy bag, arriving at the wooden gate of an old house, nervous, bright day",
    f"{GRAN} standing in a sunny courtyard of an old house, looking kindly, plain walls",
    f"{GRAN} and {GIRL} sitting together on a wooden porch, peeling fruit, soft afternoon light",
    f"{LISA} glaring coldly from a doorway, plain walls, soft light",
    f"{GIRL} and {LISA} sitting far apart on the same wooden porch, not looking at each other, soft light",
    f"{GIRL} alone in a small plain room with a low desk, looking out of the window, soft light",
    f"{GIRL} and a shy Korean boy of fourteen with black hair in a plain white shirt walking side by side under ginkgo trees, bright day",
    f"{GIRL} crying alone by a stone wall, afternoon shade, soft light",
    "a long dinner table in an old Korean boarding house with several Korean people of different ages eating together, warm light, plain walls",
    # 1900년대 대온실 건설
    f"period film still, 1909, {FUKU} standing among rows of young tropical seedlings in pots, bright daylight",
    "period film still, 1909, workers in plain white Korean clothes and Japanese workers raising white iron arches of a greenhouse, bright sky",
    f"period film still, {FUKU} carefully planting a small palm tree inside a new glass greenhouse, sunlight",
    f"period film still, close-up of {FUKU}'s hands holding a seedling, soft light",
    "period film still, a little Japanese girl with black bob hair in a plain kimono standing alone among greenhouse plants, soft light",
    "period film still, a crowd of 1910s visitors in plain clothes strolling in a palace garden turned into a public park, cherry blossoms, bright",
    "period film still, cherry blossom trees lit softly at evening in an old palace garden, visitors, warm light",
    # 계절과 자연
    "a large weeping willow by a calm pond in an old palace garden, soft spring light",
    "a pond with lotus leaves and old pine trees in a palace garden, misty morning, bright",
    "snow falling softly on a white greenhouse among bare trees, bright winter day",
    "autumn maple trees around a white glass greenhouse, golden sunlight",
    "close-up of tropical orchids blooming inside a greenhouse, soft light, shallow focus",
    # 결말 쪽
    f"{YD} and {GRAN} walking slowly together inside a sunlit glass greenhouse among plants",
    f"{YD} standing inside a restored white glass greenhouse, sunlight streaming in, peaceful smile",
    f"{GH} glowing in soft golden evening light, restored and clean, among green trees",
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
            seed = int(os.environ.get("SEED_BASE", "71000")) + i * 100 + k * 7
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

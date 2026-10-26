#!/usr/bin/env python3
"""「나무를 심은 사람」(장 지오노) Flux 무드 이미지 배치 생성

1913 프로방스 고원 황무지·폐허 마을·마른 우물 → 양치기 엘제아르 부피에(쉰다섯, 회색 콧수염)·도토리 백 개·쇠막대
→ 1차대전(참호 대신 들판의 병사 뒷모습) → 1920 떡갈나무 숲·개울·양 대신 벌통 → 너도밤나무·자작나무
→ 2차대전 뒤 되살아난 마을·사람들 → 노인의 마지막 모습.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]). ★ 배경은 장면별로만(BASE 금지, 초정리 편지 10/21).
→ 마을은 간판 없는 돌집·샘터만. 밤 장면 금지(b<60). 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_tree.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-19 /health 로 9010 확인
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Man_Who_Planted_Trees_flux"))   # 검수 후 옮긴다

BASE = ("quiet literary film still, soft natural daylight, bright enough to see clearly, not dark, "
        "muted pastel palette of sage green, warm ochre, lavender and pale sky blue, extreme shallow depth of field, soft bokeh, gentle film grain, "
        "serene, patient, hopeful mood, no signboards, no signs, no logos, no labels, no text, no letters, no numbers, no writing anywhere")

OM = "a lean weathered old French shepherd with a grey moustache, wool jacket and felt hat"
YM = "a young French hiker in 1913 clothes with a canvas rucksack"
SCENES = [
    # 1913 황무지
    "a vast barren treeless upland plateau in Provence under a bright hazy sky, dry grass and wild lavender, wind",
    f"{YM} walking alone across a barren treeless highland, seen from behind, bright daylight",
    "ruined abandoned stone houses of a deserted hilltop hamlet in Provence, roofless walls, bright daylight, no signs",
    "close-up of a dry cracked stone well with no water, bright daylight",
    "wild lavender and dry grass bending in the wind on a bare hillside, bright daylight, close-up",
    # 양치기
    f"{OM} standing with a flock of sheep on a bare hillside, a dog beside him, bright daylight",
    f"{OM} offering a gourd of water to {YM}, bright daylight, kind",
    "a small tidy stone shepherd's cottage alone on a barren slope, smoke from the chimney, bright daylight, no signs",
    "a simple wooden table inside a stone cottage with a bowl of soup and bread, warm soft window light",
    "close-up of weathered old hands sorting acorns on a wooden table, soft window light",
    "a neat pile of one hundred perfect brown acorns on a wooden table, close-up, soft light",
    f"{OM} pushing an iron rod into dry ground to make a hole, close-up, bright daylight",
    "close-up of an old hand dropping an acorn into a small hole in dry soil, bright daylight",
    f"{OM} walking across an empty hillside carrying a small sack, sheep far behind, bright daylight, seen from behind",
    "a tiny oak seedling sprouting from dry stony soil, close-up, bright morning light",
    # 1차대전
    "a young French soldier in a 1914 horizon-blue uniform sitting alone on a grassy field, tired, seen from the side, soft overcast daylight",
    "a field of red poppies under a pale sky, soft daylight",
    # 1920 숲
    f"{YM} older and thinner, standing amazed at the edge of a young oak forest on a hillside, bright daylight",
    "a young oak forest covering a once-barren hillside, sunlight through green leaves, bright daylight",
    "a clear stream flowing over stones through a young green forest, bright daylight",
    f"{OM} tending wooden beehives at the edge of a young forest, bees in sunlight, bright daylight",
    "rows of rustic wooden beehives in a meadow with wildflowers, bright daylight, no labels",
    "a grove of slender white birch trees with sunlight, bright daylight",
    "a beech forest with soft green light and fallen leaves, bright daylight",
    "close-up of fresh green oak leaves with dew in morning sunlight",
    # 숲과 마을
    "a lush green valley full of forests and meadows in Provence, a stream glinting, bright daylight, aerial view",
    "a restored small stone village with flowering gardens and a fountain, bright daylight, no signs, no shop fronts",
    "children running through a sunny meadow at the edge of a forest, bright daylight, seen from behind",
    "a young family planting vegetables in a garden beside a stone house, bright daylight",
    "a stone village fountain with clear running water and potted flowers, close-up, bright daylight, no plaques",
    f"{OM}, very old now, sitting peacefully on a bench beneath a great oak, eyes closed, dappled sunlight",
    f"{OM}, very old, walking slowly into a sunlit forest with a staff, seen from behind",
    "sunbeams streaming through a tall mature oak forest, bright daylight",
    "a single acorn resting on a mossy stone in a forest, close-up, soft light",
    "a panoramic view of green forested hills where once was desert, bright clear sky, hopeful",
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

#!/usr/bin/env python3
"""「인간의 굴레에서」(서머싯 몸) Flux 무드 이미지 배치 생성

1880~1900년대 영국 — 겨울 아침 어머니의 죽음 → 켄트 바닷가 목사관(큰아버지·큰어머니) → 기숙학교 운동장
→ 하이델베르크 강변·언덕 → 런던 회계 사무소 → 파리 화실·카페·뤽상부르 정원, 늙은 시인 크론쇼와 페르시아 양탄자
→ 런던 의학교·찻집의 밀드레드 → 가난·템스 강변 노숙 → 애설니 가족의 따뜻한 식탁·홉 따기 → 샐리, 시골 바닷가 햇빛.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 간판·상점 정면·책등·신문·편지 글씨·시계 문자판·벽 액자 금지.
35mm period film still BASE(모서리 서명 0 실측). 영국 인물이라 국적은 「English」로 명시.

    SEED_BASE=65000 .venv/bin/python scripts/gen_flux_bondage.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Of_Human_Bondage_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still, Edwardian England around 1900, quiet literary drama, soft natural daylight, bright enough to see clearly, not dark, "
        "muted palette of warm cream, faded sage green, soft brown and pale sky blue, shallow depth of field, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no numbers, no signs, no labels, no writing anywhere, no watermark, no signature")

BOY = "a thin pale English boy of nine with short brown hair, in a dark Victorian wool jacket"
TEEN = "a shy thin English schoolboy of fifteen with brown hair, in a dark school blazer"
PHILIP = "a thoughtful thin young English man in his early twenties with brown hair, in a plain dark tweed suit"
UNCLE = "a stern elderly English vicar with grey side whiskers, in a black clerical coat"
AUNT = "a gentle frail elderly English woman with grey hair in a bun, in a plain dark Victorian dress"
CRONSHAW = "a shabby old English poet with a fat tired face and thinning hair, in a worn black coat"
MILDRED = "a thin pale young English woman with fair hair pinned up, cold indifferent expression, in a plain black waitress dress with a white apron"
SALLY = "a calm healthy young English woman with auburn hair, rosy cheeks, in a plain blue cotton dress"
ATHELNY = "a lively small English man in his forties with a pointed beard, in a plain brown jacket"

SCENES = [
    # 유년 — 어머니의 죽음, 목사관
    "a grey winter morning seen through tall lace curtains of a Victorian bedroom, pale cold light, quiet and sad",
    f"{BOY} sitting alone on the edge of a bed in a plain Victorian bedroom, grey morning light",
    "a small black mourning hat and a pair of children's gloves on a plain wooden chair, soft grey light",
    "an old grey stone vicarage with ivy on the walls and a quiet garden, overcast soft daylight, English countryside",
    f"{UNCLE} sitting stiffly at a plain dining table, soft window light",
    f"{AUNT} smiling kindly, soft window light in a plain parlour",
    f"{BOY} looking out a vicarage window at a grey sea far away, soft light",
    f"{BOY} walking along an empty shingle beach on the Kent coast, grey sea, soft overcast light",
    # 기숙학교 — 굽은 발
    f"{TEEN} standing alone at the edge of a wide green school playing field while other boys run in the distance, soft daylight",
    "close-up of a boy's worn black leather boot, one foot turned slightly inward, on an old wooden floor, soft light",
    f"{TEEN} sitting alone on a stone step in an old school cloister, head down, soft daylight",
    f"{TEEN} kneeling in prayer beside a plain iron bed in a dim dormitory, soft morning light",
    # 하이델베르크
    "a calm river winding through a German valley with green wooded hills and red roofs far away, bright summer morning",
    f"{PHILIP} walking on a green hillside path above a river valley, from behind, bright summer light",
    f"{PHILIP} sitting on a grassy hill under a tree, looking at the open sky, free and thoughtful, bright summer light",
    # 런던 회계 사무소
    f"{PHILIP} sitting bored at a high wooden desk in a dim plain office, grey window light, bare walls",
    "a grey rainy London street of plain brick terraced houses, soft overcast light, no shop signs",
    # 파리
    "a sunlit painting studio in Paris with tall windows, wooden easels with blank canvases, soft bright light",
    f"{PHILIP} painting at a wooden easel in a bright studio, canvas seen from behind, soft daylight",
    "close-up of a painter's palette with thick oil paint and brushes, soft warm light",
    f"{PHILIP} and {CRONSHAW} sitting at a small marble cafe table outdoors, two glasses, soft warm afternoon light, blurred plain background",
    f"{CRONSHAW} talking with half-closed eyes over a glass of pale green absinthe, soft warm light, blurred plain background",
    "the Luxembourg Garden in Paris, chestnut trees and green iron chairs, bright soft afternoon light",
    "close-up of an old Persian carpet with an intricate red, blue and gold woven pattern, soft warm light",
    "an old hand-woven Persian rug spread on a plain wooden floor, sunlight across its pattern",
    f"{PHILIP} standing alone in a bright studio before a blank canvas, sad and resigned, soft light",
    # 런던 의학교 · 밀드레드
    f"{PHILIP} walking alone along the Thames embankment in grey London daylight, from behind",
    "a plain London tea room interior with small marble tables and white teacups, soft window light, blurred background",
    f"{MILDRED} standing beside a small marble table, looking away coldly, soft window light, blurred background",
    f"{PHILIP} gazing longingly across a small tea table, soft window light, blurred background",
    f"{MILDRED} and {PHILIP} sitting apart on a park bench, she looks away bored, soft overcast light",
    "a bouquet of violets left on an empty marble table beside a cold teacup, soft light",
    "a shabby rented room with torn curtains and overturned chairs, morning light through a window",
    f"{PHILIP} sitting alone in a small dim rented room, head in his hands, grey window light",
    # 가난
    f"{PHILIP} in a worn dark coat sitting alone on a stone bench by the river at dawn, hungry and exhausted, pale light",
    "a grey misty dawn over the Thames river with a stone bridge, soft pale light",
    # 애설니 가족 · 홉 따기
    f"{ATHELNY} laughing at a crowded family dinner table with plain bread and stew, warm window light",
    "a warm plain kitchen with a big wooden table, bread, a teapot and children's cups, golden afternoon light",
    "a green hop garden in Kent with tall vines on poles, bright late summer sunlight",
    f"{SALLY} picking hops among tall green vines, bright late summer sunlight",
    f"{SALLY} and {PHILIP} walking along a country lane between green hedges, golden evening light",
    # 결말
    f"{PHILIP} smiling quietly, sitting on a grassy cliff above the sea, bright sunlight",
    "a small fishing village harbour on the English coast under bright sun, calm sea, white cottages",
    "the sun shining brightly over a calm blue sea and green English fields, peaceful and hopeful",
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
            seed = int(os.environ.get("SEED_BASE", "65000")) + i * 100 + k * 7
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

#!/usr/bin/env python3
"""「좀머 씨 이야기」(파트리크 쥐스킨트) Flux 무드 이미지 배치 생성

1950년대 남독일 호숫가 마을(보덴 호 연상) → 나무 타는 소년·하늘을 날 수 있다는 믿음 → 빈 배낭·호두나무 지팡이로 끝없이 걷는 좀머 씨
→ 우박 폭풍 속 「날 좀 내버려 두시오」 → 카롤리나와의 약속 → 큰 자전거·피아노 수업·풍켈 선생 → 나무 위의 결심과 좀머 씨의 신음
→ 성장한 소년·호수로 걸어 들어가는 좀머 씨·침묵.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 간판·자동차 번호판·악보·책·신문 금지, 자연·호수·숲·길 위주.
★ 35mm period film still BASE. 배경은 장면별로만. 밤 장면 금지(밝기 ≥60). 인물은 국적·나이·머리색 명시.

    SEED_BASE=45000 .venv/bin/python scripts/gen_flux_sommer.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Story_of_Mr_Sommer_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still, 1950s rural southern Germany, soft natural daylight, bright enough to see clearly, not dark, "
        "muted warm palette of meadow green, lake blue, beige and brown wool, shallow depth of field, light film grain, "
        "no logos, no text, no letters, no signs, no numbers, no writing anywhere, no watermark, no signature")

BOY = "a thin German boy about eight years old with short light brown hair, in shorts and a knitted sweater"
SOM = "a tall gaunt German man in his fifties with a thin face, wearing a long dark loden coat and a wide straw hat, an empty rucksack on his back, a long walnut walking stick"
GIRL = "a German girl about eight years old with dark pigtails in a simple cotton dress"
TEEN = "a German teenage boy about fourteen with light brown hair, in a wool jacket"

SCENES = [
    # 1 호숫가 마을의 어린 시절
    "a calm wide lake with gentle hills and a small village with red tile roofs on the far shore, morning haze, wide view",
    "an orchard of old fruit trees on a green slope above a lake, summer morning",
    f"{BOY} climbing high into the branches of a tall beech tree, seen from below, sunlight through leaves",
    f"{BOY} sitting on a high tree branch looking out over fields and a distant lake, peaceful",
    f"{BOY} standing on a grassy hilltop with arms spread wide as if about to fly, his coat flapping in the wind, cloudy bright sky",
    f"close-up of {BOY} with a dreamy expression looking up at the sky",
    # 2 걷는 남자 좀머 씨
    f"{SOM} walking fast along an empty country road between meadows, seen from behind, morning light",
    f"{SOM} striding along a lakeside path, the stick swinging forward, overcast bright day",
    f"close-up of a long walnut walking stick striking a gravel path mid-stride, motion",
    f"close-up of worn leather boots walking fast on a dusty country lane",
    f"{SOM} walking across a wide field of tall grass toward a forest edge, small in the frame",
    f"{SOM} walking along a snowy country road in winter, bright white daylight",
    f"{SOM} walking through autumn woods with falling yellow leaves, determined",
    f"villagers in 1950s German clothes standing by a wooden fence watching a tall thin man walk past in the distance",
    "a small plain whitewashed house with a steep roof at the edge of a German village, quiet afternoon",
    # 3 우박 폭풍
    "dark storm clouds gathering over open German farmland, wind bending the trees, still enough daylight",
    "heavy hailstones bouncing on a country road and grass, close-up, grey daylight",
    f"{SOM} walking alone through pouring rain and hail on a country road, soaked, head down",
    f"view from inside an old 1950s car through a rain-streaked windshield, a tall thin man walking in the storm ahead, blurry",
    f"close-up of {SOM} soaked in the rain turning his face away with a pained expression",
    f"{BOY} in the back seat of an old car looking out a wet window, worried face, soft grey light",
    # 4 카롤리나
    f"{GIRL} and {BOY} walking side by side along a dirt path by a meadow, shy, summer afternoon",
    f"close-up of {GIRL} smiling over her shoulder in a sunny meadow",
    f"{BOY} sitting alone on a wooden fence waiting, looking down the empty road, late afternoon",
    # 5 큰 자전거와 피아노 수업
    f"{BOY} struggling to ride an oversized black 1950s lady's bicycle along a country road, wobbling",
    f"{BOY} pushing a large black bicycle up a steep hill road, tired",
    f"{BOY} and the large bicycle fallen sideways on a gravel road, the boy getting up, scraped knee",
    "an upright wooden piano in a dim old-fashioned parlor with lace curtains and potted plants, soft window light",
    f"{BOY} sitting stiffly at an upright piano, small hands on the keys, nervous",
    "a stern elderly German woman with grey hair in a tight bun and a high-collared dark dress, standing with arms crossed, old parlor",
    "close-up of a child's hands hesitating over black and white piano keys",
    f"close-up of {BOY} with tears in his eyes, humiliated, soft light",
    # 6 나무 위의 결심
    f"{BOY} running away across a field with clenched fists, angry and crying, overcast",
    f"{BOY} climbing very high in a huge old spruce tree, determined face, seen from below",
    f"{BOY} sitting at the top of a tall tree looking down at the ground far below, wind in his hair",
    f"looking straight down from the top of a tall tree at a grassy clearing far below, dizzying height",
    f"{SOM} below a tall tree hastily eating a piece of bread, sitting on the grass, seen from high above",
    f"{SOM} lying on his back in the grass with eyes shut, face twisted in anguish, high angle view",
    f"close-up of {BOY} in the tree branches watching below in shock and silence",
    f"{BOY} slowly climbing down a tree trunk in late afternoon light, calm face",
    # 7 성장과 호수
    f"{TEEN} riding a bicycle along a lakeside road in the late afternoon, golden light",
    f"{SOM} walking slowly into a calm lake, water up to his waist, straw hat on, seen from behind, bright evening light",
    "a straw hat floating on the calm surface of a lake, gentle ripples, soft light",
    f"{TEEN} standing still by his bicycle on a lakeshore, staring at the empty calm water, long shadows",
]

assert len(SCENES) == 44, len(SCENES)


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
            seed = int(os.environ.get("SEED_BASE", "45000")) + i * 100 + k * 7
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

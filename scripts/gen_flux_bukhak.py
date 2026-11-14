#!/usr/bin/env python3
"""「북학의」(박제가) Flux 무드 이미지 배치 생성

18세기 조선의 가난한 마을·진흙길·지게 → 서자 선비 박제가 → 압록강을 건너 요동 벌판 → 청나라 베이징 길의 수레·벽돌 성벽
→ 벽돌 가마·기와·배 → 귀국 후 붓으로 기록하는 밤 → 수레·벽돌·우물·바다 무역선 → 유배지 북쪽 산골 → 열린 바다.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 조선·청 시장·관아·현판은 한자 간판이 붙으므로 금지.
가게 거리 대신 「wide dirt road / brick city wall seen from outside / close-up of goods」. 책·두루마리 글씨 대신 붓·벼루·빈 종이.
BASE 는 사진풍 「35mm period film still」(모서리 서명 0 실측), 「drama」 금지.

    SEED_BASE=75000 .venv/bin/python scripts/gen_flux_bukhak.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Bukhakui_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still, 18th-century East Asian historical film, soft natural daylight, "
        "bright enough to see clearly, not dark, light film grain, "
        "no logos, no text, no letters, no characters, no calligraphy, no signs, no signboards, no writing anywhere, no watermark, no signature")

PARK = "a lean Korean scholar in his late twenties with a thin moustache, wearing a plain white hanbok robe and a black horsehair gat hat"
PARK_NOHAT = "a lean Korean scholar in his late twenties with a thin moustache and a topknot, wearing a plain white hanbok robe"
FARMERS = "poor Korean farmers in worn white cotton hanbok clothes"
QING = "Chinese men in plain blue cotton Qing dynasty robes with long braided queues"

SCENES = [
    # 조선 — 가난한 현실
    f"{FARMERS} carrying heavy loads on wooden A-frame jige packs along a muddy narrow mountain path, overcast but bright",
    "a narrow muddy dirt path between rice paddies in 18th-century Korea, thatched farmhouses in the distance, soft daylight",
    "a small Korean thatched-roof farmhouse with mud walls in a quiet valley, autumn daylight",
    f"{FARMERS} pulling a heavy load by hand across a rough stream with no bridge, soft daylight",
    "close-up of an empty wooden rice bowl on a straw mat, soft light, shallow depth of field",
    "a Korean ox carrying bundles of firewood on its back along a rocky mountain trail, soft daylight",
    # 박제가 — 서자 선비
    f"{PARK} standing alone at the edge of a misty pine forest, looking into the distance, soft morning light",
    f"close-up of {PARK}, thoughtful eyes, soft window light, plain paper sliding door behind",
    f"{PARK} walking along a dirt road through autumn fields, soft golden light",
    f"{PARK_NOHAT} sitting on a wooden floor of a simple room with an ink stone and a brush, plain paper walls, soft daylight",
    "close-up of a calligraphy brush resting on a black ink stone beside blank white paper, soft light",
    # 연행 — 압록강·요동
    "a long line of travellers on horseback in white robes crossing a wide shallow river at dawn, mist, soft light",
    "a vast flat brown plain under a huge sky, a small caravan of horses far away on a dirt road, soft daylight",
    f"{PARK} on horseback with a small group of travellers on a wide dusty road, soft afternoon light",
    "a broad straight dirt road lined with tall poplar trees stretching to the horizon, soft daylight",
    # 청나라에서 본 것
    "two-wheeled wooden carts drawn by mules rolling along a wide packed-earth road, dust in the air, bright daylight",
    "close-up of a large wooden spoked cart wheel on a dirt road, soft daylight",
    "a massive grey brick city wall with a gate tower seen from far outside across a field, soft overcast daylight, no flags",
    "close-up of neatly stacked grey bricks, perfectly uniform, soft daylight",
    "a brick kiln in the countryside with workers stacking grey bricks, soft smoke, bright daylight",
    f"{QING} stacking bricks to build a house wall, bright daylight, seen from the side",
    "rows of grey clay roof tiles drying in the sun on a field, close-up, bright daylight",
    "a courtyard house with grey brick walls and grey tiled roofs, plain walls, soft daylight",
    "a wide stone bridge over a calm canal, wooden boats passing underneath, soft daylight",
    "close-up of baskets of vegetables, fruit and grain heaped on a cart, soft daylight, no labels",
    f"{PARK} watching mule carts pass on a wide road, amazed expression, bright daylight",
    "large wooden sailing junk boats in a river harbor, soft daylight, no flags",
    "close-up of blue and white porcelain jars on a plain wooden table, soft daylight, plain background",
    # 귀국 — 기록
    f"{PARK_NOHAT} writing with a brush by candlelight at a low wooden desk, warm light, plain paper walls",
    "a stack of blank handmade paper and a brush on a low wooden desk, warm lamp light",
    f"{PARK} speaking earnestly to two older Korean scholars in white robes and black gat hats sitting on a wooden porch, soft daylight",
    "a group of Korean scholars in white robes and black gat hats talking in a pine grove, soft daylight",
    # 생각 — 우물·수레·바다
    "an old stone well in a Korean village with a wooden bucket, clear water, soft daylight",
    "close-up of clear water being drawn up from a stone well in a wooden bucket, sparkling light",
    "a simple wooden ox cart on a newly widened dirt road through Korean hills, soft morning light",
    "a wide blue sea with a large wooden trading ship under sail, bright daylight, no flags",
    "a Korean fishing harbor with small wooden boats on a calm bay, soft daylight",
    "a Korean potter shaping a clay jar on a wheel, close-up of hands, soft daylight",
    "a Korean blacksmith hammering glowing iron, sparks, warm light, plain background",
    # 결말 — 유배·남은 질문
    f"{PARK} as an older man with grey beard in a plain white robe standing alone in a remote snowy northern mountain village, soft winter light",
    "a lonely thatched hut in a snowy mountain valley, thin smoke from the chimney, soft winter daylight",
    f"{PARK} as an older man looking out over a wide grey sea from a cliff, wind, soft overcast light",
    "a wide sea at sunrise with soft golden light over gentle waves, wide view",
    "an old road winding over green Korean hills toward a bright horizon, soft morning light",
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
            seed = int(os.environ.get("SEED_BASE", "75000")) + i * 100 + k * 7
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

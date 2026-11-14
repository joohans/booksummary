#!/usr/bin/env python3
"""「시녀 이야기」(마거릿 애트우드) Flux 무드 이미지 배치 생성

가까운 미래 길리어드(뉴잉글랜드 옛 대학 도시) — 붉은 망토·흰 날개 모자의 시녀 → 사령관 저택(계단·방·정원)
→ 둘씩 걷는 장보기 길·담장 → 회상(남편·딸·친구, 1980년대 평범한 삶) → 레드 센터의 아주머니
→ 사령관 서재의 밤(낱말 게임 판은 글자가 붙으니 빼고 램프·안락의자만) → 정원의 닉 → 검은 승합차 → 열린 결말.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 가게·간판·책·잡지·성경 금지, 상점은 멀리서도 안 쓴다.
교수형·폭력 묘사는 넣지 않는다(담장은 빈 벽돌담만). 휘장·완장은 「without insignia」.
BASE 는 사진풍 「35mm period film still」(모서리 서명 0 실측), 「drama」 금지.

    SEED_BASE=74000 .venv/bin/python scripts/gen_flux_handmaid.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Handmaids_Tale_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still, 1980s American dystopian film, muted colors, soft overcast daylight, "
        "bright enough to see clearly, not dark, light film grain, "
        "no logos, no text, no letters, no numbers, no signs, no writing anywhere, no watermark, no signature")

HANDMAID = "a woman in a long plain red cloak and a white winged bonnet that hides her face from the side"
HANDMAIDS = "two women in long plain red cloaks and white winged bonnets walking side by side"
OFFRED = "an American woman in her early thirties with brown hair"
LUKE = "an American man in his thirties with short dark hair in a plain sweater"
DAUGHTER = "a five-year-old American girl with light brown hair"
MOIRA = "an American woman in her early thirties with short dark hair and a bold grin in a plain denim jacket"
COMMANDER = "a grey-haired American man in his fifties in a plain dark suit"
WIFE = "an elegant older American woman with blonde hair in a plain long blue dress"
AUNT = "a stern older American woman in a plain long brown dress"
MARTHA = "a middle-aged American woman in a plain dull green dress and apron"
GUARD = "a man in a plain dark uniform without insignia"

SCENES = [
    # 길리어드 — 시녀
    f"{HANDMAID}, seen from behind, standing still in a quiet tree-lined street of old brick houses, overcast morning",
    f"close-up of {HANDMAID}, profile, soft window light, white wings framing her face, calm eyes",
    f"{HANDMAIDS} along an empty brick sidewalk under autumn trees, overcast but bright, seen from a distance",
    f"{HANDMAIDS} in the snow along a quiet colonial street, soft winter daylight",
    "a long empty red brick wall beside a quiet street with bare trees, overcast but bright, no posters",
    "an old New England university campus lawn with red brick buildings, empty and silent, overcast daylight",
    "a white church steeple above bare autumn trees, soft overcast daylight",
    "a red cloak hanging on a wooden peg next to a white winged bonnet, plain white wall, close-up",
    "a basket of red apples and bread held by a hand in a red sleeve, close-up, soft daylight",
    # 사령관 저택
    "a large white colonial house with black shutters and a green lawn, overcast but bright, wide view",
    "a curved wooden staircase in an old colonial house, soft window light, polished banister",
    f"{HANDMAID} sitting on a narrow bed in a sparse white room by a tall window, soft daylight",
    "a sparse bedroom with a plain white bed, a braided rug and a tall window with white curtains, soft light, no pictures",
    "a round window seat with a faded cushion in an old house, soft daylight through glass",
    "the floor of an empty wooden wardrobe, close-up, soft light",
    f"{MARTHA} kneading bread dough in a large old kitchen, warm daylight through windows",
    f"{WIFE} sitting in a lush garden of tulips with knitting needles, soft daylight",
    "a garden of red tulips in bloom beside a white house, soft overcast daylight, close-up",
    f"{WIFE} sitting stiffly on a sofa in a formal sitting room, soft lamp light, plain walls",
    f"{COMMANDER} standing at the top of a staircase looking down, soft window light",
    # 레드 센터
    f"rows of women in red cloaks sitting on cots in an old school gymnasium, {AUNT} standing in front, bright overcast light through high windows",
    f"close-up of {AUNT} holding a wooden pointer, stern face, plain wall",
    "an empty school gymnasium with rows of narrow army cots under high windows, soft daylight",
    # 회상 — 평범했던 삶
    f"{OFFRED} and {LUKE} laughing in a small sunny 1980s kitchen, warm morning light",
    f"{OFFRED} holding hands with {DAUGHTER} in a sunny autumn park, golden light",
    f"close-up of {DAUGHTER} smiling, soft golden light, shallow depth of field",
    f"{OFFRED} and {MOIRA} sitting on a college lawn in summer, laughing, bright sunlight",
    f"{OFFRED} jogging along a riverside path in summer morning, bright light",
    f"{OFFRED}, {LUKE} and {DAUGHTER} in an old car on a forest road near a border, tense faces, soft daylight",
    f"{OFFRED} running through a snowy forest holding {DAUGHTER}'s hand, soft winter light",
    # 사령관 서재의 밤
    "an old wood-panelled study with a leather armchair and a warm desk lamp, bookshelves out of focus, soft warm light",
    f"{COMMANDER} sitting in a leather armchair in a warm lamp-lit study, quiet smile",
    f"{OFFRED} in a red dress without a bonnet, sitting across from {COMMANDER} at a small table in a lamp-lit study",
    "a bottle of hand lotion and a glass of water on a small wooden table, close-up, warm lamp light",
    "a hallway of an old house at night with a thin line of warm light under a door, soft light",
    # 정원·닉·바깥
    f"{GUARD} washing a black car in a driveway, sleeves rolled up, soft overcast daylight",
    f"{OFFRED} in a red cloak standing in a garden at dusk looking toward the dark coach house, soft warm light",
    f"{HANDMAIDS} pausing by a riverbank with a willow tree, soft overcast daylight",
    f"{MOIRA} in a sequined stage costume sitting tiredly in a dim dressing room mirror light, warm light",
    "a crowd of women in red cloaks standing in a circle on a green lawn, seen from above, overcast but bright",
    # 결말 — 검은 승합차
    "a black van parked in front of a white colonial house at dusk, headlights on, soft blue light",
    f"{HANDMAID} walking down a staircase between two {GUARD.replace('a man', 'men')}, warm hall light",
    f"{HANDMAID} stepping into the back of a black van, seen from behind, open doors, soft evening light",
    "an empty country road at dawn stretching into soft misty light, wide view",
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
            seed = int(os.environ.get("SEED_BASE", "74000")) + i * 100 + k * 7
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

#!/usr/bin/env python3
"""「등대로」(버지니아 울프) Flux 무드 이미지 배치 생성

1부 창 — 스코틀랜드 섬의 바닷가 별장, 바다 건너 등대 → 제임스와 램지 부인(창가, 뜨개질하는 갈색 양말)
→ 램지 씨(테라스를 서성임) → 정원의 릴리(이젤·캔버스) → 손님들·해변 → 촛불 만찬
2부 시간이 흐른다 — 빈 별장, 먼지, 바람에 날리는 커튼, 등대 불빛, 전쟁 들판, 청소하는 노부인
3부 등대 — 10년 뒤, 돛단배로 등대를 향하는 램지 씨·제임스·캠 → 잔디밭의 릴리와 낮잠 자는 노시인 → 붓질 한 획.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 책·책장·신문·편지·시계 문자판은 쓰지 않는다.
BASE 는 사진풍 「35mm period film still」(삽화풍은 모서리 서명이 붙는다).

    SEED_BASE=80000 .venv/bin/python scripts/gen_flux_lighthouse.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/To_the_Lighthouse_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still, 1910s British period film, natural daylight, "
        "bright enough to see clearly, not dark, light film grain, "
        "no logos, no text, no letters, no signs, no writing anywhere, no watermark, no signature")

MRS = ("a beautiful English woman around fifty with dark hair streaked with grey pinned up loosely, "
       "a calm gentle face, wearing a long grey-green Edwardian dress and a light shawl")
MR = ("a tall gaunt English man around sixty with a stern bony face, thinning grey hair and a short grey beard, "
      "wearing an old tweed jacket")
OLD_MR = ("a tall gaunt English man around seventy with a stern bony face, white hair and a white beard, "
          "wearing an old tweed jacket")
JAMES = "a six-year-old English boy with tousled fair hair, wearing a white sailor shirt and shorts"
YOUNG_JAMES = "a sullen English boy of sixteen with tousled fair hair, wearing a plain white shirt and dark trousers"
CAM = "an English girl of seventeen with long dark hair tied back, wearing a plain pale blue dress"
LILY = ("a small slender English woman in her thirties with dark hair in a neat bun and small narrow eyes, "
        "wearing a plain grey dress and a painter's smock")
OLD_LILY = ("a small slender English woman in her forties with greying dark hair in a neat bun and small narrow eyes, "
            "wearing a plain grey dress and a painter's smock")
HOUSE = "a weathered white two-storey Victorian summer house with a large bay window and a garden lawn above a rocky shore"
LIGHTHOUSE = "a tall plain white stone lighthouse on a small rocky islet far across the sea"

SCENES = [
    # 1부 창
    f"{HOUSE} on a Scottish island on a bright late summer afternoon, sea beyond, wide shot",
    f"{LIGHTHOUSE}, seen across a calm grey-blue bay on a hazy afternoon, wide shot",
    f"{MRS} sitting in a chair by a large open bay window, {JAMES} sitting on the floor beside her, soft daylight",
    f"close-up of {JAMES} looking up hopefully, shallow depth of field, soft daylight",
    f"close-up of hands knitting a reddish-brown woollen stocking with wooden needles, shallow depth of field, soft daylight",
    f"close-up of {MRS} smiling tenderly while knitting, shallow depth of field, soft daylight",
    f"{MR} standing at the bay window looking down coldly, {MRS} and {JAMES} below him, soft daylight",
    f"close-up of {JAMES} glaring angrily, holding a pair of scissors, shallow depth of field, soft daylight",
    f"{MR} pacing alone along a stone terrace above the garden, hands behind his back, soft daylight",
    f"close-up of {MR} frowning deep in thought, shallow depth of field, soft daylight",
    f"{LILY} standing at a wooden easel on a garden lawn painting, a white house in the background, soft daylight",
    f"close-up of a canvas on an easel with a few abstract strokes of purple and green paint, a triangular shape, shallow depth of field",
    f"close-up of {LILY} frowning at her canvas, brush in hand, shallow depth of field, soft daylight",
    "a thin pale serious young English man in a dark suit standing stiffly on a garden lawn, soft daylight",
    "an elderly English man with a white beard and a yellowish stained moustache dozing in a wicker garden chair, soft daylight",
    "a young English couple in Edwardian summer clothes walking hand in hand on a sandy beach below cliffs, soft afternoon light",
    "close-up of a small sandy beach with rock pools and seaweed, shallow depth of field, soft afternoon light",
    f"{MRS} walking along a garden path at dusk carrying a basket, sea in the background, warm golden light",
    "a long dining table with white cloth, many lit candles, bowls of fruit and a large earthenware pot of beef stew, warm bright candlelight",
    f"{MRS} at the head of a long candlelit dinner table serving stew, guests seated around her, warm bright candlelight",
    "close-up of a bowl of fruit with grapes, pears and a shell on a candlelit table, shallow depth of field, warm light",
    f"close-up of {MRS} looking around the dinner table with a quiet contented smile, warm candlelight",
    f"{MRS} standing in a doorway looking back into a candlelit dining room, warm light",
    f"{MRS} and {MR} sitting together in a quiet lamplit sitting room, she knits and he watches her, warm light",
    # 2부 시간이 흐른다
    "an empty Victorian sitting room with dust sheets over furniture, pale daylight through the bay window, faded",
    "white curtains blowing in the wind through an open window of an empty room, pale daylight",
    "close-up of a grey shawl hanging on a wall hook in an empty room, dust in the air, pale daylight",
    "close-up of dust and cobwebs on a windowsill with a dried flower, shallow depth of field, pale daylight",
    "a weathered empty summer house with an overgrown garden of tall grass and thistles above the sea, overcast day",
    "a misty empty muddy battlefield with broken trees under a pale sky, soft hazy light",
    "stormy grey waves crashing on a rocky shore under a heavy sky, daytime",
    "an elderly stooped Scottish cleaning woman in a plain dark dress and apron opening shutters in an empty room, pale daylight",
    "close-up of old hands sweeping a dusty wooden floor with a broom, shallow depth of field, soft daylight",
    # 3부 등대
    f"{OLD_MR} standing on a garden lawn on an early September morning, the sea and a distant lighthouse beyond, soft daylight",
    f"{OLD_LILY} setting up a wooden easel on a garden lawn, early morning light",
    f"a small wooden sailing boat with a plain white sail on a calm blue sea, {OLD_MR}, {YOUNG_JAMES} and {CAM} aboard, wide shot",
    f"close-up of {YOUNG_JAMES} at the tiller of a small sailing boat, sullen face, shallow depth of field, bright daylight",
    f"close-up of {CAM} trailing her hand in the sea from a boat, dreamy expression, shallow depth of field, bright daylight",
    f"close-up of {OLD_MR} sitting in a small boat looking towards the sea, weathered face, shallow depth of field, bright daylight",
    f"{LIGHTHOUSE.replace('far across the sea', 'seen up close')}, white waves at its base, bright blue sky",
    f"close-up of {OLD_LILY} painting a canvas on an easel on a lawn, absorbed, shallow depth of field, soft daylight",
    f"{OLD_LILY} looking across the bay at a tiny distant sailing boat, standing by her easel, soft daylight",
    f"close-up of {OLD_MR} springing up onto the rocks of a small islet from a boat, {YOUNG_JAMES} watching, bright daylight",
    "close-up of a single bold vertical brushstroke of dark paint on a canvas, shallow depth of field, soft daylight",
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
            seed = int(os.environ.get("SEED_BASE", "80000")) + i * 100 + k * 7
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

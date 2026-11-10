#!/usr/bin/env python3
"""「끝없는 이야기」(미하엘 엔데) Flux 무드 이미지 배치 생성

비 오는 날 놀림을 피해 들어간 낡은 책방 → 구릿빛 책(두 뱀의 문양)을 훔쳐 학교 다락방에서 읽는 바스티안
→ 허무에 잠식되는 환상 세계, 상아탑의 병든 어린 여제 → 초록 피부의 아트레유와 백마의 여정, 슬픔의 늪
→ 거대한 늙은 거북, 행운의 용과 비행, 남쪽 신탁의 스핑크스 문, 늑대인간 → 바스티안 차례
→ 2부: 책 속에 들어간 바스티안, 메달의 힘, 색채의 사막·빛나는 밤 숲, 기억을 잃어 가는 소년 → 생명의 물.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 책은 「plain, no lettering」 클로즈업만, 책장 금지.
판타지 장면은 1980년대 실사 판타지 영화 스틸(사진풍 = 모서리 서명 방지), 밝게.

    SEED_BASE=69000 .venv/bin/python scripts/gen_flux_neverending.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Neverending_Story_flux"))   # 검수 후 옮긴다

BASE = ("cinematic film still from a 1980s live-action fantasy film, practical effects, soft natural daylight, "
        "bright enough to see clearly, not dark, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no numbers, no signs, no labels, no writing anywhere, no watermark, no signature")

BAS = "a chubby ten-year-old German boy with short brown hair in a plain grey wool sweater"
ABAS = "a slim handsome boy of twelve with brown hair in a plain dark blue velvet tunic and silver cloak"
ATR = "a slender ten-year-old boy with olive-green skin and long black hair, in a plain reddish-brown buffalo-hide cloak, a bow on his back"
EMP = "a pale young girl of ten with long snow-white hair and golden eyes, in a plain white silk gown"
DRAGON = "a long white furry luck dragon with pearly pink-white scales, a gentle dog-like head and big ruby eyes"
BOOK = "an old thick book bound in copper-colored silk with an embossed emblem of two snakes biting each other's tails in an oval, completely plain with no lettering"

SCENES = [
    # 현실 — 비 오는 날, 책방
    f"{BAS} running alone along a wet cobblestone street in light rain, old German town, soft grey daylight",
    f"{BAS} standing inside the door of a small dim antique shop, rain on the glass behind him, warm lamp light, shallow depth of field",
    "an old wooden shop counter with a brass lamp and a teacup, warm light, everything in the background blurred",
    f"close-up of {BOOK}, lying on a wooden counter in warm lamp light",
    f"{BAS} hugging a thick copper-colored book to his chest and running out into the rain, motion blur",
    # 다락방
    f"{BAS} climbing a narrow wooden ladder into a dusty school attic, beams of daylight",
    f"{BAS} sitting cross-legged on old gym mats in a dusty attic, reading a thick copper-colored book, light from a small round window",
    "a dusty school attic with old wooden beams, stacked gym mats and a stuffed old owl, soft light through a small round window",
    f"close-up of {BAS} reading with wide eyes, his face lit by soft window light",
    "rain running down a small round attic window, grey daylight, cosy",
    # 환상 세계와 허무
    "a vast enchanted green forest of giant ancient trees with tiny glowing creatures, misty bright morning",
    "a strange fantasy landscape where part of the forest dissolves into blank white emptiness, as if erased, bright overcast light",
    "a council of strange fantasy creatures gathered in a forest clearing, a rock giant, a tiny man on a racing snail, a will-o'-the-wisp, daylight",
    "a gleaming white ivory tower rising like a giant spiral shell above a labyrinth of flower gardens, bright sunlight",
    f"{EMP} lying weak on soft white cushions in a white pavilion, pale and ill, soft light",
    f"close-up of {EMP}, golden eyes, calm sad expression, soft white light",
    # 아트레유의 여정
    f"{ATR} standing on a grassy plain beside a white horse, wide open sky, bright day",
    f"{ATR} riding a white horse across a wide grassland, morning sun",
    f"close-up of {ATR}, determined face, wind in his long black hair, daylight",
    "a vast grey misty swamp with dead trees and still water, melancholy but lit by soft daylight",
    f"{ATR} pulling at the reins of a white horse sinking into a grey swamp, sad, soft daylight",
    "a gigantic ancient turtle like a mossy mountain resting in a swamp, small boy standing before it, soft daylight",
    f"{DRAGON} lying wounded in a giant spider web in a rocky ravine, daylight",
    f"{ATR} riding on the back of {DRAGON}, flying high above clouds, bright sunlight",
    f"{DRAGON} flying over a sea of white clouds at sunrise, golden light",
    "two gigantic stone sphinx statues facing each other across a desert gateway, bright sun, long shadows",
    f"{ATR} walking alone through a huge gateway between two giant stone sphinxes in a desert, bright day",
    "a huge shaggy black wolf with glowing green eyes lying in the shadows of ruined stone walls, dim but visible, daylight from above",
    f"{ATR} standing at the edge of a world dissolving into blank white emptiness, wind blowing, bright overcast",
    # 바스티안의 차례
    f"{BAS} looking up from his book, startled, in a dusty attic, soft window light",
    f"close-up of a boy's hands holding an open book with plain blank golden-glowing pages, light rising from the pages",
    f"{EMP} looking straight into the camera with hope, soft white light",
    "a single grain of glowing golden sand in the open palm of a child's hand, soft bright white light, close-up",
    # 2부 — 책 속의 바스티안
    "a golden amulet with two intertwined snakes, one light and one dark, biting each other's tails, resting on white silk, close-up",
    f"{ABAS} standing in a vast desert of many-colored sand dunes, red, blue and violet, bright sun",
    "a night forest of giant glowing luminous plants in soft blue and green light, bright and magical",
    f"{ABAS} walking through a forest of giant luminous plants, soft glowing light",
    f"{ABAS} riding a white mule through green hills with a group of knights, sunny day",
    f"{ABAS} and {ATR} sitting by a campfire under a dusk sky, warm light, friendly",
    f"{ABAS} standing on a silver bridge over a lake, proud and alone, bright day",
    f"{ABAS} sitting alone on a carved stone throne in a pale empty hall, cold light, lonely",
    f"{ABAS} walking alone across a vast snowy plain, lost, soft white daylight",
    "a clear spring of sparkling water flowing from the ground in a meadow, sunlit droplets, bright",
    f"{BAS} running across an open sunny meadow toward a sparkling fountain, joyful",
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
            seed = int(os.environ.get("SEED_BASE", "69000")) + i * 100 + k * 7
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

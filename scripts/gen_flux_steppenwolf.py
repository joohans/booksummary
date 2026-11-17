#!/usr/bin/env python3
"""「황야의 이리」(헤르만 헤세) Flux 무드 이미지 배치 생성

1920년대 독일 도시 → 시민의 하숙집 계단참(밀랍·화분) → 다락방의 고독한 하리 할러(책·술·담배) → 황야의 늑대
→ 밤길 방황 대신 해 질 녘 강변 → 술집에서 만난 헤르미네(단발) → 춤·재즈·파블로의 색소폰·마리아
→ 가면무도회 → 마술 극장의 거울 복도·수많은 자아 → 체스 말 → 모차르트의 웃음 → 아침 햇살.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 거리 간판·포스터·신문·악보·책등은 글자가 붙으므로
얕은 심도 실내·클로즈업·자연 위주. 밤 장면은 b<60 이 되므로 「warm lamplight, bright enough」 명시.
BASE 는 사진풍 「35mm period film still」(모서리 서명 0 실측).

    SEED_BASE=76000 .venv/bin/python scripts/gen_flux_steppenwolf.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Steppenwolf_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still, 1920s German period film, warm natural light, "
        "bright enough to see clearly, not dark, light film grain, "
        "no logos, no text, no letters, no signs, no posters, no writing anywhere, no watermark, no signature")

HARRY = ("a gaunt German man about fifty with short greying hair, a tired thoughtful face and a thin moustache, "
         "wearing a rumpled dark wool suit")
HERMINE = "a young German woman in her twenties with a short dark 1920s bob haircut, pale face and dark eyes, in a simple dark dress"
PABLO = "a handsome dark-haired young jazz musician with a warm smile in a plain dark suit, holding a brass saxophone"
MARIA = "a beautiful young German woman with wavy blonde 1920s hair in a plain cream dress"

SCENES = [
    # 하숙집 — 시민의 질서
    "a clean bourgeois stairwell landing in an old German townhouse with polished wooden banisters, potted plants and waxed floor, soft daylight",
    "close-up of a potted araucaria plant on a polished wooden stair landing, soft daylight, shallow depth of field",
    "an old German townhouse with steep roofs on a quiet cobblestone street in the 1920s, soft afternoon light",
    f"{HARRY} sitting alone on the stairs of a clean townhouse stairwell, looking at the potted plants, soft daylight",
    # 다락방 — 고독
    "a cluttered attic room with stacks of plain unmarked books, wine bottles, cigar ash and scattered papers, soft window light",
    f"{HARRY} reading alone by a small attic window, cigar smoke in the air, soft afternoon light",
    "close-up of a half-empty glass of red wine and a smoking cigar on a cluttered wooden desk, warm light, shallow depth of field",
    f"close-up of {HARRY} with a melancholy distant gaze, soft window light, shallow depth of field",
    "close-up of an old straight razor lying on a white washbasin beside a small mirror, cold soft daylight, shallow depth of field",
    f"{HARRY} looking at his own tired face in a small bathroom mirror, soft daylight",
    # 황야의 늑대
    "a lone grey wolf standing on a vast empty steppe of dry grass under a pale sky, soft daylight",
    "close-up of a grey wolf's amber eyes, soft natural light, shallow depth of field",
    "a lone grey wolf walking at the edge of a dark pine forest on snowy ground, soft overcast daylight",
    f"{HARRY} standing alone on a windswept grassy hill at dusk, coat collar raised, golden light",
    "a grey wolf and its reflection in still water at the edge of a wild grassland, soft daylight",
    # 도시 방황
    f"{HARRY} walking alone along a stone river embankment at golden hour, old bridge in the background",
    "an old stone bridge over a calm river in a German city at sunset, warm golden light",
    f"{HARRY} walking down an empty cobblestone lane with old wooden doors, late afternoon light",
    "a quiet old church courtyard with bare trees and a stone bench, soft afternoon light",
    # 헤르미네
    f"a small warm tavern interior with wooden tables and warm lamplight, {HARRY} sitting alone at a table, bright enough to see clearly",
    f"{HERMINE} sitting at a wooden tavern table smiling knowingly, warm lamplight, shallow depth of field",
    f"{HERMINE} and {HARRY} talking across a small wooden table with two glasses of wine, warm lamplight",
    f"close-up of {HERMINE} with a mysterious gentle smile, warm light, shallow depth of field",
    f"{HERMINE} laughing and teaching {HARRY} to dance in a small bright room with a wooden floor, gramophone on a table, soft daylight",
    "close-up of a brass gramophone horn on a wooden table, soft warm light, shallow depth of field",
    # 재즈·파블로·마리아
    f"{PABLO} playing a saxophone on a small stage in a 1920s dance hall, warm golden lamplight, bright enough to see clearly",
    "close-up of a brass saxophone gleaming in warm light, shallow depth of field",
    f"couples in 1920s evening clothes dancing in a bright ballroom with warm chandeliers, {HARRY} watching at the edge",
    f"{MARIA} dancing gracefully with {HARRY} in a warm bright ballroom, soft golden light",
    f"close-up of {MARIA} smiling warmly, soft golden light, shallow depth of field",
    f"{PABLO} offering a small glass with a sly smile in a warm lamplit room, shallow depth of field",
    # 가면무도회
    "a crowded 1920s masked ball with people in elegant costumes and plain eye masks, streamers, warm bright chandeliers",
    "close-up of a plain black eye mask lying on a velvet chair, warm light, shallow depth of field",
    f"{HERMINE} in a plain black eye mask and a dark tailcoat at a masked ball, warm bright light",
    # 마술 극장
    "a long corridor of tall doors with brass handles lit by warm lamps, surreal dreamlike atmosphere, bright enough to see clearly",
    "a hall of many mirrors reflecting a man's figure into countless copies, warm soft light, surreal",
    f"{HARRY} standing between two tall mirrors with endless reflections of himself, warm soft light, surreal",
    "a wooden chessboard with many carved wooden chess pieces shaped like small human figures, warm light, shallow depth of field",
    f"{HARRY} as a young man and an old man facing each other in a surreal mirrored room, soft warm light",
    "a grey wolf standing calmly in an elegant empty ballroom with warm chandeliers, surreal",
    # 모차르트·불멸자들
    "Wolfgang Amadeus Mozart in an 18th-century white powdered wig and red coat laughing joyfully, warm soft light, period film",
    "an elegant 18th-century harpsichord in a bright rococo music room, soft daylight",
    f"{HARRY} laughing for the first time with tears in his eyes, warm soft light, shallow depth of field",
    # 끝 — 다시 살아갈 아침
    "morning sunlight pouring through an attic window onto an empty wooden chair, soft and hopeful",
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
            seed = int(os.environ.get("SEED_BASE", "76000")) + i * 100 + k * 7
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

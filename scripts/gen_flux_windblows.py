#!/usr/bin/env python3
"""「바람이 분다, 가라」(한강) Flux 무드 이미지 배치 생성

눈 내리는 미시령 고개(표지판·가드레일 글자 없이 눈 덮인 산길) → 화가 인주의 화실(먹그림·캔버스, 서예 글씨 없이)
→ 평론가 석원(민무늬 벽 갤러리) → 친구 정희의 탐문(겨울 도시 골목은 간판 지옥이라 쓰지 않는다 — 실내·창가·바닷가)
→ 인주의 아들 민서 → 달·별·우주(삼촌의 천체물리학, 「달의 뒷면」) → 불타는 화실(밝게) → 병실의 숨(모니터 화면 없이)
→ 봄 풍경.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 책·신문·표지판·모니터·간판은 쓰지 않는다.
⚠️ 먹그림은 한자 붓글씨가 붙기 쉬우므로 「abstract ink wash, no calligraphy」. 인물마다 「Korean … black hair」 명시.
⚠️ BASE 에 「contemporary Korean drama film」 금지(방송사 로고풍 글자).

    SEED_BASE=79000 .venv/bin/python scripts/gen_flux_windblows.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Wind_Blows_Go_flux"))   # 검수 후 옮긴다

BASE = ("35mm film still, quiet arthouse film, natural light, "
        "bright enough to see clearly, not dark, light film grain, "
        "no logos, no text, no letters, no signs, no writing anywhere, no watermark, no signature")

JUNGHEE = ("a slender Korean woman in her late thirties with shoulder-length straight black hair and a pale serious face, "
           "wearing a dark grey wool coat")
INJU = ("a Korean woman painter in her late thirties with short black hair and bright intense eyes, "
        "wearing a paint-stained loose white shirt")
SEOKWON = ("a tall Korean man in his fifties with neatly combed grey-streaked black hair and rimless glasses, "
           "wearing a dark charcoal suit, cold composed face")
MINSEO = "a quiet Korean boy of about ten with black hair, wearing a navy hooded jacket"
INK = "large abstract black ink wash paintings on white paper, sweeping brush strokes like wind and mountains, no calligraphy, no characters"

SCENES = [
    # 미시령 — 눈
    "a winding mountain road through snowy Korean mountains in heavy snowfall, no signs, no guardrails, soft white daylight",
    "a steep snow-covered mountain pass with pine trees bending in the wind, falling snow, soft white daylight, wide shot",
    "close-up of snowflakes falling on dark pine branches, shallow depth of field, soft light",
    "tire tracks in fresh snow curving off the edge of a mountain road into white emptiness, soft daylight",
    "a vast white snowy mountain ridge under a pale grey sky, wide shot, soft light",
    "a single car's headlights glowing faintly through heavy falling snow on a mountain road at dusk, bright enough to see",
    # 인주 — 화실
    f"{INJU} painting on a large canvas in a bright studio with tall windows, soft daylight",
    f"a bright empty painter's studio with {INK} pinned on white walls, soft daylight",
    "close-up of a wet brush dragging black ink across white paper, shallow depth of field, soft daylight",
    "close-up of paint-stained hands holding a brush, shallow depth of field, soft daylight",
    f"close-up of {INJU} smiling faintly, looking out of a studio window, soft daylight",
    "jars of brushes and ink dishes on a wooden table in a sunlit studio, shallow depth of field",
    "a large painting of a pale moon above dark mountains leaning against a white wall, soft daylight",
    # 정희와 인주 — 우정
    f"{JUNGHEE} and {INJU} laughing together, sitting on a wooden floor in a bright studio, warm daylight",
    "two Korean schoolgirls with black hair in white blouses walking along a seaside path, memory, soft hazy light",
    f"{JUNGHEE} and {INJU} standing side by side on a grey winter beach, wind in their hair, soft daylight",
    # 석원 — 평론가
    f"{SEOKWON} standing in a white empty gallery with large framed abstract paintings, soft daylight",
    f"close-up of {SEOKWON} staring coldly at a painting, shallow depth of field, soft light",
    f"{SEOKWON} and {JUNGHEE} facing each other tensely in a bare white gallery room, soft daylight",
    "visitors' silhouettes in front of large abstract ink paintings in a bright white gallery, soft daylight",
    # 정희의 탐문
    f"{JUNGHEE} sitting alone at a wooden table by a window in a quiet apartment, holding a cup of tea, grey winter daylight",
    f"close-up of {JUNGHEE}'s face, thoughtful and grieving, shallow depth of field, soft window light",
    f"{JUNGHEE} walking alone along a snowy riverside path in winter, wide shot, soft daylight",
    f"{JUNGHEE} looking through a pile of loose sketches spread on a floor, soft daylight",
    "close-up of a pencil sketch of a woman's face on rough paper, shallow depth of field, soft daylight",
    f"{JUNGHEE} talking with an elderly Korean woman with grey hair in a modest room, soft daylight",
    f"{JUNGHEE} standing at the edge of a snowy mountain road looking down, wind, soft daylight",
    # 민서
    f"{MINSEO} sitting by a window looking out at falling snow, soft daylight",
    f"{JUNGHEE} holding the hand of {MINSEO} walking along a winter path, wide shot, soft daylight",
    # 달과 별 — 삼촌의 우주
    "a huge pale full moon rising over dark snowy mountains, clear deep blue sky, bright moonlight",
    "the Milky Way over a quiet snowy mountain valley, long exposure, bright starlight",
    "close-up of the cratered grey surface of the moon, astronomical photograph",
    f"{INK} showing swirling galaxies and stars, soft daylight",
    "an old brass telescope by an open window at twilight, soft blue light",
    # 위협 — 방해
    f"{JUNGHEE} looking back over her shoulder in a dim corridor, uneasy, soft light, bright enough to see",
    "a dark figure's shadow falling across a white studio wall, tense, soft light",
    "close-up of a hand gripping a door handle, tense, shallow depth of field",
    # 불 — 화실
    "an abandoned painter's studio filled with orange flames and smoke, bright firelight",
    "close-up of burning sheets of paper with ink paintings curling in flames, bright orange light",
    f"{JUNGHEE} crawling across a smoky wooden floor toward bright light, dramatic, bright firelight",
    # 숨 — 병실과 봄
    "a quiet white hospital room with morning light through thin curtains, no screens, soft light",
    f"close-up of {JUNGHEE} lying in a hospital bed with eyes closed, soft morning light, shallow depth of field",
    "cherry blossoms and fresh green leaves outside a window in spring sunlight, bright",
    "a wide sunny spring mountain valley with new green leaves and a light breeze, bright daylight",
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
            seed = int(os.environ.get("SEED_BASE", "79000")) + i * 100 + k * 7
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

#!/usr/bin/env python3
"""「소피의 세계」(요슈타인 가아더) Flux 무드 이미지 배치 생성

노르웨이 작은 마을, 우편함의 하얀 봉투 → 정원 산울타리 속 비밀 동굴에서 편지를 읽는 소피
→ 편지를 물어 오는 큰 개 → 수수께끼의 철학자 알베르토 → 철학사 여행(그리스 신전·아테네 광장·동굴의 그림자·
중세 수도원·르네상스 화실·데카르트의 촛불 서재·계몽주의 살롱) → 호숫가 오두막과 빨간 보트, 거울
→ 다른 세계의 소녀 힐데와 아버지 → 6월 정원 생일 파티 → 숲과 별.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 봉투·카드는 「blank, no writing」, 표지판·책장 금지.
사진풍(1990년대 영화 스틸) + 역사 장면은 「period film still」.

    SEED_BASE=70000 .venv/bin/python scripts/gen_flux_sophie.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Sophies_World_flux"))   # 검수 후 옮긴다

BASE = ("cinematic film still, 1990s Scandinavian family film, soft natural daylight, "
        "bright enough to see clearly, not dark, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no numbers, no signs, no labels, no writing anywhere, no watermark, no signature")

SOPHIE = "a curious fourteen-year-old Norwegian girl with long straight dark brown hair in a plain blue knitted sweater"
ALB = "a thin middle-aged Norwegian man with a short grey beard and a dark beret, in a plain dark brown coat"
HILDE = "a fifteen-year-old Norwegian girl with wavy blonde hair in a plain white summer dress"
DOG = "a big friendly golden labrador dog"
ENV = "a plain blank white envelope with no writing on it"

SCENES = [
    # 마을과 우편함
    "a quiet Norwegian village street with small painted wooden houses and birch trees, early summer afternoon, bright",
    f"{SOPHIE} walking home along a quiet village road with a school backpack, birch trees, bright afternoon",
    f"{SOPHIE} opening a plain green metal mailbox on a wooden post by a garden gate, bright afternoon",
    f"close-up of a girl's hands holding {ENV}, soft daylight",
    f"{SOPHIE} standing still in a garden, staring thoughtfully at a small white card in her hand, bright daylight",
    f"close-up of {SOPHIE} looking up at the sky with a puzzled expression, soft daylight",
    # 산울타리 동굴
    "a hidden hollow inside a dense green garden hedge, sunlight filtering through leaves, cosy secret den",
    f"{SOPHIE} sitting cross-legged inside a hollow in a dense green hedge, reading a stack of plain white papers, dappled sunlight",
    f"{SOPHIE} lying on her bed by an open window at dusk light, thinking, plain bedroom walls, soft warm light",
    "a small white bedroom in a Norwegian house with a window open to a garden, plain walls, bright morning",
    # 개와 철학자
    f"{DOG} trotting through a garden with a plain brown envelope in its mouth, bright day",
    f"{DOG} sitting by a garden gate looking up, bright day",
    f"{ALB} standing at the edge of a birch forest, watching calmly, soft daylight",
    f"{ALB} and {SOPHIE} walking together along a forest path, talking, dappled sunlight",
    f"{ALB} sitting in an old wooden chair in a small attic room full of old curious objects, soft window light",
    f"close-up of {ALB}, thoughtful face, soft window light",
    # 철학사 여행 — 고대
    "the ruins of an ancient Greek temple with white marble columns on a hill above a blue sea, bright sun",
    f"{SOPHIE} and {ALB} standing among ancient Greek marble ruins at sunrise, golden light",
    "period film still of an ancient Athenian marketplace with people in plain white tunics, an old bearded man talking with young men, bright sun",
    "period film still of an old bald bearded philosopher in a plain white robe talking with young men under a stone portico, bright sun",
    "shadows of people projected on a rough cave wall by firelight, seen from behind silhouettes of chained figures, warm orange light, visible detail",
    "a bright opening of a cave seen from inside, sunlight and green valley outside, contrast of shadow and light",
    "close-up of a single drop of water on a green leaf reflecting the world, bright morning",
    # 중세·근대
    "period film still of a quiet medieval stone monastery cloister with a garden, soft daylight",
    "period film still of a monk in a plain brown habit walking in a sunny medieval cloister garden",
    "period film still of a Renaissance painter's studio with an easel and a plain blank canvas, bright window light",
    "period film still of a 17th-century man with long dark hair writing with a quill by a candle in a plain room, warm light, papers without visible writing",
    "period film still of an 18th-century salon with people in powdered wigs talking, bright chandelier light",
    "a brass telescope by an open window at dawn, sky turning blue, soft light",
    # 수상한 일들
    f"{SOPHIE} discovering a small plain red silk scarf hanging on a branch in the forest, puzzled, soft daylight",
    f"{SOPHIE} holding half a peeled banana and staring at it in surprise, kitchen, bright day",
    "a small red wooden cabin on the shore of a forest lake, a red rowing boat tied to a small dock, bright day",
    f"{SOPHIE} rowing a small red rowing boat across a still forest lake, bright day",
    f"{SOPHIE} looking into an old oval mirror in a wooden cabin, her reflection seems to wink, soft light",
    # 힐데의 세계
    f"{HILDE} sitting on a wooden dock by the sea at midsummer, reading a thick plain folder of papers, bright evening sun",
    f"{HILDE} lying on her bed reading a thick binder of papers, laughing, bright summer light",
    "a Norwegian officer in a plain beige uniform without insignia, sitting alone at a desk writing, warm desert light through a window",
    "a white wooden house by the sea in southern Norway with a garden and a flagless pole, bright midsummer",
    # 생일 파티와 결말 쪽
    "a midsummer garden party with a long table under birch trees, white tablecloth, flowers, lanterns, bright evening light",
    f"{SOPHIE} in a plain white dress at a garden party table under birch trees, bright evening light",
    f"{SOPHIE} and {ALB} slipping away through a garden into a sunlit forest, from behind",
    "a sunlit Norwegian forest of birch and pine with soft mist, bright morning, peaceful",
    "a starry twilight sky over a calm fjord, deep blue but bright, visible mountains",
    f"{SOPHIE} standing on a hill above a fjord, wind in her hair, looking at the wide sky, bright day",
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
            seed = int(os.environ.get("SEED_BASE", "70000")) + i * 100 + k * 7
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

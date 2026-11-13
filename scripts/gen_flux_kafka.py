#!/usr/bin/env python3
"""「해변의 카프카」(무라카미 하루키) Flux 무드 이미지 배치 생성

도쿄를 떠나는 열다섯 살 카프카(야간 버스·바다) → 다카마쓰 바닷가와 작은 사립 도서관(열람실·창가·정원)
→ 오시마·사에키 씨·여름 바닷가 소녀의 그림 → 고양이와 말하는 노인 나카타 → 하늘에서 떨어지는 물고기
→ 트럭 운전사 호시노와 길 → 신사 숲·산속 오두막·깊은 숲속 마을 → 입구의 돌·바다.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 일본 거리·가게·간판·책장 금지(한자 간판·책등 제목),
도서관은 창가·빈 책상·정원으로만. 인물은 전부 「Japanese … black hair」 명시.
⚠️ BASE 에 「drama」 쓰지 말 것(방송사 로고풍 글자 — 대온실 실측).

    SEED_BASE=72000 .venv/bin/python scripts/gen_flux_kafka.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Kafka_on_the_Shore_flux"))   # 검수 후 옮긴다

BASE = ("35mm film still, early 2000s Japanese art-house film, soft natural daylight, shallow depth of field, "
        "bright enough to see clearly, not dark, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no numbers, no signs, no labels, no writing anywhere, no watermark, no signature")

KAFKA = "a quiet fifteen-year-old Japanese boy with short black hair in a plain grey hoodie"
OSHIMA = "a slender androgynous Japanese young man in his twenties with neat black hair in a plain white shirt"
SAEKI = "an elegant Japanese woman in her fifties with shoulder-length black hair in a plain navy dress"
NAKATA = "a gentle elderly Japanese man with a shaved grey head in a plain beige jacket and a cloth hat"
HOSHINO = "a sturdy Japanese truck driver in his twenties with a ponytail in a plain green work shirt and cap without logo"
CAT = "a small calico cat"

SCENES = [
    # 가출
    f"{KAFKA} with a backpack standing alone at a quiet suburban house gate at dawn, soft blue light",
    f"{KAFKA} asleep against the window of a night bus, soft passing lights, warm interior light, visible detail",
    f"{KAFKA} looking out at a calm blue sea from a seawall, bright morning",
    "a wide calm Seto Inland Sea with small green islands, bright summer morning",
    f"close-up of {KAFKA}'s face, determined eyes, soft daylight",
    f"{KAFKA} doing push-ups alone in a plain small room, morning light",
    # 도서관
    "a small old Japanese private library building of dark wood in a quiet garden with pine trees, bright day, no signs",
    "a quiet reading room with a large wooden table and a tall window open to a green garden, soft afternoon light, no bookshelves",
    f"{KAFKA} reading at a wooden table by a tall window in a quiet old room, soft afternoon light",
    f"{OSHIMA} standing by a window in an old wooden room, smiling softly, afternoon light",
    f"{OSHIMA} driving a small green sports car along a coastal mountain road, bright day",
    f"{SAEKI} sitting at a writing desk by a window, writing with a fountain pen on plain blank paper, soft light",
    f"close-up of {SAEKI}, wistful distant gaze, soft window light",
    "an old oil painting of a boy sitting on a summer beach, hanging on a plain wall, soft light",
    f"a ghostly fifteen-year-old Japanese girl with black hair in a plain light blue dress sitting at a desk in moonlight, pale blue light, visible detail",
    "a small guest room with a single bed and an open window to a garden at night, soft lamp light, plain walls",
    # 나카타
    f"{NAKATA} crouching in an empty grassy lot, talking to a black cat, bright afternoon",
    f"{NAKATA} sitting on a low wall with {CAT} beside him, gentle smile, bright day",
    "a black and white cat and a siamese cat sitting in tall summer grass, bright day",
    f"{NAKATA} walking slowly with an umbrella under a clear sky, bright day",
    "period film still, 1944, Japanese schoolchildren in plain clothes lying asleep on a grassy hillside in a forest, bright day",
    "period film still, a Japanese female teacher in plain 1940s clothes standing alone on a forest path, worried, soft daylight",
    "dozens of small silver fish falling from a blue sky onto a quiet residential lane, surreal, bright day",
    "a heavy rain of dark leeches falling on a quiet road, surreal, soft light, visible detail",
    "a mysterious tall man in a black top hat and a plain black coat standing in a plain room, eerie, soft light",
    # 신사 숲·피
    f"{KAFKA} waking up on the ground in a dense shrine forest at dawn, confused, soft light",
    f"close-up of {KAFKA} staring at his hands, soft dawn light in a forest",
    "a quiet Shinto shrine path in a dense green forest with an old stone lantern, misty morning, bright",
    "rows of red wooden shrine gates along a forest path, bright day, no writing",
    # 호시노와 여정
    f"{HOSHINO} and {NAKATA} sitting in a truck cab on a highway, sunlight, plain dashboard",
    "a large plain blue truck on an empty coastal highway, bright day, no signs",
    f"{HOSHINO} and {NAKATA} crossing a long bridge over the sea on foot, bright day",
    f"{HOSHINO} lifting a round flat grey stone in a plain room, straining, soft light",
    "close-up of a round flat grey stone on a wooden floor, mysterious, soft light",
    f"{NAKATA} asleep peacefully on a futon in a plain room, soft afternoon light",
    # 산속 오두막과 숲
    "a small wooden cabin in a deep mountain forest, bright morning, mist",
    f"{KAFKA} sitting on the wooden porch of a mountain cabin, listening to the forest, bright morning",
    f"{KAFKA} walking deeper into a dense green forest along a narrow trail, sunlight beams",
    "two Japanese soldiers in plain WWII uniforms without insignia standing in a sunlit forest, calm and timeless",
    "a small quiet village in a forest clearing with old wooden houses, misty, soft light",
    # 바다·결말 쪽
    f"{KAFKA} standing on a summer beach facing the sea, wind, bright day",
    "waves gently washing onto a sandy beach, bright morning, close to the water",
    f"{KAFKA} on a train looking out at green rice fields, bright day",
    "the sea at sunset seen from a quiet beach, golden light, calm",
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
            seed = int(os.environ.get("SEED_BASE", "72000")) + i * 100 + k * 7
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

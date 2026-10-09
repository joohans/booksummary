#!/usr/bin/env python3
"""「소유냐 존재냐」(에리히 프롬) Flux 무드 이미지 배치 생성 (스톡 보충용)

비소설이라 장면 대신 「소유 vs 존재」의 대비를 사물·인물·자연으로 그린다.
교훈(구보·태평천하): 상점·도시·실내 벽은 간판·액자를 부른다 → 처음부터 얕은 심도 클로즈업·자연·하늘 위주.
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 포트는 /generate 1회로 확인
OUT = Path("assets/images/To_Have_or_to_Be_flux")   # 스톡 AI 검증이 Flux 까지 깎지 않도록 따로 받아 검수 후 옮긴다

BASE = ("contemplative painterly film still, 1970s, soft natural light, muted warm palette with calm blue-green accents, "
        "film grain, very shallow depth of field, background completely blurred out of focus, "
        "no text, no signs, no logos, no labels, no brand names, no letters, no numbers, no writing anywhere")

SCENES = [
    # 위대한 약속
    "a vast field of identical factory smokestacks at dusk seen from far away, orange haze, no people",
    "close-up of a conveyor belt carrying endless identical shiny objects, blurred factory background",
    "a lonely man sitting on a sofa surrounded by stacks of unopened cardboard boxes, empty expression, dim light",
    # 테니슨 vs 바쇼
    "a hand pulling a small wildflower out of a crack in an old stone wall, roots and soil dangling, close-up",
    "a wilted uprooted flower lying on a wooden table beside a magnifying glass, dark background",
    "an old Japanese poet in a simple robe crouching quietly to look at a tiny white flower blooming by a hedge, not touching it, morning light",
    "close-up of a tiny white shepherd's purse flower blooming by a rustic hedge, dew drops, soft morning light",
    # 소유양식 일상
    "close-up of a hand tightly gripping a heavy ring of many keys, tense knuckles, dark background",
    "a woman clutching an expensive handbag to her chest anxiously, face half in shadow",
    "a student frantically copying every word into a notebook, eyes down, blurred lecture hall",
    "a student listening with shining eyes, pen resting, absorbed in thought, warm window light",
    "close-up of a wall of identical locked safe deposit boxes, cold metallic light",
    "a man polishing an expensive car alone in a garage at night, obsessive, single overhead lamp",
    "a hoarder's room seen through a doorway, piles of objects to the ceiling, a narrow path, dim light",
    # 사랑
    "a couple sitting at opposite ends of a long dinner table in silence, candles between them, cold mood",
    "a jealous hand gripping another person's wrist tightly, close-up",
    "an elderly couple laughing together while walking slowly in an autumn park, holding hands, golden light",
    "two people talking warmly on a bench by a lake, leaning toward each other, listening, soft evening light",
    # 존재양식
    "a child completely absorbed in building a sandcastle on a beach, wind in hair, sunset",
    "an old man playing a cello alone with eyes closed, warm lamp, dark background",
    "a woman kneading bread dough with floured hands, close-up, morning kitchen light",
    "a person standing alone on a hilltop at sunrise with arms open, mist in the valley below",
    "hands gently releasing a small bird into the open sky",
    "an open hand palm up holding nothing, light falling on it, dark background",
    "a gardener kneeling in a vegetable garden, hands in the soil, smiling quietly",
    "a group of people sharing a simple meal at a long outdoor table under trees, laughter",
    # 불안 · 잃음
    "a man standing in the ashes of his burned house at dawn, empty-handed",
    "a single suitcase left on an empty railway platform in fog",
    "a man in a suit staring at his reflection in a dark window at night, hollow eyes, city lights blurred",
    # 프롬 · 시대
    "an elderly bearded thinker in glasses writing by hand at a wooden desk by a window overlooking a lake, 1970s, soft light",
    "a stormy sea at night with a lighthouse beam cutting through",
    # 끝
    "an empty room with sunlight streaming through a single window onto a bare wooden floor, peaceful",
    "a path through a quiet birch forest in spring, sunlight, no people",
    "close-up of a dandelion seed head in a hand, seeds blowing away in the wind",
    "a calm lake at dawn reflecting the sky, a small rowboat, mist",
    "a mother and small child lying in tall grass looking up at the clouds",
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
    base, scenes, tag = BASE, SCENES, "f"
    OUT.mkdir(parents=True, exist_ok=True)
    made = 0
    t0 = time.time()
    for i, scene in enumerate(scenes, 1):
        prompt = f"{base}. {scene}"
        for k in range(per):
            seed = 49000 + i * 100 + k * 7
            img = generate(prompt, seed)
            if not img:
                continue
            path = OUT / f"mood_{tag}{i:02d}_{k+1}.jpg"
            path.write_bytes(img)
            made += 1
            print(f"[{made}] {path.name}  ({time.time()-t0:.0f}s)  {scene[:50]}", flush=True)
    print(f"\n✅ {made}장 생성 / {time.time()-t0:.0f}초", flush=True)


if __name__ == "__main__":
    main()

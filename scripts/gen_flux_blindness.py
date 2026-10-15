#!/usr/bin/env python3
"""「눈먼 자들의 도시」(주제 사라마구) Flux 무드 이미지 배치 생성

익명의 도시, 하얀 실명(우유 바다), 버려진 정신병원 격리, 의사의 아내, 화재와 탈출, 폐허의 도시, 비, 개, 회복.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 얕은 심도 · 민무늬 벽 · 클로즈업(위저드 베이커리 10/14 2차 방식). 도시는 짙은 하얀 안개 속 원경만, 간판·신호등 숫자·차 번호판 금지.
→ 군인은 실루엣·뒷모습(계급장·글자 없음). 폭력·성폭력은 그리지 않는다.
→ 하얀 실명이라 처음부터 밝은 우윳빛 톤. 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_blindness.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-13 /health 로 9010 확인
OUT = Path("assets/images/Blindness_flux")   # 검수 후 옮긴다

BASE = ("cinematic film still, milky white diffused light, overexposed soft whites, pale cream and cold grey-blue palette, "
        "extreme shallow depth of field, soft bokeh, plain bare walls, gentle film grain, haunting and humane mood, "
        "no signs, no posters, no labels, no license plates, no badges, no traffic light numbers, "
        "no text, no letters, no numbers, no writing anywhere")

SCENES = [
    # 하얀 실명
    "a man's face behind a car windshield in shock, eyes wide open, pure white glow filling the frame, close-up",
    "a sea of pure milky white light swallowing everything, abstract, soft and terrifying",
    "close-up of a human eye with a pale milky haze reflected in it, soft light",
    "a man's hands groping in front of him in a bright white void, close-up",
    # 확산
    "a doctor in a white coat looking into an eye with an ophthalmoscope, bright clinic with bare white walls, close-up",
    "an ophthalmologist alone at night at his desk lit by a lamp, rubbing his eyes, bare wall, worried",
    "a woman in dark sunglasses with long dark hair, elegant and still, pale background, close-up",
    "an old man with a black eye patch and white stubble, gentle face, pale background, close-up",
    "a small boy with a slight squint clutching his own sleeve, looking lost, soft pale light",
    # 격리
    "a long bare corridor of an abandoned old hospital with peeling white walls and pale light, empty",
    "rows of iron hospital beds in a bare dormitory ward under pale window light, empty and cold",
    "silhouettes of soldiers with rifles standing far away behind a gate in pale white fog, no insignia",
    "a rope stretched along a bare wall as a guide line, hands following it, close-up",
    "a middle-aged woman with calm determined eyes standing beside a blind man, holding his arm, bare wall, soft light",
    "close-up of a woman's eyes, the only eyes that can see, clear and full of grief, pale light",
    # 지옥
    "blind people sitting on iron beds in a dim crowded ward, faces turned in different directions, pale light, no gore",
    "empty food crates on a bare concrete floor under a single pale shaft of light",
    "a woman's hand gripping a pair of scissors at her side, close-up, trembling, pale light",
    "orange fire glowing through the windows of a bare old building at night, smoke rising into white haze",
    # 폐허의 도시
    "a wide empty city street completely swallowed by thick white fog, abandoned cars as faint shapes, no signs visible",
    "a line of blind people holding each other's shoulders walking through white fog, seen from behind",
    "a stray dog in white haze on an empty road, soft focus",
    "a woman leading a small group of people by the hand through misty empty ruins, seen from behind",
    "a dog gently licking tears from a woman's face, close-up, tender, soft light",
    "three women standing on a balcony in heavy rain, faces turned up, washing themselves in the rain, joy, soft grey light",
    "rain falling on a quiet balcony with water streaming, close-up, cleansing",
    "a small cozy apartment living room with bare walls where tired people sleep on the floor, morning light",
    "statues of saints in a quiet church with white cloth tied over their eyes, soft pale light, no writing",
    # 회복
    "a man's face in tears of joy as color returns to his eyes, close-up, warm light breaking through white",
    "sunlight breaking through white fog over a quiet city of rooftops, hopeful",
    "a woman looking up at a bright white sky from a balcony, fear and wonder, seen from below",
    "an open window with white curtains blowing in bright morning light, empty room",
    "close-up of two hands holding each other tightly, soft white light",
    "a white bird flying across a pale bright sky, soft focus",
    "a woman's face in profile with closed eyes, peaceful, white light around her",
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
            seed = 88000 + i * 100 + k * 7
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

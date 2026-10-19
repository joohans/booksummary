#!/usr/bin/env python3
"""「천 개의 파랑」(천선란) Flux 무드 이미지 배치 생성

근미래 경마장 → 휴머노이드 기수 콜리와 경주마 투데이 → 하늘 한 조각 → 낙마 → 폐기 직전의 로봇
→ 연재가 고치는 콜리 → 보경의 식당·휠체어 탄 은혜 → 수의사 복희 → 가장 느린 경주 → 파란 하늘.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 경마장 전광판·번호 조끼·간판은 글자가 붙는다 → 「no numbers on saddle cloth, no scoreboard」, 클로즈업·하늘 위주.
→ 로봇은 「simple rounded green-gray humanoid, no logos」. 인물마다 Korean 명시. 처음부터 밝은 톤.
→ 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_blue.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-19 /health 로 9010 확인
OUT = Path("assets/images/A_Thousand_Blues_flux")   # 검수 후 옮긴다

BASE = ("luminous gentle painterly film still, near-future Korea, bright soft daylight, "
        "vivid sky blue, soft white and warm sand palette, bright enough to see clearly, not dark, "
        "extreme shallow depth of field, soft bokeh, gentle film grain, tender hopeful mood, "
        "no scoreboard, no numbers on saddle cloth, no signboards, no signs, no logos, no text, no letters, no numbers, no writing anywhere")

K = "Korean people with black hair"
R = "a small slim humanoid robot jockey with a simple rounded green-gray body and gentle glowing eyes, no logos"
SCENES = [
    # 하늘 · 천 개의 단어
    "a vast clear blue sky with soft white clouds seen from below, luminous, peaceful",
    f"{R} looking up at a small patch of blue sky through a narrow gap in a dim storage room, wonder, close-up",
    "many shades of blue swirling together like watercolor in the sky, dreamy, abstract",
    # 경마 · 콜리와 투데이
    f"{R} riding a beautiful dark bay racehorse at full gallop on a sandy track, motion blur, bright daylight",
    "close-up of a racehorse's head and flaring nostrils at full speed, dust, sunlight",
    f"close-up of {R} gripping the reins, leaning forward, intense",
    "a crowded racecourse grandstand blurred in the background behind galloping horses, no signs, no scoreboard",
    "close-up of a horse's foreleg and hoof striking sand, slow motion dust",
    # 고통 · 낙마
    "a tired racehorse with sad eyes in a stable stall, soft light, close-up",
    f"{R} falling from a galloping horse in mid air against a blue sky, slow motion, dramatic",
    f"a broken {R} lying on the sandy track with a cracked arm, sky reflected in its eyes",
    "a horse standing alone in an empty racetrack at dusk, quiet, melancholy",
    # 폐기 직전 · 연재
    f"a broken {R} folded in a dusty storage corner among discarded parts, soft light",
    f"a 17-year-old Korean girl with short hair and safety goggles repairing a small humanoid robot at a cluttered workbench, focused, {K}",
    "close-up of hands soldering tiny wires inside a robot arm, sparks, warm light, no text",
    f"a Korean teenage girl and {R} sitting side by side on a rooftop looking at the sky, {K}",
    # 보경 · 은혜 · 집
    f"a tired Korean mother in an apron cooking chicken soup in a small restaurant kitchen, steam, warm light, no signs, {K}",
    f"a gentle Korean teenage girl in a wheelchair smiling at a horse over a fence, bright daylight, {K}",
    f"two Korean sisters laughing together in a small cozy room, one in a wheelchair, warm light, {K}",
    "an old firefighter's helmet on a shelf beside a framed photo with no visible face, soft light, no text",
    # 지수 · 학교
    f"two Korean high school girls arguing then laughing at a school lab table with robot parts, {K}",
    # 복희 · 민주 · 서진
    f"a young Korean female veterinarian gently stroking a horse's neck in a stable, worried, {K}",
    f"a Korean man in a plain dark jacket secretly taking photos with a camera behind a stable fence, {K}",
    f"a stern Korean woman manager in a plain uniform with no badges handing over a broken robot to a teenage girl, {K}",
    # 계획
    f"a group of Korean people of different ages huddled around a kitchen table planning at night, warm lamp, {K}",
    f"{R} gently touching a horse's face in a quiet stable, tender, close-up",
    "close-up of a horse's eye reflecting blue sky, gentle",
    # 가장 느린 경주
    f"a racehorse walking slowly and calmly alone down a sunlit racetrack while blurred spectators stand up, {K}",
    "a horse cantering slowly with its mane flowing in the wind, golden light, peaceful",
    f"blurred Korean spectators in a stand with hands over their mouths, moved, tears, no signs, {K}",
    f"a Korean girl in a wheelchair crying and smiling at the racetrack fence, {K}",
    # 진동 · 행복 · 파랑
    f"{R} sitting quietly beside a girl on grass, her hand on its shoulder, warm sunset",
    "a horse grazing freely in a wide green meadow under a big blue sky, peaceful",
    f"{R} looking up at the open blue sky with arms slightly raised, luminous, peaceful",
    "a single feather drifting in a vast blue sky, close-up, hopeful",
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
            seed = 49000 + i * 100 + k * 7
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

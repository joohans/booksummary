#!/usr/bin/env python3
"""「쇼코의 미소」(최은영) Flux 무드 이미지 배치 생성

표제작: 소도시 고교·일본 교환학생 쇼코의 미소 → 편지(접힌 뒷면만) → 일본 시골집의 쇼코
→ 좌절한 소유·비 오는 날 할아버지와 우산 → 장례·재회 → 서늘한 미소.
다른 수록작: 베트남 이웃(씬짜오), 프랑스 수도원(한지와 영주), 광장의 노인과 중년 여성(미카엘라)은 클로즈업으로.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]). ★ 배경은 장면별로만(BASE 금지, 초정리 편지 10/21).
→ 학교·역·광장·도쿄 거리는 간판·글씨 위험 → 빼거나 흐린 배경으로. 인물마다 국적 명시. 밤 장면 금지(지구 끝의 온실 10/22 b<60).
→ 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_shoko.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-19 /health 로 9010 확인
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Shokos_Smile_flux"))   # 검수 후 옮긴다

BASE = ("quiet literary film still, soft natural daylight, bright enough to see clearly, not dark, "
        "muted pastel palette of pale blue, soft grey and warm beige, extreme shallow depth of field, soft bokeh, gentle film grain, "
        "tender melancholy mood, no signboards, no signs, no logos, no labels, no text, no letters, no numbers, no writing anywhere")

KO = "a Korean girl with black hair"
JP = "a Japanese girl with black hair"
SCENES = [
    # 만남
    f"{KO} of sixteen in a plain school uniform standing at the gate of a quiet house in a small Korean town, curious, soft morning light",
    f"{JP} of sixteen with a polite gentle smile, close-up portrait, soft window light, calm distant eyes",
    f"two teenage girls, one Korean and one Japanese, sitting side by side on a wooden floor of a Korean house, slight distance between them, afternoon light",
    f"close-up of a Japanese teenage girl's polite smile while looking slightly away, enigmatic, soft light",
    f"an old Korean grandfather with grey hair sitting silently on a porch, stern but gentle face, afternoon light",
    f"a Korean grandfather and a Japanese teenage girl drinking tea together at a low table, quiet warmth",
    # 편지
    "a stack of folded letters tied with string on a wooden desk, envelopes seen from the blank back, soft daylight, no writing",
    f"close-up of an old man's wrinkled hands holding a folded letter, blank back side only, by a window",
    f"{KO} reading a folded letter by a window, letter seen from behind, wistful, close-up",
    "a red mailbox-free country road in Korea in autumn, telephone poles, soft haze, no signs",
    # 일본
    "a quiet Japanese countryside house with a tiled roof and a small garden, overcast soft light, no signs",
    f"{JP} in her early twenties sitting alone in a dim tatami room with a sliding paper door, tired eyes, soft grey daylight",
    f"a Korean young woman and a Japanese young woman standing apart in a Japanese garden, tense silence, soft light",
    "a small rural Japanese train platform seen from afar in soft rain, empty, no signs, blurred",
    # 좌절
    f"a Korean young woman in her twenties sitting on the floor of a small cramped studio apartment surrounded by film reels, defeated, grey daylight",
    "close-up of an old film camera on a cluttered desk, dust, soft light",
    f"{KO} in her twenties staring out a rainy window, raindrops on glass, melancholy",
    # 비 오는 날 할아버지
    f"an old Korean grandfather in a worn coat standing at a small apartment door on a rainy day, wet shoulders, shy",
    f"an old Korean man walking away down a narrow rainy alley, seen from behind, no signs",
    f"{KO} in her twenties running after an old man in the rain holding out a black umbrella, tears, soft grey light",
    "close-up of a hand holding out a black umbrella in the rain, raindrops, emotional",
    # 이별과 재회
    "white chrysanthemums on a simple table in a quiet room, soft daylight, mourning",
    f"a Korean young woman and a Japanese young woman sitting side by side on a bench by the sea, overcast, quiet",
    "close-up of a bundle of old letters being handed from one hand to another, blank backs only",
    f"{JP} in her twenties with a polite smile, close-up, cool soft light, slightly distant",
    f"{KO} in her twenties watching someone leave, wistful, close-up, soft light",
    # 다른 수록작
    f"a middle-aged Vietnamese woman cooking in a small kitchen in Germany, warm light, gentle sad eyes",
    f"a Korean girl and a Vietnamese woman sitting at a dinner table with dishes, quiet, warm light",
    "an old stone monastery cloister in rural France with a quiet garden, soft morning light",
    "a young Black Kenyan man and a Korean young woman walking slowly in a French countryside field, talking, soft light",
    "a rhinoceros standing in golden savanna grass, calm, soft light",
    f"an elderly Korean woman and a middle-aged Korean woman walking together through a wide city square, seen from behind, blurred crowd, no signs",
    "many yellow ribbons tied on a fence, fluttering in the wind, soft daylight, no writing",
    # 결말
    "a calm grey sea under an overcast sky, quiet, cool light",
    "a soft white sky with a single bird flying, cool and quiet",
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
            seed = int(os.environ.get("SEED_BASE", "41000")) + i * 100 + k * 7
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

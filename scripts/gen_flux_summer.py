#!/usr/bin/env python3
"""「바깥은 여름」(김애란) Flux 무드 이미지 배치 생성

스노볼(안은 눈, 바깥은 여름) → 입동(아이 잃은 부부, 자정의 도배) → 노찬성과 에반(소년과 유기견)
→ 건너편(공무원 시험 연인) → 침묵의 미래(사라지는 언어의 박물관) → 풍경의 쓸모(태국 여름)
→ 가리는 손(손으로 가린 얼굴) → 어디로 가고 싶으신가요(계곡, 편지).
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 거리·학원가는 간판 지옥(엄마를 부탁해 역 장면 교훈). 실내 맨벽·클로즈업·자연 위주.
→ 휴대폰·CCTV 화면은 「뒤에서 / 빛만」. 편지는 「blank」. 인물마다 Korean 명시.
→ 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_summer.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-19 /health 로 9010 확인
OUT = Path("assets/images/Outside_Is_Summer_flux")   # 검수 후 옮긴다

BASE = ("luminous quiet painterly film still, contemporary Korea in the 2010s, bright soft daylight, "
        "pale summer green, white and soft sky blue palette, bright enough to see clearly, not dark, "
        "extreme shallow depth of field, soft bokeh, gentle film grain, restrained melancholic and tender mood, "
        "no signboards, no signs, no logos, no text, no letters, no numbers, no writing anywhere")

K = "Korean people with black hair"
SCENES = [
    # 표제 — 스노볼
    "close-up of a glass snow globe with white snow swirling inside, sitting on a sunny summer windowsill with green leaves outside",
    "a snow globe held in a hand against a bright summer field, snow inside, heat haze outside, close-up",
    # 입동
    f"a young Korean couple pasting wallpaper on an apartment wall late at night under a single lamp, exhausted, silent, {K}",
    "a small empty child's room with pale walls and a tiny bed, toys neatly placed, soft light, no text",
    "close-up of a rolled sheet of plain flowered wallpaper and a brush with paste, soft light",
    f"a grieving young Korean mother sitting on the floor of a half-papered room, face hidden, {K}",
    f"blurred Korean neighbors whispering together in an apartment corridor, soft focus, {K}",
    "a first frost on a window of a high-rise apartment at dawn, pale light",
    # 노찬성과 에반
    f"a little Korean boy in summer clothes sitting on a curb hugging a small old white dog, warm afternoon, {K}",
    f"an elderly Korean grandmother and her grandson eating dinner at a low table in a tiny room, soft light, {K}",
    f"a little Korean boy walking a small limping dog down a quiet riverside path at sunset, seen from behind, {K}",
    "an empty dog leash lying on a summer sidewalk in sunlight, close-up",
    # 건너편
    f"a young Korean couple sitting apart at a small cafe table, not looking at each other, quiet, blurred background, no signs, {K}",
    "two stacks of thick plain exam books on a small desk in a tiny study room, close-up, no visible titles",
    f"a young Korean woman in a police uniform without insignia speaking into a microphone in a broadcast booth, distant look, {K}",
    "a long bridge over a wide river at dusk with the far bank blurred, quiet",
    # 침묵의 미래
    "a vast quiet museum hall with rows of empty glass display cases filled with soft light, no labels, surreal",
    "an old person sitting alone in a glass room inside a museum, viewed by blurred visitors, surreal and lonely",
    "a breath of luminous mist leaving an old person's lips and drifting into the air, close-up, surreal",
    "wisps of glowing light floating up from a quiet crowd and vanishing into a high ceiling, surreal",
    # 풍경의 쓸모
    f"a Korean man in his thirties standing on a tropical beach in Thailand holding a phone seen from behind, anxious, bright summer light, {K}",
    f"an elderly Korean mother and a young wife walking on a sunny tropical beach under palm trees, {K}",
    "a tropical resort pool under blazing summer sun with palm trees, empty, bright",
    f"an older Korean man with an awkward smile in a faded photograph held in a hand, close-up, no text, {K}",
    # 가리는 손
    f"a Korean single mother watching her teenage son from a kitchen doorway with an uneasy expression, soft light, {K}",
    f"a mixed-race Korean teenage boy covering his mouth with his hand, ambiguous expression, close-up, {K}",
    "a grainy security camera still of an empty night street corner seen from above, blurred, no timestamp, no text",
    f"a teenage boy blowing out candles on a birthday cake, the room turning dark, close-up, {K}",
    # 어디로 가고 싶으신가요
    "a clear mountain valley stream with smooth rocks in summer, bright, quiet",
    "rushing water in a deep green mountain valley, sunlight on the surface, close-up",
    f"a Korean widow in her thirties sitting alone in a dim apartment holding a phone that glows on her face, seen from the side, screen not visible, {K}",
    "an empty man's jacket hanging on a chair by a window, soft light",
    f"a Korean woman holding a handwritten letter on plain paper with no visible words, tears in her eyes, close-up, {K}",
    "a young boy's hand reaching up out of clear water toward sunlight, seen from below, hopeful, surreal",
    "a summer window with sheer curtains blowing and bright green trees outside, hopeful",
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
            seed = 59000 + i * 100 + k * 7
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

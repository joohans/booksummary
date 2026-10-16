#!/usr/bin/env python3
"""「메리골드 마음 세탁소」(윤정은) Flux 무드 이미지 배치 생성

언덕 위 꽃잎 사이로 피어난 마음 세탁소, 지은, 차 한 잔, 얼룩과 주름, 손님들(재하·연희·은별·연자), 백만 번의 환생, 메리골드 꽃.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 현대 한국 거리·가게 정면은 간판 지옥(10/14). 세탁소는 「동화풍 2층 집」 외관만, 실내는 얕은 심도·민무늬 벽·클로즈업.
→ 부정어는 일반어만. 화면·휴대폰은 뒤에서 보거나 빛만(은별 인플루언서). 처음부터 밝은 톤.
→ 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_marigold.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-13 /health 로 9010 확인
OUT = Path("assets/images/Marigold_Mind_Laundry_flux")   # 검수 후 옮긴다

BASE = ("storybook healing fantasy film still, warm golden afternoon light, marigold orange, cream and soft sage palette, "
        "extreme shallow depth of field, soft creamy bokeh, plain painted walls, gentle film grain, tender and comforting mood, "
        "no logos, no text, no letters, no numbers, no writing anywhere")

SCENES = [
    # 언덕 위 세탁소
    "a small two-story fairy-tale cottage on top of a green hill surrounded by blooming orange marigolds under a soft sky, no signs",
    "a cottage magically blooming out of a swirl of red flower petals on a hilltop, fantasy, golden light",
    "a field of bright orange marigold flowers swaying in warm wind, close-up",
    "white linen sheets drying on a clothesline on a sunny hilltop, wind, flower petals flying",
    # 지은
    "a calm young Korean woman in her late twenties with long dark hair and a cream apron, gentle sad eyes, close-up portrait, warm bokeh",
    "a young woman pouring golden tea from a glass teapot into a white cup, close-up of hands, steam, warm light",
    "a cup of tea with a single marigold petal floating on it on a wooden table, close-up, soft light",
    "a young woman ironing a white shirt with soft glowing light rising from the fabric, magical, close-up",
    "a white shirt with a dark stain slowly fading away in soap bubbles, close-up, magical",
    # 능력 · 부모 실종
    "a small girl standing alone in a glowing meadow as two figures of parents fade into light particles, fantasy, emotional",
    "a little girl hugging her knees alone in a vast empty field at dusk, lonely",
    "many floating translucent images of the same woman across different eras drifting like petals in the sky, rebirth, dreamy",
    "an hourglass with orange sand on a windowsill at sunset, close-up",
    # 손님들
    "a tired young Korean man in his thirties sitting alone in a dim small basement room holding an old film camera, lonely",
    "a young man drinking tea at a wooden counter, his tense face softening, warm light",
    "a young Korean woman in her twenties with tear-streaked face holding a cup of tea, close-up, warm bokeh",
    "a young woman letting go of a red balloon into a blue sky, seen from behind, release",
    "a young woman sitting on her bed at night lit only by the glow of a phone held away from the camera, exhausted, lonely",
    "a young woman stepping out into morning sunlight, eyes closed, breathing deeply, relief",
    "a middle-aged Korean woman with kind tired eyes working in a small restaurant kitchen, warm light, dignified",
    "close-up of worn hands of a middle-aged woman holding a warm cup, gentle smile in soft focus",
    "a hand smoothing a wrinkled cloth with an iron, wrinkles disappearing, close-up, soft light",
    # 마을 사람들
    "a group of neighbors laughing together around a small table with snacks under a warm string light at dusk",
    "a delivery man in his forties with a shy smile holding a small cardboard box with no markings, soft focus",
    # 지은 자신의 얼룩
    "a young woman sitting alone by a window at night with a cup of tea, finally crying, soft moonlight",
    "a young woman meeting a small girl version of herself in a sunny meadow, both smiling, dreamlike",
    "a mother hugging a little girl in a field of marigolds, warm golden haze, memory",
    "a young woman brewing tea for herself, smiling gently, morning light",
    # 반드시 오고야 말 행복
    "a young woman walking down a hill path with wind blowing her hair and flower petals, determined smile",
    "orange marigold petals carried by the wind over a small village at sunset",
    "a bus window with sunset light and a woman's reflection smiling softly, seen from inside, no signs",
    "a hilltop at golden hour with a lone cottage glowing warmly, peaceful",
    "close-up of a single orange marigold in morning dew, hopeful",
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
            seed = 91000 + i * 100 + k * 7
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

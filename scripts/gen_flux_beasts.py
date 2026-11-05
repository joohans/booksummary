#!/usr/bin/env python3
"""「작은 땅의 야수들」(김주혜) Flux 무드 이미지 배치 생성

1917 평안도 설산의 호랑이·사냥꾼·일본군 장교 → 평양 기생집의 어린 옥희(월향·연화) → 경성의 소년 정호와 거리의 아이들
→ 인력거꾼 고학생 한철 → 1919 흰옷의 군중 → 1930년대 무대의 옥희 → 전쟁·광복 → 정호의 최후 → 제주 해녀와 노년의 옥희.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 경성 거리·간판·현판·태극기·신문·군복 계급장 금지,
실내는 맨벽·창호지, 야외는 산·눈·들판·바다. 35mm period film still BASE(모서리 서명 0). 밤 장면 금지. 인물마다 「Korean … black hair」.

    SEED_BASE=56000 .venv/bin/python scripts/gen_flux_beasts.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Beasts_of_a_Little_Land_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still, soft natural daylight, bright enough to see clearly, not dark, "
        "muted palette of snow white, pine green, faded indigo and warm earth brown, shallow depth of field, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no numbers, no writing anywhere, no flags, no watermark, no signature")

HUNTER = "a rugged Korean hunter in his thirties with black hair and a thin beard, in a padded cotton jacket and fur hat, 1917"
OFFICER = "a Japanese army officer with short black hair in a plain olive wool greatcoat without insignia, 1917"
OKHUI = "a ten-year-old Korean girl with long black braided hair, in a faded pink hanbok, 1918"
OKHUI_W = "a graceful Korean woman in her twenties with black hair in a low bun, in an elegant pale jade hanbok, 1930s"
GISAENG = "two young Korean women with black hair in a low bun, in soft colored hanbok, 1920s"
JUNGHO = "a thin Korean street boy of about twelve with cropped black hair, in a patched grey cotton jacket, 1918"
JUNGHO_M = "a lean Korean man in his twenties with short black hair and intense eyes, in a dark wool coat, 1930s"
HANCHUL = "a young Korean man with neat black hair in a plain white shirt and dark trousers, 1920s"
OLD = "an old Korean woman in her seventies with grey hair tied back, in plain white cotton clothes, 1960s"
HAENYEO = "a Korean woman diver with black hair in a plain black diving suit and round goggles pushed up, 1960s"

SCENES = [
    # 1917 설산
    "a vast snowy mountain forest of tall pines in northern Korea on a bright winter morning, mist between the ridges",
    "fresh tiger paw prints in deep snow between pine trees, close-up, soft morning light",
    "a huge Siberian tiger standing in deep snow among pine trees, staring ahead, bright winter daylight",
    f"{HUNTER} crouching behind a snowy rock holding an old matchlock rifle, breath steaming, bright daylight",
    f"{OFFICER} fallen in the snow among pines, looking up in fear, bright winter light",
    f"{HUNTER} standing over a dead tiger in the snow, solemn, pine forest behind, overcast bright light",
    "a small thatched-roof mountain hut half buried in snow with smoke rising, bright winter afternoon",
    # 옥희의 어린 시절
    f"{OKHUI} standing alone in a frozen rice field with distant blue mountains, bright cold morning",
    f"{OKHUI} holding a small cloth bundle, looking back over her shoulder on a dirt country road, soft daylight",
    "a quiet courtyard of a traditional Korean tiled-roof house with a plain plastered wall and a persimmon tree, soft daylight",
    f"{OKHUI} kneeling on a wooden floor learning to fold silk, soft light through paper sliding doors",
    f"{GISAENG} playing a gayageum zither in a bright room with paper sliding doors, 1920s",
    f"{OKHUI} watching two older girls dance with long hanbok sleeves in a sunlit courtyard",
    "close-up of a girl's hands playing gayageum strings, soft window light, shallow depth of field",
    # 정호
    f"{JUNGHO} sitting on a stone riverbank with a group of ragged street children, hazy morning",
    f"{JUNGHO} running barefoot along a dirt riverside path, motion blur, bright daylight",
    f"{JUNGHO} peeking from behind a plastered wall at a girl in a pink hanbok, sunlight",
    f"{JUNGHO} and {OKHUI} sharing a steamed sweet potato on a stone step, warm afternoon light",
    # 한철
    f"{HANCHUL} pulling an empty wooden rickshaw along a quiet tree-lined dirt road, autumn daylight",
    f"{HANCHUL} reading a book with a plain blank cover by a window, soft daylight, close-up",
    "an old wooden rickshaw resting under a ginkgo tree with yellow leaves, soft autumn light, close-up",
    # 1919
    "a large crowd of Koreans in white clothes raising their hands and shouting on an open dirt field, 1919, bright spring daylight",
    "a sea of white cotton clothes and raised hands, close-up from behind the crowd, dust in sunlight, 1919",
    "a Korean schoolgirl in a white jeogori and black skirt with her fist raised among a crowd, 1919, bright daylight",
    "Japanese soldiers in plain olive uniforms marching on a dusty country road, 1919, from behind, hazy light",
    # 경성 1930년대
    f"{OKHUI_W} looking at herself in a round wooden mirror, soft window light, close-up",
    f"{OKHUI_W} standing on a simple wooden theater stage under a warm spotlight, red velvet curtain, 1930s",
    f"{OKHUI_W} and {HANCHUL} walking side by side along a riverside path under cherry blossoms, 1930s",
    f"{OKHUI_W} crying alone on a stone bench under bare trees, overcast soft light",
    f"{JUNGHO_M} standing in the shadow of a plastered alley wall, watching, soft afternoon light",
    f"{JUNGHO_M} handing a small gold ring to {OKHUI_W} by a window, soft warm light, close-up of hands",
    "a small gold ring on an open palm, soft warm light, extreme close-up",
    "an old silver cigarette case on a wooden table, soft window light, close-up, plain surface",
    # 전쟁·광복
    f"{JUNGHO_M} in a cold prison cell with a small barred window, a beam of daylight on his face",
    "a crowd of Koreans in white clothes cheering with raised arms on a sunny hillside, 1945, joy",
    f"{OKHUI_W} standing on a hill looking at a valley of rice fields, wind in her hanbok, bright day",
    f"{JUNGHO_M} walking alone across a snowy field toward distant mountains, from behind, bright winter light",
    "a tiger walking away into a misty snowy pine forest, seen from behind, soft light",
    # 1964 제주
    "black volcanic rocks on the coast of Jeju island with turquoise waves, bright sunny day",
    f"{HAENYEO} floating in clear turquoise water holding an orange float, bright sunlight",
    f"{OLD} sitting on black volcanic rocks by the sea, holding a sleeping baby wrapped in cloth, bright soft light",
    f"{OLD} gazing at the calm sea with a gentle smile, wind in her grey hair, close-up, golden light",
    "a stone wall of black volcanic rock with yellow canola flowers behind it, Jeju, bright spring day",
    "sunlight sparkling on a calm blue sea at golden hour, a lone diver's float on the water",
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
            seed = int(os.environ.get("SEED_BASE", "56000")) + i * 100 + k * 7
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

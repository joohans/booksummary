#!/usr/bin/env python3
"""「위저드 베이커리」(구병모) Flux 무드 이미지 배치 생성

말더듬는 열여섯 살 소년, 마법사 점장과 파랑새 소녀, 마법의 빵들, 타임 리와인더(머랭 쿠키), 두 개의 결말.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 시간을 파는 상점(10/14)에서 현대 한국 거리·가게 정면은 80장 중 29장이 간판으로 폐기됐다.
   거리·간판·기차역·경찰차는 넣지 않는다. 빵집은 실내·작업대·오븐·진열 클로즈업만, 가격표·메뉴판 없이.
→ 사건(아동 대상 범죄)은 그리지 않는다. 불안은 빈 복도·닫힌 문·빗물로만.
→ 처음부터 밝은 톤(밝기 ≥60). 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_wizard.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-13 /health 로 9010 확인
OUT = Path("assets/images/Wizard_Bakery_flux")   # 검수 후 옮긴다

# ── 2차(10/14): 1차 80장 중 67장이 간판·포스터로 폐기됐다. 「contemporary Korea」+빵집 = 간판 지옥.
#    한국 설정어를 빼고, 얕은 심도 클로즈업 · 민무늬 회벽 · 자연 · 동화풍 실내로만 짠다.
BASE = ("storybook magical realism film still, extreme shallow depth of field, soft creamy bokeh background, "
        "plain whitewashed plaster walls, warm golden light, cream, caramel and soft blue palette, gentle film grain, "
        "no signs, no posters, no labels, no paper notes, no screens, no text, no letters, no numbers, no writing anywhere")

SCENES = [
    "close-up of a teenage East Asian boy's face lit by warm golden light, cautious eyes, black and white striped shirt",
    "a teenage boy in a striped shirt hugging his knees on a wooden floor beside a plain white wall, soft window light",
    "close-up of a boy's trembling lips and hand covering his mouth, struggling to speak, soft light",
    "a boy's hand holding a plain bread roll, close-up, warm evening light",
    "an old wooden door closed with soft light under it, plain white wall, stillness",
    "a single small child's red shoe lying on a wooden floor near a plain wall, soft light, melancholy",
    "a boy running through a dark wet night street of plain brick walls, warm light ahead, motion blur, nobody else",
    "close-up of fresh bread loaves on a rustic wooden shelf, warm bokeh",
    "a pale young man with a small ponytail in a white baker's coat, close-up portrait, calm enigmatic gaze, plain plaster wall behind",
    "close-up of a baker's floury hands shaping dough, magical golden dust rising, dark warm background",
    "a large round antique iron oven door glowing from inside, brick around it, close-up, warm magical light",
    "a boy crawling into a glowing golden tunnel inside an oven, seen from behind, fairy tale",
    "a cozy secret bedroom with a big carved wooden bed and golden lamp light, plain walls, fairy tale",
    "a small bright blue bird perched on a jar of flour, close-up, warm bokeh",
    "a blue bird in flight with wings spread against a warm golden blurred background, close-up",
    "close-up portrait of a gentle young woman with a bright blue feather in her black hair, soft smile, warm bokeh",
    "a young woman's hand opening and a blue bird flying out of it, sparkles, magical",
    "close-up of dark red cinnamon cookies on a black plate, ominous glow, shallow depth of field",
    "close-up of golden walnut pretzels linked like a chain, warm light",
    "close-up of pastel macarons and madeleines glowing faintly on parchment paper, magical",
    "close-up of a tiny doll made of colorful jelly candy lying on parchment paper, eerie and delicate",
    "a single white chrysanthemum lying on a plain wooden table, soft morning light",
    "a tearful teenage girl's face in profile, soft warm bokeh, guilt and regret",
    "a frightened young woman's eyes looking back over her shoulder, warm bokeh, close-up",
    "a stern young baker's face half in shadow, cold eyes, close-up, warm rim light",
    "a magical golden light freezing floating flour particles in mid-air, time stopped, abstract",
    "a boy clutching a small paper bag to his chest, close-up, warm evening light, determined face",
    "close-up of a boy's shocked wide eyes in dim light, shallow depth of field",
    "a delicate white meringue cookie cracked in two on a wooden floor, close-up, dramatic light",
    "a white meringue cookie in an open palm glowing, the light swirling backward like a clock rewinding",
    "a spiral of golden light and drifting white petals, time rewinding, abstract and dreamy",
    "a young man in a white apron smiling calmly in a sunlit kitchen with plain white walls, close-up",
    "a young man running down a sunny tree-lined country path holding a bread roll, seen from behind, green leaves, hopeful",
    "warm sunset light through tall trees in a quiet park, golden hour, peaceful",
    "a blue bird sitting on a branch of a blossoming tree in bright spring sunlight, close-up",
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
            seed = 86000 + i * 100 + k * 7
            img = generate(prompt, seed)
            if not img:
                continue
            path = OUT / f"mood_g{i:02d}_{k+1}.jpg"
            path.write_bytes(img)
            made += 1
            print(f"[{made}] {path.name}  ({time.time()-t0:.0f}s)  {scene[:50]}", flush=True)
    print(f"\n✅ {made}장 생성 / {time.time()-t0:.0f}초", flush=True)


if __name__ == "__main__":
    main()

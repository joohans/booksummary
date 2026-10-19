#!/usr/bin/env python3
"""「엄마를 부탁해」(신경숙) Flux 무드 이미지 배치 생성

서울역 인파 속 실종 → 전단지 → 시골집 부엌·밭·재봉질 → 큰아들의 졸업증명서·숙직실 청소 → 담장의 붉은 장미
→ 밖으로 돌던 아버지·두통 → 엄마의 「나」, 「난 이제 이 집에서 나갈라요」 → 텅 비어 간 엄마.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 역·거리·간판은 글자 지옥. 역은 「군중 클로즈업·흐린 배경」만. 재봉틀은 상표가 붙으니 손 클로즈업.
→ 전단지·증명서는 「blank paper」. 인물마다 Korean 명시. 처음부터 밝은 톤.
→ 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_mom.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-18 /health 로 9010 확인
OUT = Path("assets/images/Please_Look_After_Mom_flux")   # 검수 후 옮긴다

BASE = ("luminous tender painterly film still, rural and urban Korea from the 1970s to the 2000s, bright soft daylight, "
        "warm earthy colors, soft red, beige and green, bright enough to see clearly, not dark, "
        "extreme shallow depth of field, soft bokeh, gentle film grain, quiet sorrowful and loving mood, "
        "no signboards, no signs, no logos, no text, no letters, no numbers, no writing anywhere")

K = "Korean people with black hair"
SCENES = [
    # 실종 · 전단지
    f"a crowded blurred stream of commuters in a busy station, an old Korean woman's hand slipping away from an old man's hand, close-up of hands, motion blur, no signs, {K}",
    f"an elderly Korean woman in a simple blue cardigan standing lost and bewildered in a blurred crowd, close-up, {K}",
    f"middle-aged Korean siblings sitting around a table in silence with blank sheets of paper and a pen, worried, {K}",
    "close-up of a hand holding a pen hesitating over a blank sheet of paper, soft light",
    f"a middle-aged Korean woman handing blank flyers to strangers on a blurred street, seen from behind, no text, {K}",
    # 시골집 · 쉴 새 없는 엄마
    "a small Korean country house with a tiled roof and a yard with jars of kimchi and a persimmon tree, 1970s, bright, no signs",
    f"a Korean mother in her forties in a headscarf cooking rice in a huge iron pot over a wood fire in a traditional kitchen, steam, {K}",
    "close-up of a mother's rough hands sewing cloth with a needle and thread, warm light",
    "close-up of hands knitting a wool scarf with needles, warm light, no text",
    f"a Korean mother bending over in a green vegetable field at sunrise, working, seen from afar, {K}",
    f"a Korean mother peeling garlic at night under a dim lamp, tired but tender, close-up, {K}",
    f"a Korean mother packing a heavy cloth bundle of food for her children, close-up, {K}",
    # 큰딸
    f"a Korean woman writer in her forties sitting at a desk by a window in a Seoul apartment, lost in thought, {K}",
    f"a little Korean girl sitting beside her mother who is sewing, looking up at her, 1970s, warm light, {K}",
    # 큰아들 · 졸업증명서 · 숙직실
    f"a young Korean man in 1970s clothes lying awake in a bare small night-duty room, worried, {K}",
    f"a Korean mother in a plain coat holding a folded blank paper standing at a door at night, out of breath, {K}",
    f"a Korean mother sweeping the floor of an empty office at dawn with a broom, quiet light, no text, {K}",
    f"a Korean mother wiping desks one by one in an empty office at dawn, seen from behind, no text, {K}",
    # 장미
    f"a Korean mother planting red rose seedlings along a brick wall in spring, bending, warm light, {K}",
    "close-up of bright red roses in full bloom climbing over a brick wall, sunlight",
    f"a passerby stopping beneath a wall of red roses to smell them, soft focus, {K}",
    # 아버지 · 두통
    f"an elderly Korean man sitting alone on the porch of an empty country house, regretful, {K}",
    f"a Korean man walking ahead quickly on a country road while his wife follows far behind, seen from behind, {K}",
    f"a Korean mother pressing her temple in pain, eyes closed, sitting in a dim corner of a kitchen, close-up, {K}",
    "an empty traditional kitchen with a cold iron pot and a single ray of light, quiet",
    # 엄마의 「나」
    f"an elderly Korean woman in a blue cardigan with bare feet in plastic sandals walking alone on a country path, gentle face, {K}",
    f"an old Korean woman standing at the gate of an old country house, looking back one last time, soft light, {K}",
    f"a young Korean girl in 1950s simple clothes laughing in a field of wildflowers, memory of youth, dreamy, {K}",
    "a white butterfly resting on a wooden gate in soft spring light, close-up",
    f"an old Korean woman's face softly smiling with tears, close-up, warm light, {K}",
    # 에필로그
    "a basket of persimmons and a folded knitted scarf on a wooden floor, close-up, nostalgic",
    f"a middle-aged Korean daughter hugging her mother's old cardigan, crying, close-up, {K}",
    "an empty rocking chair by a window with sunlight falling on it, quiet",
    "a single red rose lying on a wooden table in morning light, close-up",
    "a country road disappearing into soft morning mist with wildflowers, hopeful",
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
            seed = 69000 + i * 100 + k * 7
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

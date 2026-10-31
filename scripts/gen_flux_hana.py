#!/usr/bin/env python3
"""「지구에서 한아뿐」(정세랑) Flux 무드 이미지 배치 생성

환생 수선집의 한아(헌 옷 리폼·저탄소 생활) → 11년 연인 경민, 캐나다 유성우·운석 → 낯설어진 경민(흉터 없음·가지무침·연필심·다이아몬드)
→ 광물 외계인의 정체·먼 별에서 지켜본 사랑 → 우주를 떠도는 진짜 경민 → 요원·열성 팬 → 받아들이는 사랑 → 결혼·청소년 쉼터
→ 돌아온 「엑스」의 소멸·우주선으로 떠나보냄 → 늙은 한아와 그, 한 방향을 바라보는 두 사람.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 간판·거리·공항·재봉틀(상표)·치약 튜브·연필 몸통 금지.
35mm 필름 스틸 BASE(모서리 서명 0). 한국인 인물은 매번 「Korean … black hair」. ★ 배경은 장면별로만. 밤 장면 금지(밝기 ≥60).

    .venv/bin/python scripts/gen_flux_hana.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Only_Hana_on_Earth_flux"))   # 검수 후 옮긴다

BASE = ("35mm film still, soft natural daylight, bright enough to see clearly, not dark, "
        "gentle pastel palette of cream, sage green, soft pink and pale sky blue, shallow depth of field, light film grain, "
        "tender, warm, whimsical romantic mood, no logos, no text, no letters, no numbers, no signs, no writing anywhere, no watermark, no signature")

HA = "a Korean woman of thirty-one with black shoulder-length hair and a gentle round face, wearing a loose cream linen shirt"
KM = "a lanky Korean man of thirty-one with messy black hair and light stubble, restless faraway look"
AL = "a Korean man of thirty-one with neat black hair, clean-shaven, calm devoted gaze, plain grey sweater"
YU = "a Korean woman of thirty-two with a short black bob haircut and sharp but kind eyes"
JY = "a young Korean woman of twenty-five with a long black ponytail and a small backpack"

SCENES = [
    # 1 환생 수선집과 한아
    f"a small sunlit clothing repair workshop with plain white walls, folded fabrics and potted plants on wooden shelves, {HA} at a worktable",
    f"close-up of a Korean woman's hands sewing a colorful patch onto old denim jeans with needle and thread, soft window light",
    f"{HA} holding up a reworked vintage jacket and smiling, plain white wall behind, morning light",
    f"{HA} and {YU} laughing together over a pile of old clothes on a worktable, plain cream walls, warm daylight",
    f"close-up of neatly folded patched shirts and spools of thread in soft pastel colors on a wooden table",
    f"{HA} riding a plain bicycle along a tree-lined riverside path in spring, green leaves, bright day",
    f"{HA} watering small herb pots on a sunny rooftop garden, plain sky behind",
    # 2 11년 연인 경민
    f"{HA} and {KM} sitting on a riverside lawn, he looks away at the sky while she looks at him, bright afternoon, wide shot",
    f"{KM} with a big travel backpack walking away down a path, {HA} watching from behind, summer daylight",
    f"close-up of {HA} looking wistful by a sunny window, holding a mug, plain wall",
    # 3 캐나다 유성우와 운석
    f"a vast pine forest beside a calm lake in Canada at pale pre-dawn, sky softly lit lavender and pink, a single bright meteor streak, bright enough",
    f"a smoking small crater in a snowy pine forest clearing in bright daylight, glittering crystalline rock fragments",
    f"{HA} sitting on a sofa anxiously holding her phone against her chest, sunny living room with plain walls",
    # 4 낯설어진 경민
    f"{AL} standing at a doorway with a soft smile, sunlight behind him, {HA} looking at him puzzled",
    f"close-up of a man's bare forearm with smooth unmarked skin in soft light",
    f"a Korean home dining table with rice, soup and seasoned eggplant side dish, {AL} eating happily, {HA} staring surprised, bright kitchen",
    f"close-up of a wooden toothbrush with a perfect neat line of white toothpaste held out by a man's hand, soft bathroom light, plain tiles",
    f"{AL} gazing at {HA} attentively across a cafe table by a window, she reads a book, warm daylight, plain walls",
    f"close-up of a man's fingers holding thin black graphite pencil leads, curious and odd, soft light",
    f"close-up of an open palm holding a small brilliant cut diamond sparkling in sunlight",
    f"{HA} turning the sparkling diamond in her fingers with a shocked expression, sunny room",
    # 5 정체 — 광물의 별
    f"a man's silhouette with a faintly glowing faceted crystal visible inside his chest, soft blue light, sci-fi, bright room",
    "a serene alien planet made of pale crystal mountains and pastel mineral plains under a bright lilac sky, two small moons",
    "a giant crystalline telescope-like structure on a pastel mineral planet pointing at a tiny blue earth in a bright sky",
    "a luminous pastel nebula with soft pink and turquoise clouds and scattered stars, bright and dreamy",
    "planet earth seen from space glowing blue and white, soft sunlight on the horizon",
    f"{KM} floating weightless and joyful inside a softly glowing translucent alien capsule, stars outside, bright interior",
    f"{AL} holding {HA}'s hands and speaking earnestly in a sunlit room, her eyes wide",
    # 6 요원과 열성 팬
    "a stern Korean man in a dark suit and sunglasses standing in a sunny park under ginkgo trees, watching from afar",
    f"{JY} sitting on a grassy hill gazing up at a bright blue sky with a faint streak of a rocket trail, hopeful",
    "a plant-like humanoid alien with green vine hair and leaf patterns on pale skin, fingertips touching rich soil, bright greenhouse light",
    f"{YU} confronting {AL} with crossed arms in the workshop, {HA} between them, plain white walls, daylight",
    # 7 받아들이는 사랑
    f"{HA} and {AL} walking hand in hand along a riverside path with cherry blossoms, bright spring day",
    f"{HA} resting her head on {AL}'s shoulder on a park bench under green trees, sunlight",
    f"a simple garden wedding, {HA} in a plain white linen dress and {AL} in a light suit, few guests, flowers, bright day",
    f"a bright warm kitchen of a youth shelter, {HA} serving food to several Korean teenagers at a long wooden table, plain walls",
    # 8 엑스의 귀환과 소멸
    f"a pale exhausted thin Korean man with messy black hair and stubble standing at a door, hollow eyes, daylight",
    f"a thin weak Korean man with messy black hair lying in a bed beside a bright window, {HA} sitting quietly beside him",
    "a soft column of white light rising from a misty green field at dawn toward a small glowing spacecraft, bright pastel sky",
    f"{HA} and {AL} standing in a misty field watching the light fade into the sky, seen from behind, dawn",
    # 9 결말
    f"an elderly Korean woman with grey hair and a gentle smile holding hands with {AL}, sitting on a hill under a bright sky",
    "two figures standing side by side seen from behind on a grassy hill, both facing the same horizon, pastel sky, wide shot",
    f"close-up of two hands with fingers intertwined, one with a faint crystalline shimmer, soft sunlight",
    "a single small blue planet earth glowing among pastel stars and soft nebula clouds, bright, hopeful",
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

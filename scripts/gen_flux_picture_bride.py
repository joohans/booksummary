#!/usr/bin/env python3
"""「알로하, 나의 엄마들」(이금이) Flux 무드 이미지 배치 생성

1910년대 후반 김해 어진말(들판·강가·초가 마당) → 중매쟁이와 사진 한 장 → 세 친구 버들·홍주·송화의 출발
→ 이민선과 바다 → 하와이 도착과 사진과 다른 남편들 → 사탕수수 농장 노동 → 태완과의 서먹한 신혼
→ 세탁소 빨래 노동 → 독립운동 후원(지폐 금지 — 손에 쥔 작은 천 주머니로) → 태완의 중국행 이별
→ 다시 모인 세 친구·아이들 → 딸 펄과 세 엄마 → 바닷가의 알로하.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 조선 관아·현판·간판·교회 표지·신문·편지·책·지폐 금지 → 들판·맨벽 실내·클로즈업·바닷가.
인물마다 「Korean … black hair」 명시(서양인 방지). 35mm 사진풍 BASE. ★ 배경은 장면별로만(BASE 금지). 밤 장면 금지.

    .venv/bin/python scripts/gen_flux_picture_bride.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Picture_Bride_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still, warm natural daylight, bright enough to see clearly, not dark, "
        "soft warm palette of sunlit green, ocean blue, sand beige and white cotton, shallow depth of field, gentle film grain, "
        "early twentieth century, tender, resilient, hopeful mood, no signboards, no signs, no logos, no labels, no text, no letters, no numbers, no writing anywhere")

BU = "a slender Korean young woman of eighteen with black hair in a low braided bun, determined bright eyes, plain white cotton hanbok blouse and long skirt"
HO = "a pretty Korean young woman of eighteen with black hair neatly pinned, lively confident face, pale pink cotton hanbok"
SO = "a shy thin Korean young woman of eighteen with black hair in a simple braid, gentle sad eyes, faded light blue cotton hanbok"
TW = "a lean serious Korean man of twenty-six with short black hair, quiet distant eyes, plain white shirt and work trousers"
PE = "a cheerful Korean American girl of eight with black hair in two braids, plain white cotton dress"

SCENES = [
    # 1 어진말
    f"wide view of a quiet Korean countryside in the 1910s, green rice paddies, low thatched-roof farmhouses with earthen walls, soft hills, morning light",
    f"{BU} carrying a water jar on her head along a dirt path between rice paddies, morning sun",
    f"{BU} sitting on a wooden porch of a thatched farmhouse, looking wistfully toward the distant hills, close-up, plain earthen wall behind",
    f"close-up of a Korean young woman's hands holding a small old sepia photograph of a young man, the photograph shows only a blurred portrait with no writing, warm light",
    f"an elderly Korean matchmaker woman with grey hair in a bun and dark hanbok speaking eagerly to {BU} in a sunny farmhouse courtyard, plain earthen walls",
    f"a Korean mother in her forties in worn white hanbok holding the hands of her daughter {BU}, both tearful, in a sunlit courtyard",
    f"{BU}, {HO} and {SO} sitting together on a grassy riverbank, laughing and talking, willow trees, bright afternoon",
    f"{SO} standing alone at the edge of a field under a pine tree, villagers far away in the distance, soft light",
    f"{HO} looking at a small sepia photograph and smiling dreamily, close-up, sunny meadow behind",
    f"three young Korean women in white and pastel hanbok walking away along a long dirt road between fields, carrying cloth bundles, seen from behind, morning",
    # 2 바다
    f"three young Korean women in hanbok standing at the rail of an old steamship, looking at the wide open ocean, wind in their hair, bright day",
    f"vast blue Pacific ocean seen from the wooden deck of an old steamship, white wake, clear sky, no people",
    f"{BU} seasick but hopeful, sitting on a wooden deck with a cloth bundle, ocean behind, close-up",
    f"{SO} and {BU} sharing a small rice ball on the deck of an old steamship, ocean light",
    # 3 하와이 도착
    f"first sight of a lush green tropical island with volcanic mountains and palm trees from the sea, bright morning, no buildings",
    f"three young Korean women in hanbok standing on a sunny wooden dock with palm trees, looking around anxiously, cloth bundles at their feet",
    f"{HO} staring in shock at an older Korean man of about forty-five with grey stubble in a worn suit, on a sunny dock with palm trees",
    f"a scruffy lazy-looking Korean man in his forties with unkempt hair and a crumpled shirt, slouching against a palm tree, squinting, bright day",
    f"{TW} standing stiffly before {BU} under a palm tree, both awkward and silent, bright tropical light",
    f"close-up of {BU}'s face, disappointment and resolve mixing in her eyes, tropical green blurred behind",
    # 4 사탕수수 농장
    f"vast green sugarcane field in Hawaii under a bright sky, tall stalks swaying, mountains in the distance, no people",
    f"Korean women in white cotton work clothes and wide straw hats cutting tall sugarcane under the hot sun",
    f"{BU} in a wide straw hat wiping sweat from her forehead in a tall sugarcane field, close-up, sunlight through stalks",
    f"a small plain wooden plantation cottage with a tin roof surrounded by banana trees, bright afternoon, no signs",
    f"{BU} cooking rice in an iron pot over an outdoor fire beside a plain wooden cottage, banana leaves, warm light",
    f"{TW} sitting alone on the steps of a plain wooden cottage at dusk-like golden afternoon, looking away, {BU} watching from the doorway",
    # 5 세탁소·노동
    f"{BU}, {HO} and {SO} washing white sheets in large wooden tubs outdoors, white laundry hanging on lines behind them, bright sun",
    f"rows of white sheets and shirts drying on clotheslines in a sunny yard with palm trees, gentle breeze, no people",
    f"close-up of a Korean woman's reddened hands wringing out white cloth over a wooden tub, water drops sparkling in sunlight",
    f"{HO} laughing while ironing white shirts with an old iron on a plain wooden table, plain white wall, warm light",
    f"{SO} with a bruise on her cheek, sitting quietly on a wooden bench outdoors, {BU} gently holding her hand, soft light",
    # 6 독립운동·이별
    f"a group of Korean immigrant men and women in plain clothes gathered seriously in a plain wooden hall with bare white walls, listening intently, daylight from windows",
    f"close-up of a Korean woman's hands placing a small cloth pouch into a plain wooden box on a table, warm light, no writing",
    f"{TW} talking passionately to a few Korean men under a large banyan tree, serious faces, bright day",
    f"{TW} with a small travel bag saying goodbye to {BU} on a sunny wooden dock, she holds a baby wrapped in white cloth, steamship blurred behind",
    f"{BU} holding a baby and watching a steamship sail away on the bright blue ocean, seen from behind, palm trees",
    # 7 엄마들
    f"{BU}, {HO} and {SO} reunited, embracing and crying with joy in a sunny yard with white laundry lines",
    f"three Korean women in plain cotton dresses feeding several small children at a long plain wooden table outdoors under a mango tree, laughing",
    f"{SO} cradling a newborn baby, smiling softly, plain white wall, warm window light",
    f"{PE} running happily between rows of white laundry with three Korean women watching and smiling, bright sun",
    f"{PE} dancing barefoot on a sunny beach, arms raised, joyful, turquoise waves behind",
    f"{TW} older and limping with a wooden cane, walking slowly up a sunny path toward a plain wooden cottage, {BU} waiting at the door",
    f"three Korean women in their thirties sitting together on the sand at a golden sunny beach, shoulders touching, looking at the ocean, seen from behind",
    f"{PE} holding hands with {BU}, {HO} and {SO} on a sunny beach with palm trees, wide shot, warm golden light",
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

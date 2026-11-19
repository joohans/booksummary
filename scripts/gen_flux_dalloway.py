#!/usr/bin/env python3
"""「댈러웨이 부인」(버지니아 울프) Flux 무드 이미지 배치 생성

1923년 6월 런던의 하루 → 아침 꽃 사러 나서는 클라리사(꽃 클로즈업·공원·하늘) → 젊은 날의 시골집 버턴(정원·테라스)
→ 피터·샐리·리처드 회상 → 피터의 방문(응접실, 바느질하는 드레스) → 공원 벤치의 셉티머스와 레치아
→ 환각(나무·새·빛) → 의사의 진찰실(민무늬 벽) → 열린 창문 → 저녁 파티(촛불·샹들리에, 밝게) → 작은 방의 클라리사
→ 창밖 노부인 → 「For there she was」.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 상점 간판·버스·신문·시계 문자판(빅벤 근접)·
꽃집 간판은 글자가 붙으므로 쓰지 않는다. 빅벤은 먼 실루엣만. BASE 는 사진풍 「35mm period film still」.

    SEED_BASE=78000 .venv/bin/python scripts/gen_flux_dalloway.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Mrs_Dalloway_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still, 1920s English period film, natural daylight, "
        "bright enough to see clearly, not dark, light film grain, "
        "no logos, no text, no letters, no signs, no writing anywhere, no watermark, no signature")

CLARISSA = ("a slender elegant English woman in her early fifties with short silver-streaked fair hair, "
            "a delicate thoughtful face, wearing a pale lavender 1920s day dress and a small cloche hat")
YOUNG_CLARISSA = "a slender English girl of eighteen with long fair hair pinned up, wearing a white Edwardian summer dress"
PETER = "an English man in his early fifties with greying dark hair and a lean restless face, wearing a worn tweed suit"
SALLY = "a lively dark-haired English girl of eighteen with bright eyes, wearing a loose white summer dress"
RICHARD = "a solid kindly English gentleman in his fifties with neat grey hair and a moustache, wearing a dark three-piece suit"
SEPTIMUS = ("a thin pale English man around thirty with short brown hair and haunted hollow eyes, "
            "wearing a shabby brown suit and an overcoat")
REZIA = "a small dark-haired Italian woman in her twenties with a gentle anxious face, wearing a simple dark blue dress and a modest hat"

SCENES = [
    # 아침 — 꽃 사러
    f"{CLARISSA} stepping out of a white Georgian front door onto a quiet London street on a bright June morning, soft daylight",
    "close-up of fresh sweet peas, roses and delphiniums in buckets, morning light, shallow depth of field",
    f"close-up of {CLARISSA} smiling faintly while smelling a bunch of sweet peas, shallow depth of field, soft daylight",
    "a quiet elegant London street of white Georgian townhouses with iron railings on a bright June morning, no shops, soft daylight",
    "the distant silhouette of a gothic clock tower above trees and rooftops seen across a London park on a hazy summer morning, wide shot",
    f"{CLARISSA} walking along a tree-lined path in a green London park on a bright summer morning, wide shot",
    "close-up of sunlight through fresh green plane tree leaves, summer morning, bright",
    "a small aeroplane leaving a white trail of smoke high in a blue June sky above treetops, wide shot",
    # 버턴 — 젊은 날
    "a large old English country house with ivy walls and a stone terrace overlooking a summer garden, soft golden light",
    f"{YOUNG_CLARISSA} and {SALLY} laughing together on a stone terrace in a summer garden, soft golden light",
    f"{SALLY} picking a flower from a garden urn on a terrace at dusk, warm golden light",
    f"{YOUNG_CLARISSA} standing by a lake with a young dark-haired English man in a tweed jacket, tense quiet moment, soft daylight",
    "a still lake surrounded by trees beside an English country estate, soft afternoon light",
    f"close-up of {YOUNG_CLARISSA} looking thoughtfully down, shallow depth of field, soft golden light",
    # 리처드와 피터
    f"{RICHARD} standing in a quiet drawing room with a bouquet of red and white roses, soft daylight",
    f"{CLARISSA} sitting in a sunlit drawing room mending a green silk evening dress with needle and thread, soft daylight",
    "close-up of hands sewing a shimmering green silk dress with a needle, shallow depth of field, soft daylight",
    f"{PETER} sitting opposite {CLARISSA} in a pale sunlit drawing room, emotional conversation, soft daylight",
    f"close-up of {PETER} holding an open pocketknife, fidgeting, shallow depth of field, soft daylight",
    f"close-up of {PETER} with tears in his eyes, shallow depth of field, soft daylight",
    f"{PETER} walking alone through a London park on a summer day, wide shot, soft daylight",
    # 셉티머스와 레치아
    f"{SEPTIMUS} sitting on a park bench staring blankly at the trees, {REZIA} beside him looking worried, soft daylight",
    f"close-up of {SEPTIMUS} with wide haunted eyes staring at swaying trees, shallow depth of field, soft daylight",
    "close-up of sparrows on a branch against a bright summer sky, shallow depth of field",
    f"close-up of {REZIA} looking anxiously sideways, holding her hat, shallow depth of field, soft daylight",
    "close-up of trees swaying in the wind in a park with bright sunlight flickering through the leaves, dreamy",
    f"{SEPTIMUS} in a 1910s British army uniform without insignia standing in a misty muddy field, memory, soft hazy light",
    "a misty empty muddy battlefield with broken trees under a pale sky, soft hazy light",
    f"{REZIA} sitting by a window in a small plain room making a hat with ribbons and flowers, soft daylight",
    f"{SEPTIMUS} and {REZIA} laughing softly together in a small plain room while she sews a hat, warm daylight",
    # 의사
    "a stern grey-haired English doctor in a dark frock coat sitting behind a polished desk in a plain office with bare walls, soft daylight",
    f"{SEPTIMUS} sitting stiffly in a chair in a bare plain doctor's office, {REZIA} standing behind him, soft daylight",
    "an open sash window of a plain room with white curtains blowing in the summer wind, bright daylight",
    "a narrow iron railing below a tall window seen from above, empty, soft daylight",
    # 파티
    "an elegant 1920s London drawing room prepared for an evening party with flowers and candles, warm bright light",
    f"{CLARISSA} in a shimmering green silk evening gown greeting guests at the top of a staircase, warm bright light",
    "elegant 1920s guests in evening dress talking in a candlelit drawing room, warm bright light, soft focus",
    "close-up of champagne glasses and roses on a white tablecloth, warm candlelight, bright, shallow depth of field",
    f"close-up of {CLARISSA} in a green evening gown, her smile fading, listening, warm light, shallow depth of field",
    f"{CLARISSA} in a green evening gown standing alone in a small quiet room by a window at night, lamp light, bright enough to see",
    "through a window at night, an old lady in a lit room across the street preparing for bed, warm lamplight",
    f"{PETER} and an elegant dark-haired English woman in her fifties sitting on a sofa at a party, warm light",
    f"{CLARISSA} in a green evening gown appearing in a doorway at a party, glowing, warm bright light",
    "close-up of a rose petal falling on a polished floor, warm light, shallow depth of field",
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
            seed = int(os.environ.get("SEED_BASE", "78000")) + i * 100 + k * 7
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

#!/usr/bin/env python3
"""「광문자전」(박지원) Flux 무드 이미지 배치 생성

18세기 한양, 종로의 거지 두목 광문, 겨울밤, 거적, 다리 밑, 약방, 보증, 싸움 말리기, 기생 운심의 칼춤.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 관아·가게 정면은 현판 글씨가 붙는다(숙향전·마의 산 교훈). 건물은 초가·담장·기와 지붕 끝만, 실내는 맨 벽·클로즈업.
→ 약방은 「이름표 없는 나무 서랍」으로. 인물마다 Korean·hanbok 명시(메리골드 교훈: 안 쓰면 서양인).
→ 처음부터 밝은 낮빛(밝기 ≥60). 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_gwangmun.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-17 /health 로 9010 확인
OUT = Path("assets/images/The_Tale_of_Gwangmun_flux")   # 검수 후 옮긴다

BASE = ("luminous painterly Korean historical drama film still, 18th century Joseon dynasty Hanyang, bright soft daylight, "
        "warm earthy ochre, pale jade and soft white palette, bright enough to see clearly, not dark, "
        "extreme shallow depth of field, soft bokeh, gentle film grain, humane warm and humorous mood, "
        "no signboards, no calligraphy, no logos, no text, no letters, no numbers, no writing anywhere")

K = "Joseon dynasty Korean people with black hair in traditional hanbok"
SCENES = [
    # 연암과 청지기들
    f"a pale young Korean scholar of eighteen in white hanbok lying ill on a floor mat, listening to old servants telling stories by a soft lamp, {K}",
    f"old Korean servants in plain hanbok laughing while telling a story, close-up of wrinkled faces, warm light, {K}",
    # 종로의 거지 두목
    f"a ragged cheerful Korean beggar man with a big mouth and messy braided hair in torn hanbok, close-up portrait, warm daylight, {K}",
    f"a group of ragged Korean beggars gathered around their leader in a bright dusty alley between earthen walls, {K}",
    "close-up of a cracked wooden begging bowl on dusty ground, soft light",
    # 겨울밤 죽은 거지 · 쫓겨남
    "a snowy Joseon village of thatched roofs under soft pale winter light, quiet, no signs",
    f"a sick Korean beggar shivering under a straw mat in the snow, an old companion watching in worry, {K}",
    f"angry Korean beggars pointing and driving one man away in the snow, motion, {K}",
    f"a ragged Korean man hiding in the corner of a tiled courtyard caught by a surprised householder with a lantern, {K}",
    # 거적 · 다리 밑 · 장사
    "close-up of a woven straw mat rolled on snowy ground, soft light",
    "an old stone bridge over a frozen stream in Joseon Hanyang, pale winter daylight, no text",
    f"a ragged Korean man carefully wrapping a body in a straw mat under a stone bridge, solemn, soft light, {K}",
    f"a lone Korean man carrying a straw-wrapped bundle on his back walking out through snowy fields at dawn, seen from behind, {K}",
    "a small fresh grave mound in a snowy field with a single pine tree, dawn light",
    f"a Korean man in a gat hat secretly watching from behind a stone wall, curious, {K}",
    # 약방
    "a bright Joseon herbal pharmacy interior with rows of plain unlabeled wooden drawers and hanging dried herbs, no labels, no writing",
    "close-up of dried medicinal herbs, roots and a brass scale on a wooden table, soft light",
    f"a humble Korean helper grinding herbs with a mortar in a bright pharmacy, quiet face, {K}",
    "close-up of old Korean brass coins with square holes scattered on a wooden floor, soft light, no writing",
    f"a Korean pharmacy owner in hanbok looking with suspicion at a quiet humble helper, tense, {K}",
    f"a Korean pharmacy owner bowing deeply in apology to a humble ragged helper, warm light, {K}",
    # 장안의 이름
    f"Korean townspeople in hanbok chatting and smiling at a bright busy market of straw-roofed stalls, blurred background, no signs, {K}",
    f"two Korean men shaking hands over a pouch of coins while a ragged man vouches for them with a grin, {K}",
    # 싸움 말리기 · 익살
    f"two Korean men in hanbok fighting on a dusty road while a ragged man takes off his coat and mimes like a clown between them, {K}",
    f"a ragged Korean man drawing a line on the ground with a stick, making a funny face, crowd laughing, {K}",
    f"Korean children in hanbok laughing and teasing each other in a sunny alley, {K}",
    # 장가 · 집
    f"a ragged Korean man of forty with long braided hair laughing and shaking his head, close-up, warm light, {K}",
    "an empty plot of land with a broken earthen wall and wild grass under a bright sky, peaceful",
    # 운심의 칼춤
    f"a beautiful Korean gisaeng in elegant hanbok sitting still and refusing to dance at a banquet, proud expression, {K}",
    f"a ragged Korean man humming and clowning at the doorway of an elegant banquet room, guests startled, {K}",
    f"a Korean gisaeng performing a graceful sword dance with two swords, flowing silk sleeves, motion blur, warm lantern light, {K}",
    f"Korean noblemen in hanbok laughing and applauding at a lantern-lit banquet, {K}",
    # 속편 · 결말
    f"a large crowd of Korean townspeople in hanbok gathering on a road to see a released man, joyful, {K}",
    f"a ragged Korean man smiling gently, walking away down a long country road into soft morning light, seen from behind, {K}",
    "a winding country road disappearing into misty hills at sunrise, bright, peaceful",
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
            seed = 99000 + i * 100 + k * 7
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

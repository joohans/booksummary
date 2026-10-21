#!/usr/bin/env python3
"""「초정리 편지」(배유안) Flux 무드 이미지 배치 생성

초정 산골(나무하기·약수·토끼 눈 할아버지) → 흙바닥 훈장(오복·난이) → 누이와 이별·편지
→ 석수 일(정·망치·연꽃 확) → 한양 절 공사·깨진 확 → 임금의 정체 → 가족 재회.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 조선 실내·거리는 현판·족자가 붙는다(광문자전 10/17) → 산·들판·초가·맨벽·클로즈업만.
→ 이 책은 「글자」가 주제지만 화면에 글씨를 그리지 않는다 — 편지는 접힌 뒷면, 흙바닥은 막대 끝만.
→ 인물마다 Korean 명시. 처음부터 밝은 톤. 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_chojeong.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-19 /health 로 9010 확인
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Chojeong_Letters_flux"))   # 검수 후 옮긴다

BASE = ("warm painterly Korean historical film still, early Joseon dynasty, outdoors in rural mountain nature, "
        "pine forests, rocky streams, open fields and soft mountains, bright soft natural daylight, "
        "warm earthy palette of ochre, pine green and pale sky blue, bright enough to see clearly, not dark, "
        "extreme shallow depth of field, soft bokeh, gentle film grain, tender nostalgic mood, "
        "no buildings or walls unless described, no signboards, no plaques, no calligraphy, no hanging scrolls, no banners, no seal, "
        "no text, no letters, no characters, no writing anywhere")
# ⚠️ 10/21 1차는 BASE 에 「plain blank walls」를 넣었다가 산길·약수·들판까지 전부 담장 골목이 됐고
#    현판·족자가 70장 중 약 25장에 붙었다 → 자연을 BASE 에 박고 건물은 장면에서만 부른다

K = "Korean people with black hair in plain undyed Joseon hanbok"
SCENES = [
    # 초정 산골 — 나무하기·약수·할아버지
    f"a twelve-year-old Korean boy carrying a load of firewood on a wooden A-frame on his back, walking up a misty pine forest path, seen from behind, {K}",
    f"a gentle elderly Korean nobleman with reddened tired eyes in a plain white robe and black horsehair hat sitting on a mossy rock under a pine tree, kind smile, {K}",
    "clear mineral spring water bubbling up between mossy rocks in a forest, a wooden gourd dipper resting nearby, close-up, sunlight",
    f"a Korean boy carrying a gourd bottle of spring water across an autumn field, mountains behind, {K}",
    "a small thatched-roof cottage in a quiet mountain valley, thin smoke from the chimney, autumn trees, morning light",
    f"a Korean boy and his older sister sitting on a wooden porch of a thatched cottage, laughing together, warm evening light, {K}",
    f"an elderly man handing a small cloth bag of rice to a barefoot Korean boy in a forest clearing, close-up of hands, {K}",
    # 흙바닥 훈장
    f"village children crouching around a Korean boy holding a stick over the bare dirt ground, curious faces, close-up of faces, {K}",
    "close-up of a child's hand holding a thin stick touching smooth bare dirt ground, soft daylight",
    f"a young Korean servant man resting beside a wooden water mill wheel by a stream, smiling, {K}",
    f"a Korean girl sorting dried medicinal herbs in round straw baskets, close-up of hands and herbs, {K}",
    # 이별과 편지
    f"an injured Korean stonemason father lying on a straw mat with a bandaged leg against a plain earthen wall, worried, {K}",
    f"a teenage Korean girl with a cloth bundle walking away down a long dirt road between fields, seen from behind, {K}",
    f"a Korean boy standing alone on a grassy hill at sunset watching an empty road, lonely, {K}",
    "close-up of two hands holding a folded sheet of plain paper, the paper seen only from the blank back, soft light",
    f"a Korean boy sitting under a big tree holding a folded paper to his chest, eyes closed, moved, {K}",
    # 석수
    "close-up of an iron chisel and wooden mallet resting on a rough granite block, stone dust, sunlight",
    f"a Korean boy carving a granite stone with a chisel and mallet, stone dust flying, focused face, close-up, {K}",
    f"Korean stonemasons cutting large granite blocks at a mountain quarry, dust in the sunlight, {K}",
    f"a group of Korean stonemasons walking along a country road with tools on their backs toward distant mountains, {K}",
    # 한양 절 공사
    f"a large wooden building under construction with timber scaffolding and stone foundations, workers far away, no plaques, bright sky, {K}",
    "close-up of a beautifully carved granite basin shaped like a lotus flower, petals in stone, soft light",
    "a carved granite lotus basin cracked and broken in two on the dirt ground, stone fragments, melancholy light",
    f"an older Korean stonemason with a stern jealous face, close-up portrait, dusty light, {K}",
    f"a Korean boy kneeling with his head bowed on a stone-paved yard, plain wall behind, {K}",
    # 임금
    f"an elderly Korean king in a plain deep red silk robe with no emblem, kind reddened eyes, looking down warmly, close-up, {K}",
    f"an elderly Korean man rubbing his tired eyes by candlelight at night, blank sheets of paper on a low table, plain wall, {K}",
    "a mountain valley with a misty mineral spring and a small open wooden pavilion, early morning, no plaques",
    f"a Korean boy and an elderly man walking side by side on a forest path, warm afternoon light, seen from behind, {K}",
    # 퍼지는 글자
    f"Korean stonemasons gathered at dusk around a boy pointing at the dirt ground with a stick, smiling, {K}",
    f"a Korean girl applying herbal paste to an injured worker's arm, close-up of hands, {K}",
    # 재회·결말
    f"a Korean brother and sister embracing in tears in front of a thatched cottage, spring blossoms, {K}",
    f"a Korean family of father, son and daughter eating together at a small low table under the eaves of a thatched house, warm light, {K}",
    "golden autumn rice fields in a Korean valley with soft mountains behind, bright sky",
    "pink azaleas blooming on a Korean mountainside at sunrise, hopeful, luminous",
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

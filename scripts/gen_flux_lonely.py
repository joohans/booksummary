#!/usr/bin/env python3
"""「너무 시끄러운 고독」(보후밀 흐라발) Flux 무드 이미지 배치 생성

1970년대 프라하 — 지하실 폐지 압축공 한탸, 뚜껑문으로 쏟아지는 폐지, 낡은 압축기와 꾸러미, 맥주와 독서,
명화 복제화를 두른 꾸러미, 집 안에 쌓인 두 톤의 책 → 젊은 날의 기억(시골 처녀·집시 소녀) → 교외의 거대한 압축 공장
→ 장갑 낀 젊은 노동자들 → 텅 빈 지하실.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 책은 무지 천 장정·흐린 책장·먼 거리로만, 간판·신문·포스터 금지.
★ 35mm film still BASE. 배경은 장면별로만. 밤 장면 금지(밝기 ≥60, 지하실은 천장 뚜껑문 햇빛). 인물은 「Czech … 」 명시.

    SEED_BASE=48000 .venv/bin/python scripts/gen_flux_lonely.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Too_Loud_a_Solitude_flux"))   # 검수 후 옮긴다

BASE = ("35mm film still, soft natural daylight, bright enough to see clearly, not dark, "
        "warm palette of paper beige, faded ochre, brick red and dusty green, shallow depth of field, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no numbers, no writing anywhere, no watermark, no signature")

HANTA = "a stocky Czech man in his sixties with thinning grey hair and a stubbly round face, in a stained grey work apron over a shirt, 1970s"
YOUNG = "a young Czech man in his twenties with wavy brown hair, in a plain white shirt, 1930s"
GIRL = "a young Czech country girl with braided blonde hair and a ribbon, in a plain linen dress, 1930s"
GYPSY = "a slender young Romani woman with long black hair, in a plain simple dress, 1940s"
WORKERS = "young Czech workers in clean orange overalls and thick work gloves, 1970s"
BOOK = "old books with plain unmarked cloth covers, pages blurred out of focus"

SCENES = [
    # 프라하와 지하실
    "a wide view of old Prague red tiled rooftops and church spires on a hazy sunny morning, 1970s",
    "a quiet cobblestone courtyard with a worn wooden hatch door in the ground, soft daylight, 1970s",
    "a mountain of crumpled waste paper pouring down through a square hatch in a cellar ceiling, a shaft of sunlight",
    f"{HANTA} standing knee-deep in heaps of waste paper in a cellar lit by a ceiling hatch, sunbeam",
    "an old green-painted hydraulic baling press with a big iron lever in a brick cellar, daylight from above",
    f"{HANTA} pulling the iron lever of an old green baling press, paper squeezing out, warm light",
    "neat compressed bales of waste paper tied with wire stacked against a whitewashed brick wall, soft light",
    f"close-up of {HANTA}'s rough hands lifting {BOOK} out of a heap of waste paper",
    f"{HANTA} sitting on a paper bale reading an open book, a large mug of beer beside him, sunbeam, pages blurred",
    "a large glass mug of golden beer on a wooden crate beside crumpled paper, sunbeam, close-up",
    f"close-up of {HANTA}'s face lit by a sunbeam, eyes closed, a peaceful smile",
    "a grey mouse peeking out of a heap of crumpled paper, sunbeam, close-up",
    f"{HANTA} placing an open book in the center of a half-formed paper bale, careful and tender",
    "a paper bale wrapped in a reproduction of a golden wheat field painting, impressionist style, close-up",
    "a paper bale wrapped in a reproduction of a colorful tropical painting of flowers, close-up",
    "a row of finished paper bales each wrapped in different colorful painting reproductions, in a brick cellar",
    f"{HANTA} pushing a handcart of paper bales across a sunny cobblestone courtyard",
    # 집
    f"{HANTA} carrying a bundle of {BOOK} up a narrow wooden staircase, daylight",
    "a small old apartment room crammed floor to ceiling with stacks of old books with plain cloth covers, soft window light",
    "a narrow bed beneath a sagging wooden shelf overloaded with heavy old books with plain covers, morning light",
    f"{HANTA} lying in bed looking up anxiously at a sagging shelf of books above him, morning light",
    "a small bathroom piled with stacks of old books with plain covers, soft window light",
    f"{HANTA} sitting at a small kitchen table by a sunny window, a beer mug, an open book, pages blurred, content",
    # 젊은 날의 기억
    "a sunny green Bohemian countryside meadow with a small village and a dance pavilion, 1930s",
    f"{YOUNG} dancing with {GIRL} at a sunny village dance in a meadow, ribbons flying",
    f"close-up of {GIRL} laughing in a sunny meadow, ribbons in her braids",
    f"{GIRL} flying a kite on a windy green hill, laughing, 1930s",
    f"{YOUNG} and {GYPSY} sitting by a small stove in a plain wooden hut, warm daylight, quiet",
    f"{GYPSY} smiling shyly, standing in a sunny doorway of a wooden hut, close-up",
    f"{GYPSY} feeding a small wood stove, soft daylight through the window",
    "an empty wooden hut doorway with a lone kite lying in the grass, overcast daylight, melancholy",
    f"{HANTA} standing alone in a grassy field looking at the horizon, overcast, remembering",
    # 상상과 사색
    "a dreamy soft-focus image of an ancient Chinese sage with a long white beard in plain robes, misty light",
    "a dreamy soft-focus image of a young bearded man in plain white robes on a hill, gentle light",
    f"{HANTA} sitting quietly on a bench by the Vltava river, sunny, a beer mug beside him",
    # 새 압축 공장
    "a vast modern factory hall with an enormous hydraulic paper press and conveyor belts, bright daylight from skylights, 1970s",
    f"{WORKERS} feeding piles of waste paper onto a conveyor belt in a bright factory hall",
    "close-up of thick work gloves tossing crumpled paper onto a moving conveyor belt",
    f"{HANTA} standing small and stunned in the doorway of a huge bright factory hall, seen from behind",
    f"{WORKERS} drinking milk from bottles and laughing during a break in a bright factory yard",
    # 마지막
    f"{HANTA} sitting alone on a paper bale in his cellar, head bowed, sunbeam from the hatch",
    f"{HANTA} resting his hand on the old green baling press, eyes closed, soft sunbeam",
    "an empty brick cellar with a silent old green baling press and scattered paper, a single shaft of sunlight",
    "loose sheets of blank paper drifting down through a shaft of sunlight, close-up, dreamy",
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
            seed = int(os.environ.get("SEED_BASE", "48000")) + i * 100 + k * 7
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

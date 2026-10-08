#!/usr/bin/env python3
"""「카인의 후예」 Flux 무드 이미지 배치 생성 (스톡 보충용)

1946년 평안남도 순안 양짓골, 북한 토지개혁 시기의 농촌 → 장면을 Flux 로 채운다.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 핵심 소재가 「송덕비」「농민대회 현수막·구호」「야학 칠판」이지만 비석 글자·현수막·칠판은 장면에서 아예 뺀다.
   쓰러진 비석은 「글자 없는 뒷면」으로만, 농민대회는 군중의 뒷모습과 들판으로만 그린다.
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).
"""
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

FLUX = "http://192.168.0.150:9010/generate"   # 포트는 /health 로 확인(2026-10-08 9010 정상)
OUT = Path("assets/images/The_Descendants_of_Cain_flux")   # 스톡 AI 검증이 Flux 까지 깎지 않도록 따로 받아 검수 후 옮긴다

BASE = ("lyrical painterly film still, a farming village in Pyongan province northern Korea in the winter of 1946, "
        "thatched and tiled roofs, bare hills, cold blue-grey and warm lamplight palette turning to soft spring green, film grain, "
        "tense yet tender mood, no text, no signboards, no banners, no slogans, no flags, no inscriptions, no letters, no writing")

SCENES = [
    # 양짓골 · 훈
    "a quiet Korean farming village of thatched roofs under light snow at dusk, smoke from chimneys, bare hills behind",
    "a large tiled-roof landlord house with a stone wall and gate on a snowy morning, set apart from small thatched houses",
    "a thoughtful young Korean man in his late twenties in a dark 1940s overcoat and round glasses standing alone in a frozen field",
    "a lamplit room at night where poor village children in padded hanbok sit on the floor listening to a young man, no blackboard",
    # 오작녀
    "a gentle young Korean woman in a plain white hanbok and dark skirt quietly preparing a meal tray in a dim kitchen with an earthen stove",
    "a young woman in hanbok mending clothes by an oil lamp while a young man reads at a low desk in the next room, paper door half open",
    "a young woman in hanbok standing at a snowy gate at night holding a lantern, waiting, worried face",
    # 도섭 영감 · 토지개혁
    "a stocky old Korean farmer in his sixties with a grey beard and a fur hat, eyes hardening, holding an axe in a snowy yard",
    "a crowd of Korean villagers in padded winter clothes gathered in a snowy field seen from behind, a man shouting from a cart, no banners",
    "an old stone monument toppled over in the snow, seen from its plain uncarved back side, an axe lying nearby",
    "men in 1940s caps measuring a frozen field with ropes and stakes, a landlord house in the background",
    "a small boy peeking from behind a haystack watching a house at night, the light of a window",
    # 수난
    "a looted room in a traditional house, chests opened, scattered cloth, cold light through torn paper windows",
    "a dark village lane at night, a figure running with a sickle, a dog barking, moonlight on snow",
    "a fierce young man in his twenties clenching his fists in a dark barn, burning eyes",
    "a young man sitting alone on a cold veranda at night staring at the snow, resigned",
    # 오작녀의 거짓말
    "a young woman in hanbok standing between a group of angry villagers and a young man in a courtyard, chin raised, protecting him",
    # 산등성이
    "a lonely mountain ridge path at dusk in early spring, two small figures, melting snow, dramatic sky",
    "a young man gripping a knife hidden in his sleeve walking behind an old farmer up a hillside at dusk, tense",
    "two men struggling on a hillside at dusk, a third young man running up to pull them apart",
    "a sturdy young farmer in work clothes standing on a ridge at sunset, speaking firmly to a fallen young man",
    # 봄 · 떠남
    "a young man running down a hillside across a thawing field toward a small thatched house at dawn",
    "a young man and a young woman in hanbok holding each other's hands in a doorway at dawn, tearful, bundles packed",
    "two small figures walking south along a long road across a spring valley at sunrise, mist, hope",
    "early spring in a Korean valley, plum blossoms on a bare branch, melting snow on the hills, soft light",
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
            seed = 38000 + i * 100 + k * 7
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

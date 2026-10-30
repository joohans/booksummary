#!/usr/bin/env python3
"""「천 개의 찬란한 태양」(할레드 호세이니) Flux 무드 이미지 배치 생성

헤라트 오두막의 마리암과 엄마 나나 → 15살 생일, 아버지 잘릴의 외면·나나의 죽음 → 카불의 구두장이 라시드와 결혼·유산·폭력
→ 라일라·아버지 바비·소년 타리크 → 내전 로켓 → 라시드의 두 번째 아내 → 아지자 → 두 여자의 연대 → 탈레반·도주 실패
→ 마리암의 선택 → 파키스탄 머리 → 카불 귀환·고아원 → 「천 개의 찬란한 태양」.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 시장·가게·벽 글씨(페르시아 문자)·현판·코란 펼침면·신문 금지 → 들판·맨벽 실내·클로즈업.
인물마다 「Afghan … black hair」 명시. ⚠️ 폭력·처형 장면은 직접 그리지 않는다. 35mm 사진풍 BASE. ★ 배경은 장면별로만(BASE 금지). 밤 장면 금지.

    .venv/bin/python scripts/gen_flux_suns.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/A_Thousand_Splendid_Suns_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still, warm natural daylight, bright enough to see clearly, not dark, "
        "soft warm palette of sunlit beige, faded green, sky blue and warm grey, shallow depth of field, gentle film grain, "
        "quiet, tender, melancholic but hopeful mood, no screens, no signboards, no signs, no logos, no labels, no text, no letters, no numbers, no writing anywhere")

MA = "an Afghan girl of fifteen with long black hair under a loose plain headscarf, plain cotton dress"
MW = "an Afghan woman in her thirties with black hair under a plain dark headscarf, tired gentle eyes, plain dress"
LA = "an Afghan girl of fourteen with wavy black hair and bright eyes, plain blouse"
RA = "a heavy stern Afghan man in his fifties with a thick black beard, plain shirt and vest"
TA = "an Afghan teenage boy with short black hair and a kind face, plain shirt"
SCENES = [
    # 헤라트 오두막
    "a small mud-brick hut alone in a grassy clearing near a stream with willow trees, hills of Herat behind, bright spring daylight",
    "a clear stream running between willow trees and wild grass in the Afghan countryside, bright sunlight",
    f"{MA} sitting by a stream under willow trees, gazing toward a distant city, soft morning light",
    "an Afghan woman with grey-streaked black hair under a plain headscarf kneading dough inside a simple mud-walled hut, plain walls, warm window light",
    "close-up of a plain clay teapot and small glass cups on a woven mat inside a hut, soft light",
    f"{MA} waiting at the edge of a dusty path, watching the road, golden afternoon light",
    # 아버지의 외면
    "a high plain stone garden wall with a closed wooden gate, a girl sitting on the ground beside it, early morning grey light, no writing",
    "an empty dusty country road under a pale dawn sky, a lone car far away",
    "a wooden stool knocked over under a bare willow tree, empty, grey overcast light",
    # 결혼·카불
    f"{MA} in a plain green dress sitting stiffly beside {RA}, looking down, plain room, soft light",
    "a wide view of Kabul city spread across a dusty valley with brown mountains behind, hazy bright daylight, seen from a hill",
    f"close-up of the hands of {MW} washing rice in a metal bowl in a plain courtyard, daylight",
    "a small plain courtyard with a well, a plum tree and mud-brick walls, bright daylight",
    f"{MW} sitting alone on a floor cushion in a plain room, staring at the window, quiet sadness, soft light",
    "a pair of worn men's leather shoes on a plain wooden workbench with shoemaker's tools, close-up, warm light",
    f"close-up of {MW} looking out through a window lattice, tear in her eye, soft light",
    # 라일라
    f"{LA} reading a book on a rooftop in Kabul, mountains behind, bright afternoon light, book pages blank",
    "a gentle bespectacled Afghan man in his forties with a short beard reading poetry to his daughter in a plain room, warm light, pages blank",
    f"{LA} and {TA} laughing and walking along a dusty Kabul hillside path, bright daylight",
    f"{TA} sitting on a low wall with a colorful kite, smiling, blue sky",
    f"{LA} and {TA} sitting together on a hill overlooking Kabul at golden hour, seen from behind",
    # 내전
    "grey smoke rising over distant rooftops of Kabul, brown mountains, hazy daylight, far away",
    "a ruined mud-brick house with a collapsed wall and dust in the air, bright harsh daylight, no people",
    f"{LA} with a bandaged forehead lying on a floor mattress in a plain room, eyes closed, soft light",
    # 두 번째 아내
    f"{MW} watching coldly from a doorway as {LA} sits on a cushion, plain room, tense mood, soft daylight",
    f"{LA} in a plain blue dress cooking at a simple clay stove in a plain courtyard, daylight",
    "close-up of a tiny Afghan baby girl with black hair wrapped in a plain cloth blanket, soft warm light",
    f"{MW} smiling for the first time while holding a little Afghan girl of two on her lap, plain room, warm light",
    f"{MW} and {LA} drinking tea together on a rooftop in warm golden late afternoon light",
    f"{MW} braiding the black hair of {LA} in a plain sunlit room, tender mood",
    # 탈레반·도주
    "two Afghan women in pale blue burqas holding the hand of a little girl, walking through a dusty empty street, bright daylight, no signs",
    "a dusty bus station yard with an old bus, women in pale blue burqas waiting, far away, bright daylight, no signs",
    f"close-up of the hands of {MW} and {LA} clasped together tightly, soft light",
    "a dry cracked field under a hazy pale sky during drought, a single bare tree",
    "a little Afghan girl with black hair in a plain dress holding a woman's hand at a plain wooden door, sad goodbye, soft daylight",
    # 마리암의 선택
    f"{MW} standing alone in a plain courtyard at dawn, calm determined face, soft pale light",
    f"{MW} sitting peacefully by a small window with a beam of morning light, eyes closed, serene",
    "a single white flower growing out of a dry stone wall, close-up, soft morning light",
    # 머리·귀환
    "green pine-forested mountains of Murree in Pakistan under a bright clear sky, hotel roofs far away",
    f"{LA} as a young woman with wavy black hair and a light headscarf, holding hands with two children on a green hillside, bright",
    "the ruins of a small mud-brick hut among wild grass and willow trees beside a stream, quiet, golden afternoon light",
    "close-up of an old wooden box holding a folded letter and a small cloth bag, soft warm light, no writing visible",
    f"{LA} as a young woman teaching smiling Afghan children in a bright plain classroom with a blank chalkboard, daylight",
    "a wide view of Kabul at sunrise with countless glowing rooftops and mountains behind, golden hopeful light",
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

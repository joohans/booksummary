#!/usr/bin/env python3
"""「순례 주택」(유은실) Flux 무드 이미지 배치 생성

중3 수림 · 402호 건물주 순례 씨(75세, 평생 세신사) · 외할아버지와 줄자 → 고급 아파트에 사는 철없는 부모와 언니
→ 외할아버지 사망·빚 → 순례 주택(4층 빌라)으로 이사 → 옥상 공용 공간·이웃(새벽 배송·청소)
→ 가족의 민낯과 성장 → 「관광객은 요구하고, 순례자는 감사한다」.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 아파트 외벽 동 번호·브랜드, 목욕탕 간판, 택배 상자 송장 금지.
인물마다 「Korean … black hair」 명시. 35mm 사진풍 BASE. ★ 배경은 장면별로만(BASE 금지). 밤 장면 금지.

    .venv/bin/python scripts/gen_flux_sunrye.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Sunrye_House_flux"))   # 검수 후 옮긴다

BASE = ("35mm contemporary film still, warm natural daylight, bright enough to see clearly, not dark, "
        "soft warm palette of sunlit beige, faded green, sky blue and warm grey, shallow depth of field, gentle film grain, "
        "warm, gently humorous everyday mood, no screens, no signboards, no signs, no logos, no labels, no text, no letters, no numbers, no writing anywhere")

SL = "a fifteen-year-old Korean girl with a black ponytail and a calm clever face, wearing a plain navy hoodie"
SR = "a small energetic Korean grandmother in her seventies with short permed grey hair and a bright wrinkled smile, wearing a plain floral blouse"
MOM = "a Korean woman in her mid forties with neat shoulder-length black hair and stylish plain clothes"
DAD = "a Korean man in his late forties with black hair and glasses, wearing a plain sweater, looking helpless"
SIS = "a seventeen-year-old Korean girl with long straight black hair, wearing a plain school uniform"
SCENES = [
    # 순례 주택
    "a modest four-story red brick villa building on a quiet Korean residential street, potted plants by the entrance, bright summer daylight, no signs",
    "a sunny rooftop of a small brick building with potted vegetables in styrofoam boxes, a wooden bench and a small shared fridge, bright sky",
    "laundry drying on a line on a sunny rooftop, rooftops of low brick houses behind, blue sky",
    # 순례 씨
    f"{SR} sitting on a rooftop bench peeling sweet potatoes, laughing, bright daylight",
    f"close-up of the strong wrinkled hands of {SR} holding a warm roasted sweet potato, soft daylight",
    f"{SR} walking briskly with a cloth shopping bag down a quiet alley of low houses, morning light",
    "close-up of a folded white scrub towel and a wooden bath stool in a bright tiled bathhouse, steam, plain white tiles",
    f"{SR} watering potted plants on a rooftop at golden afternoon light",
    # 어린 수림·외할아버지
    "a small Korean girl of six with black bob hair sitting on a grandmother's lap on a sunny wooden floor, plain wall, warm light",
    "a gentle Korean grandfather in his seventies with white hair measuring a wooden shelf with an old metal tape measure, warm daylight, plain wall",
    "close-up of an old worn metal tape measure on a wooden table, soft window light",
    f"{SL} sitting with {SR} on a rooftop bench at golden afternoon light, talking, seen from the side",
    # 고급 아파트의 가족
    "a spacious modern luxury apartment living room with a white sofa and large windows, sunlight, minimalist, no screens",
    f"{MOM} sipping coffee by a large window in a luxurious apartment, looking down with a slightly snobbish face, bright daylight",
    f"{DAD} lying on a white leather sofa doing nothing, comic mood, bright modern living room",
    f"{SIS} looking puzzled at a pot of water on a modern stove, holding a packet of instant noodles with no label, comic mood",
    f"{SL} at a dining table watching her parents with a skeptical look, modern bright kitchen, plain wall",
    # 몰락
    "a black mourning ribbon and white chrysanthemums on a simple table, soft grey daylight",
    f"{MOM} crying on a sofa while {DAD} sits beside her holding his head, cardboard moving boxes around, daylight",
    "plain unmarked cardboard moving boxes stacked in an empty modern apartment, afternoon light",
    f"close-up of {SL} counting a few banknotes and coins on a table, serious face, soft daylight",
    # 이사
    "a small moving truck parked in a narrow residential alley of low brick houses, plain boxes, bright daylight, no text on truck",
    f"{MOM} standing in a narrow brick-walled stairwell holding a box, looking dismayed, daylight",
    "a tiny plain room with a single small window, a few boxes and folded blankets on the floor, soft daylight",
    f"{SL}, {MOM}, {DAD} and {SIS} squeezed together sleeping on floor mattresses in one tiny room, morning light, comic mood",
    # 이웃들
    "a tired but cheerful Korean man in his thirties with black hair carrying plain delivery boxes at dawn on an empty residential street, pale blue light",
    "a Korean woman in her fifties with black hair tied back, wearing rubber gloves, mopping a stairwell floor and smiling, daylight",
    "neighbors of different ages sharing food on a sunny rooftop at a long plastic table, laughing, Korean people with black hair",
    f"{MOM} arguing with an older Korean neighbor woman in a stairwell, comic mood, daylight",
    f"{DAD} awkwardly carrying a heavy bag of rice up a stairwell, sweating, comic mood, daylight",
    # 변화
    f"{SR} handing a warm sweet potato to {SL} on the rooftop, soft afternoon light",
    f"{SIS} carefully cooking instant noodles in a small pot on a portable gas stove on a rooftop, proud face",
    f"{MOM} wearing rubber gloves and scrubbing a floor for the first time, determined face, plain wall, daylight",
    f"{DAD} working at a small part-time job stacking plain boxes in a warehouse, sweating, bright light",
    f"{SL} reading a small poetry book with blank pages on the rooftop, wind in her hair, golden light",
    # 순례자
    "a narrow quiet alley in an old Korean neighborhood with potted flowers and sunlight, nobody, no signs",
    f"{SR} and {SL} walking side by side down a sunlit residential alley, seen from behind",
    "a pair of worn walking shoes on a rooftop in morning sunlight, close-up",
    "a wide view of low Korean rooftops under a bright morning sky with soft clouds, hopeful",
    f"{SL}, {MOM}, {DAD} and {SIS} sitting together with {SR} on a sunny rooftop, eating together, warm smiles, seen from a distance",
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

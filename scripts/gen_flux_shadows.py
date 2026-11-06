#!/usr/bin/env python3
"""「백의 그림자」(황정은) Flux 무드 이미지 배치 생성

숲에서 길을 잃은 은교와 무재, 일어서는 그림자 → 40년 된 낡은 전자상가(가~마동)의 복도·계단·작은 가게·수리실
→ 전구·부품·인두 클로즈업 → 상가 사람들(난로 가게, 기러기아빠, 남편 잃은 여자)과 그들의 그림자 → 정전 → 철거
→ 섬, 어둠 속 두 사람의 손.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 상가 간판·가격표·부품 상자 라벨·전광판·현판 금지,
⚠️ 「현대 한국+가게」는 글자 지옥(10/14 80장 중 67장 폐기) → 한국 설정어는 인물에만, 가게는 얕은 심도 클로즈업·민무늬 벽.
그림자 장면은 밝은 낮(벽에 드리운 그림자)으로 — 밤 금지. 35mm film still BASE. 인물마다 「Korean … black hair」.

    SEED_BASE=64000 .venv/bin/python scripts/gen_flux_shadows.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/One_Hundred_Shadows_flux"))   # 검수 후 옮긴다

BASE = ("35mm film still, quiet melancholy magical realism, soft natural daylight, bright enough to see clearly, not dark, "
        "muted palette of faded cream, dusty teal, pale grey concrete and warm tungsten amber, shallow depth of field, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no numbers, no signs, no labels, no writing anywhere, no watermark, no signature")

EUNGYO = "a quiet Korean woman in her late twenties with shoulder-length black hair, in a plain grey work jacket"
MUJAE = "a gentle thin Korean man in his late twenties with short black hair, in a plain navy sweater"
BOTH = f"{EUNGYO} and {MUJAE}"
OLDMAN = "a kind old Korean man in his seventies with grey hair, in a plain brown cardigan"
STOVE = "a worn-out Korean man in his fifties with greying black hair, in a plain padded vest"
FATHER = "a lonely Korean man in his forties with black hair, in a plain beige shirt"
WIDOW = "a tired Korean woman in her forties with black hair tied back, in a plain dark cardigan"

SCENES = [
    # 숲
    "a hazy green forest path in early autumn, tall thin trees, soft diffused daylight, quiet and slightly eerie",
    f"{BOTH} walking side by side on a narrow forest path, seen from behind, soft daylight through trees",
    f"{BOTH} standing lost among tall trees, looking around, misty soft light",
    "a long human shadow on a forest floor slowly rising up from the ground like a standing silhouette, magical realism, soft daylight",
    f"{EUNGYO} staring at her own shadow standing upright beside her on a forest path, surreal, soft daylight",
    f"{MUJAE} gently holding {EUNGYO}'s wrist on a forest path, close-up of hands, soft light",
    # 전자상가
    "a long dim corridor of an old 1970s concrete arcade building with small shuttered stalls, warm tungsten light and daylight from the far end, no signs",
    "an old concrete stairwell with worn terrazzo steps and a metal handrail, a beam of daylight, empty",
    "an old concrete walkway bridge connecting two worn 1970s buildings, seen from below, pale overcast sky, no signs",
    "a narrow cluttered workbench with a soldering iron, coils of copper wire and small vacuum tubes, warm lamp light, close-up, shallow depth of field",
    f"{EUNGYO} repairing a small old radio at a workbench with a soldering iron, warm lamp light, plain wall behind",
    f"{MUJAE} sorting small electronic parts in an old wooden drawer, warm light, close-up, no labels",
    "a tangle of old cables and copper wires hanging from a concrete ceiling, warm light, close-up",
    "rows of bare incandescent light bulbs glowing softly, warm amber, extreme shallow depth of field",
    f"{OLDMAN} carefully wrapping a single small light bulb in paper at a tiny counter, warm light, close-up of hands",
    "a single small light bulb resting in an open palm, warm glow, close-up",
    f"{BOTH} eating noodles together at a tiny folding table in a narrow corridor, warm light, plain wall",
    f"{BOTH} sitting on concrete steps sharing a drink from paper cups, soft afternoon light",
    "an old concrete rooftop of a 1970s building with water tanks and laundry lines, city haze in the distance, bright overcast",
    f"{BOTH} standing on an old rooftop looking at the hazy city, from behind, soft light",
    # 상가 사람들과 그림자
    f"{STOVE} sitting alone beside an old cold kerosene stove, staring at the floor, soft window light, plain wall",
    "a dark human shadow standing alone on a plain concrete wall with no one casting it, surreal, bright daylight",
    f"{FATHER} sitting alone at a small table eating, an empty chair opposite, soft window light",
    "a human shadow climbing up the outside wall of a tall plain apartment building, surreal, bright overcast day",
    f"{WIDOW} sitting motionless on a bench, her long shadow on the ground looking heavier than her, soft daylight",
    f"{EUNGYO} looking at a long shadow stretching across an empty corridor floor, soft light, unsettling",
    "two shadows of a man and a woman side by side on a plain cream wall, soft afternoon light",
    # 대화
    f"{BOTH} talking quietly face to face across a workbench, gentle expressions, warm lamp light",
    f"close-up of {EUNGYO}'s face listening, soft warm light, shallow depth of field",
    f"close-up of {MUJAE}'s face smiling shyly, soft window light",
    "a pair of matryoshka nesting dolls without any painted letters on a wooden shelf, soft light, close-up",
    # 정전·철거
    "an old corridor during a power outage lit only by daylight from a doorway, dust in the air, quiet",
    f"{BOTH} holding a single small candle between them in a dim corridor, faces softly lit, close-up",
    "an old shuttered stall with its metal shutter pulled down, plain grey, soft daylight, close-up",
    "a half-demolished old concrete building with exposed rebar under a pale sky, soft daylight, no signs",
    "a yellow excavator arm against a pale grey sky beside a crumbling concrete wall, soft daylight, no text",
    "empty rooms in a gutted concrete building, rubble on the floor, daylight from broken windows",
    f"{EUNGYO} standing alone in front of a fenced demolition site, from behind, overcast soft light",
    # 섬
    "a small ferry crossing a calm grey sea toward a small green island, soft overcast light",
    "a narrow island road along the sea at dusk with soft pastel sky, bright enough to see, quiet",
    f"{BOTH} walking along a quiet island road by the sea, from behind, soft pastel dusk light",
    f"{BOTH} holding hands tightly, close-up of hands, soft pastel light",
    "two long shadows of a man and a woman walking together on an empty road, soft warm light",
    "a calm sea at soft dawn with a pale golden horizon, peaceful, bright",
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
            seed = int(os.environ.get("SEED_BASE", "64000")) + i * 100 + k * 7
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

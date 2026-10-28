#!/usr/bin/env python3
"""「15소년 표류기」(쥘 베른) Flux 무드 이미지 배치 생성

1860 오클랜드 항구 → 스쿠너 표류·폭풍 → 무인도(체어맨 섬) 상륙 → 프랑스인 표류자의 동굴(프렌치 덴)
→ 사냥·덫·겨울·호수 스케이트 → 대통령 투표·브리앙/도니펀 갈등 → 반란 선원 상륙 → 화해·구명보트 귀향.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 배 이름·간판·책 표지 금지, 자연·클로즈업 위주.
인물은 「European boys in 1860s Victorian clothes」 명시(얼굴·국적), 개는 「a whole dog」로.
★ 배경은 장면별로만(BASE 금지). 밤 장면 금지(b<60). 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_15.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-19 /health 로 9010 확인
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Two_Years_Vacation_flux"))   # 검수 후 옮긴다

BASE = ("painted adventure book illustration in the style of a classic 19th century novel, soft natural daylight, bright enough to see clearly, not dark, "
        "warm palette of sea blue, sand, moss green and sunlit ochre, gentle film grain, hopeful adventurous mood, "
        "no ship names, no signs, no logos, no labels, no text, no letters, no numbers, no writing anywhere")

BOYS = "a group of European schoolboys aged ten to sixteen in 1860s Victorian jackets and caps, clear friendly human faces"
BR = "a fifteen-year-old French boy with tousled brown hair in a rumpled 1860s jacket, determined face"
DO = "a proud fifteen-year-old English boy with neat blond hair in a smart 1860s jacket, holding a hunting rifle"
SCENES = [
    "a 19th century wooden harbor of Auckland with small sailing ships at anchor under a clear morning sky, green hills behind",
    "a small two-masted schooner moored at a quiet wooden pier at dawn, calm water, mooring rope on the bollard",
    "close-up of a loosened thick mooring rope slipping off a wooden bollard into calm water",
    f"{BOYS} on the deck of a schooner looking out at the open sea, pale daylight",
    "a small two-masted schooner tossed on huge grey-green storm waves under heavy clouds with a break of light",
    f"{BR} gripping the wooden ship's wheel in wind and spray, daylight storm",
    "a wrecked schooner lying on its side on a sandy beach of a wild island, calm morning after the storm",
    f"{BOYS} wading ashore on a wide sandy beach carrying wooden crates, a whole friendly brown dog running beside them",
    "a wild uninhabited island coastline with cliffs, forest and a long white beach under a bright sky",
    "a dense green temperate forest of beech trees with sunlight beams, untouched wilderness",
    "the entrance of a dry cave in a rocky cliff beside a river, sunlight, ferns and bushes",
    "inside a sunlit rock cave with simple wooden furniture, hammocks, barrels and a fire place, cozy shelter",
    "an old rusty iron pickaxe and a broken clay pot lying on the floor of a rocky cave, close-up, soft light",
    "a large calm blue lake surrounded by forest and low hills on a wild island, bright day",
    f"{BOYS} pulling a big log raft loaded with crates along a river, sunny day",
    "a sturdy boy with dark hair in 1860s clothes building a wooden cart with simple tools on a beach, focused",
    "a tall older boy with short dark hair in a 1860s waistcoat examining wild plants and leaves in a forest clearing",
    f"{DO} aiming at birds on a misty marsh at morning, reeds around",
    "a simple wooden snare trap among ferns and moss in a forest, close-up, soft daylight",
    "a flock of seals resting on rocks by the sea, island shore, bright overcast sky",
    "a big flightless rhea bird running across a grassy plain on a wild island, sunny",
    "a snowy island landscape in winter with a frozen lake and pine trees, pale bright daylight",
    f"{BOYS} ice skating on a frozen lake in winter, wrapped in wool scarves, bright day",
    "warm firelight in a rock cave in winter with boys' boots and wool coats drying, cosy, bright lantern light",
    f"{BOYS} gathered in a circle inside a sunlit cave dropping folded paper slips into a wooden box, voting",
    f"{BR} and {DO} facing each other in a tense argument on a beach, other boys watching",
    f"{DO} and three other boys walking away along the shore with rifles and packs, seen from behind",
    "a small ship's lifeboat drifting onto a rocky beach with rough-looking bearded sailors climbing out, overcast day",
    "rough bearded 19th century sailors with knives and muskets lurking among forest trees, daylight, menace",
    "a spotted jaguar crouching in tall grass at the edge of a forest, daylight",
    f"{BR} helping {DO} up from the ground in a forest clearing, reconciliation",
    "a kind weathered middle-aged sailor with a grey beard in a blue 1860s coat, a ship's mate, warm face, on a beach",
    "a kind middle-aged woman in a plain 1860s dress and shawl sitting among a group of young boys by a fire, motherly, bright",
    f"{BOYS} and a bearded sailor repairing a wooden lifeboat on a sunny beach, hammering planks",
    f"a small wooden boat with a sail leaving a wild island at sunrise, {BOYS} on board waving, bright morning sea",
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

#!/usr/bin/env python3
"""「객지」(황석영) Flux 무드 이미지 배치 생성

1960년대 말 바닷가 간척 공사장 → 갯벌·방조제·돌 나르는 지게·손수레 → 함바(합숙소)의 맨벽·담요·양은 도시락
→ 전표 대신 손(글자 유발 소품은 쓰지 않는다) → 감독의 폭력은 그림자·주먹 클로즈업 → 동혁과 대위
→ 밤의 모의(등잔불, 밝게) → 경찰 트럭은 먼 실루엣 → 산 위로 오르는 일꾼들 → 하나둘 내려가는 뒷모습
→ 홀로 남은 동혁, 바다를 내려다보는 새벽.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 간판·현수막·깃발·지폐·전표·포장지·트럭 번호판은
글자가 붙으므로 쓰지 않는다. 군중 장면은 깃발이 붙으니 소수 인물로. 인물마다 「Korean … black hair」 명시
(빠뜨리면 서양인). BASE 는 사진풍 「35mm period film still」.

    SEED_BASE=77000 .venv/bin/python scripts/gen_flux_gaekji.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Gaekji_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still, late 1960s period film, natural daylight, "
        "bright enough to see clearly, not dark, light film grain, "
        "no logos, no text, no letters, no signs, no writing anywhere, no watermark, no signature")

DONGHYUK = ("a lean Korean laborer in his late twenties with short black hair, a calm determined face, "
            "wearing a faded grey work shirt with rolled sleeves and loose dark trousers")
DAEWI = ("a stocky hot-tempered Korean laborer in his thirties with cropped black hair and a rough stubbled face, "
         "wearing an old faded army field jacket without insignia")
WORKERS = "a few weathered Korean laborers with black hair in faded work clothes and straw hats"
FOREMAN = "a burly Korean foreman with slicked black hair in a dark jacket, arms crossed, stern face"

SCENES = [
    # 간척 공사장 — 바다와 갯벌
    "a vast grey tidal mudflat at low tide stretching to the horizon under a pale sky, soft daylight",
    "a long half-built stone sea dike curving across a tidal flat, heaps of rocks, soft overcast daylight",
    f"{WORKERS} carrying rocks on wooden A-frame backpacks along a muddy sea dike, wide shot, soft daylight",
    "close-up of a laborer's hands gripping the wooden straps of an A-frame back carrier loaded with stones, shallow depth of field",
    f"{WORKERS} pushing wooden wheelbarrows full of stones along planks over mud, soft daylight",
    "a small steam excavator and piles of rubble on a coastal reclamation site, distant, hazy daylight",
    # 도착 — 새 일꾼
    f"{DONGHYUK} walking alone on a dusty coastal dirt road with a small cloth bundle on his shoulder, wide shot, soft daylight",
    f"close-up of {DONGHYUK} looking out at a muddy construction site by the sea, wind in his hair, shallow depth of field",
    # 합숙소 — 함바
    "the inside of a crude wooden workers' barracks with bare plank walls, rows of thin grey blankets on a wooden floor, daylight through a small window",
    "close-up of a dented aluminium lunch box with rice and kimchi on a wooden plank, shallow depth of field, soft daylight",
    f"{WORKERS} eating rice from metal bowls sitting on the floor of a bare wooden barracks, warm daylight from the door",
    "close-up of worn rubber shoes and muddy boots lined up at the door of a wooden barracks, shallow depth of field",
    "a row of crude wooden barracks huts with tin roofs beside a muddy yard near the sea, soft overcast daylight",
    # 빚과 착취 — 손
    "close-up of a rough calloused palm holding a few small dull coins, shallow depth of field, soft daylight",
    "close-up of a tired laborer's face with sweat and dust, staring down, shallow depth of field, soft daylight",
    f"{FOREMAN} standing on a sea dike watching laborers work, low angle, soft daylight",
    "close-up of a clenched fist with scraped knuckles, shallow depth of field, soft daylight",
    "close-up of a bandaged hand resting on a knee, shallow depth of field, soft daylight",
    "a cheap makeshift drinking stall shack with a wooden bench and empty bowls by a muddy road, soft daylight",
    # 대위 — 분노와 폭행
    f"close-up of {DAEWI} shouting angrily, veins on his neck, soft daylight",
    f"{DAEWI} confronting {FOREMAN} face to face on a muddy work site, tense, soft daylight",
    f"{DAEWI} lying hurt on the muddy ground, bruised face, other laborers kneeling around him, soft daylight",
    f"{DONGHYUK} kneeling and helping a bruised injured Korean laborer in an army jacket sit up, soft daylight",
    # 모의 — 밤
    f"{DONGHYUK} talking quietly to {WORKERS} sitting in a circle inside a bare barracks, a kerosene lamp casting warm light, bright enough to see faces",
    "close-up of a small kerosene lamp flame on a wooden floor in a bare room, warm glow, bright",
    f"close-up of {DONGHYUK}'s face lit by warm lamplight, serious and thoughtful, bright enough to see clearly",
    f"{DONGHYUK} and {DAEWI} whispering together behind a wooden barracks at dusk, warm golden light",
    # 시찰 전날 — 긴장
    "a dusty coastal road with a distant black 1960s sedan approaching, wide shot, soft daylight",
    "a distant line of policemen in dark uniforms and helmets walking along a coastal dirt road, wide shot, hazy daylight, no flags",
    f"{WORKERS} dropping their tools on the muddy ground and standing still, soft daylight",
    # 산 위로 — 독산
    f"{DONGHYUK} leading {WORKERS} climbing a steep bare rocky hill above the sea, wide shot, soft daylight",
    "a bare rocky hilltop with scrubby pine trees overlooking a grey sea and a tidal flat, soft daylight",
    f"{WORKERS} sitting tired among rocks and pine trees on a hilltop, soft afternoon light",
    "close-up of a small campfire among rocks on a hillside at dusk, warm glow, bright",
    f"{DONGHYUK} standing on a rock looking down at the reclamation site far below, wind, soft daylight",
    # 회유와 이탈
    "two laborers in straw hats walking down a hill path away from the camera, small figures, soft daylight",
    f"{FOREMAN} talking softly to a hesitant young Korean laborer, offering a cigarette, soft daylight",
    "a narrow dirt path winding down a bare hillside with scattered footprints, soft daylight",
    f"close-up of {DAEWI} with a bandaged forehead looking back sadly over his shoulder, soft daylight",
    # 홀로 남음 — 결말
    f"{DONGHYUK} alone on a bare hilltop, small figure against a wide pale sky above the sea, wide shot, soft dawn light",
    f"close-up of {DONGHYUK} sitting alone among rocks, a calm resolute expression, soft dawn light, shallow depth of field",
    "sunrise over a grey tidal flat and a half-built sea dike, soft golden light",
    "a single pine tree on a windy hilltop above the sea at dawn, soft golden light",
    "an empty muddy reclamation site at dawn with abandoned wheelbarrows and A-frame carriers, soft golden light",
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
            seed = int(os.environ.get("SEED_BASE", "77000")) + i * 100 + k * 7
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

#!/usr/bin/env python3
"""「푸른 사자 와니니」(이현) Flux 무드 이미지 배치 생성

세렝게티 새벽 초원 → 마디바 무리(늙은 우두머리 암사자·새끼들) → 작고 약한 와니니 → 한밤의 침입자(밤 금지 → 해 질 녘)
→ 다친 말라이카·쫓겨나는 와니니 → 떠돌이(원숭이·새·치타·굶주림·알과 곤충) → 수사자 잠보·다리 저는 아산테
→ 첫 사냥 → 비구름을 찾아 초원의 끝 → 비·강 건너기 → 무투와의 싸움 → 아산테의 마지막 → 초원을 달리는 와니니 무리.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 사람·차량·총·표지판 금지(밀렵꾼은 빈 초원의 긴장으로만).
야생 다큐 사진풍 BASE. ★ 배경은 장면별로만(BASE 금지). 밤 장면 금지(밝기 ≥60).

    .venv/bin/python scripts/gen_flux_wanini.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Wanini_the_Green_Lioness_flux"))   # 검수 후 옮긴다

BASE = ("wildlife documentary photograph, telephoto lens, warm natural daylight, bright enough to see clearly, not dark, "
        "soft warm palette of golden grass, acacia green, dusty ochre and pale blue sky, shallow depth of field, gentle film grain, "
        "anatomically correct animals with four legs, tender, brave, hopeful mood, no people, no vehicles, no logos, no text, no letters, no numbers, no writing anywhere")

WA = "a small slender young lioness about one year old with faint spots on her legs, big alert ears and bright amber eyes"
MA = "a sturdy strong young lioness about one year old, broad chest, bold stare"
MD = "an old scarred lioness matriarch, lean and powerful, cold stern eyes"
AS = "a large adult male lion with a thick golden mane, limping on his left front leg, a healed scar on his shoulder"
JA = "a young male lion about two years old with a short scruffy patchy mane, clever curious face"
MU = "a huge menacing male lion with a long dark black mane, fierce eyes"

SCENES = [
    # 1 초원과 마디바 무리
    "vast golden savanna at sunrise in Serengeti, scattered umbrella acacia trees, soft mist, wide view",
    f"a pride of lionesses and cubs resting under an umbrella acacia tree in golden morning light, {MD} watching over them",
    f"close-up portrait of {MD} lying on a rock outcrop overlooking the savanna, bright daylight",
    f"several lion cubs playing and wrestling in tall golden grass, one small thin cub watching from the side, sunny",
    f"close-up portrait of {WA}, ears perked, listening intently, golden grass background, morning light",
    f"{MA} playfully pinning {WA} down in the grass, dust in the air, bright day",
    f"a group of lionesses stalking a herd of zebra across open grassland, {WA} trailing far behind, bright afternoon",
    f"{WA} lying alone a little apart from the pride under a thorn bush, looking at the others, warm afternoon light",
    # 2 침입자와 사고
    f"two male lions creeping low through tall grass at golden dusk, {AS} and {JA}, glowing warm sunset light",
    f"{WA} spotting two male lions in the grass at golden sunset, ears forward, warm bright orange sky",
    f"{MA} lying wounded in the grass with a scratch on her flank, dust settling, bright overcast daylight",
    f"{MD} standing tall and roaring over {WA} who crouches with ears flat, bright day, dust in the air",
    f"{WA} walking away alone across open savanna, looking back over her shoulder at the distant pride under a tree, wide shot, bright daylight",
    # 3 떠돌이
    f"{WA} standing alone in vast empty golden grassland under a huge pale blue sky, tiny in the frame",
    f"a troop of baboons sitting in an acacia tree looking down at {WA} below, bright sunny day",
    f"a flock of white egrets and a marabou stork standing in grass near {WA}, bright day",
    f"a cheetah sprinting after {WA} across the grass, dust flying, motion blur, bright daylight",
    f"close-up of {WA} chewing on a tuft of dry grass, hungry thin face, warm afternoon light",
    f"close-up of {WA} sniffing at a ground nest with speckled eggs in the grass, bright day",
    f"{WA} lying exhausted in the thin shade of a dry thorn bush, heat haze over the savanna",
    f"a group of spotted hyenas watching from a distance across dry grassland, bright hazy day",
    # 4 수사자들
    f"{JA} lying in the grass and lifting his head curiously, close-up, warm morning light",
    f"close-up portrait of {AS}, wise tired eyes, golden mane glowing in the sun",
    f"{AS} limping slowly across the savanna, side view, bright golden afternoon",
    f"{WA} and {JA} sitting side by side on a termite mound looking out over the plains, bright day",
    f"{AS}, {JA} and {WA} resting together under an umbrella acacia tree, midday shade, warm light",
    # 5 첫 사냥
    f"{WA} crouching low in tall grass, eyes locked on a herd of wildebeest, tense, bright morning",
    f"{WA} leaping toward a warthog that runs away with its tail up, dust, motion blur, bright day",
    f"{WA} and {JA} sharing a meal over a small antelope carcass in the grass, proud, bright day",
    # 6 말라이카와 재회
    f"{MA}, thin and limping, approaching {WA} through the grass, cautious, bright soft daylight",
    f"two young lionesses rubbing heads together affectionately in golden grass, warm afternoon light",
    # 7 초원의 끝, 비, 강
    "cracked dry earth and a dried-up waterhole on the savanna under a hazy pale sky, bright day",
    f"four lions walking in a line across a dusty dry plain toward distant blue hills, wide shot, bright daylight",
    "an old elephant with large tusks standing near a baobab tree on the plains, bright day",
    "huge white rain clouds gathering over the green distant horizon of the savanna, sun breaking through, bright",
    f"{WA} standing in light rain with water droplets on her fur, eyes half closed, soft bright light",
    "a wide brown river winding through the savanna with hippos in the water, bright sunny day",
    f"lions wading across a shallow river, water splashing, bright daylight",
    # 8 무투와의 싸움
    f"close-up portrait of {MU} standing on a rocky ridge, bright harsh daylight",
    f"{MU} and {AS} fighting, rearing up and clawing, dust exploding around them, bright daylight",
    f"{AS} lying in the tall grass, resting his head, calm noble face, soft golden afternoon light",
    # 9 와니니 무리
    f"{WA} now older and stronger, standing on a rock and roaring across the plains, golden light",
    f"a small pride of four lions running together across golden grassland, side view, motion, bright warm light",
    "vast green savanna after the rains with zebra and wildebeest grazing, umbrella acacia trees, bright sunny day, wide view",
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

#!/usr/bin/env python3
"""「파견자들」(김초엽) Flux 무드 이미지 배치 생성

프롤로그 겨울 입양 가정의 여자아이 → 범람체를 피해 내려간 지하 도시(동굴 주거·터널·형편없는 식사)
→ 어린 태린과 스승 이제프, 노을·별 이야기, 황동 지구본 → 파견자 아카데미 훈련·최종 시험
→ 유화 물감을 흩뿌린 듯한 지상(범람체에 덮인 폐허 도시·균류·포자) → 머릿속 목소리 쏠
→ 늪과 늪인 → 아동 보호소로 위장한 연구소 → 경계 지역, 노을.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 화면·계기판·간판·표지판·라벨·책·시계 금지.
사진풍 영화 스틸 BASE(삽화풍은 모서리 서명이 붙는다). 한국 인물은 「Korean … black hair」를 인물마다 명시.

    SEED_BASE=66000 .venv/bin/python scripts/gen_flux_dispatchers.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Dispatchers_flux"))   # 검수 후 옮긴다

BASE = ("cinematic science fiction film still, quiet literary drama, soft natural light, bright enough to see clearly, not dark, "
        "shallow depth of field, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no numbers, no signs, no labels, no writing anywhere, no watermark, no signature")

GIRL = "a small Korean girl of seven with black hair in a plain grey sweater"
TAERIN = "a determined Korean young woman of nineteen with short black hair, in a plain grey jumpsuit"
SUIT = "a Korean young woman with short black hair in a plain pale grey protective suit with an open clear visor"
IJEF = "a tall calm man in his thirties with dark hair and a stern gentle face, in a plain dark long coat"
SEONO = "a gentle Korean young man of nineteen with black hair, in a plain grey jumpsuit"

SCENES = [
    # 프롤로그 — 겨울, 입양된 여자아이
    "a quiet suburban house in winter with soft snow on the roof, pale morning light",
    f"{GIRL} sitting by a frosted window, looking out and waiting, soft winter daylight",
    "a small folded blank paper note on a child's bed with a white blanket, soft winter light",
    # 지하 도시
    "a vast underground cavern city with terraced stone dwellings carved into rock walls, warm amber lamps everywhere, bright and clearly visible",
    "a long narrow underground tunnel corridor with smooth rock walls and warm hanging lamps, bright enough to see",
    "a plain metal tray with grey bland food on a long canteen table in an underground hall, warm lamp light",
    f"{GIRL} and {IJEF} sitting together on a rock ledge in a warm lamplit cavern, he tells her a story",
    "close-up of a child's hands turning an old plain brass globe with smooth unmarked continents, warm lamp light",
    f"{TAERIN} looking up at a high rock ceiling of an underground cavern lit by warm lamps, longing",
    "people walking quietly through a busy underground market street in a lamplit cave, warm light, no signs",
    # 아카데미 · 시험
    f"{TAERIN} running on a track in a bare bright underground training hall with rock walls",
    "young recruits in plain grey jumpsuits standing in rows in a bare bright underground hall",
    f"{TAERIN} and {SEONO} sitting on a stone bench in an underground garden with pale mushrooms and lamps, talking",
    f"{TAERIN} holding her head with both hands, eyes closed, hearing a strange voice, warm lamplight, blurred background",
    f"{TAERIN} lying awake on a plain bed in a small rock-walled room, warm dim lamp, thoughtful",
    "a huge round plain metal hatch door in a rock wall of an underground tunnel, warm light",
    "a long vertical shaft with a plain metal lift platform rising toward a bright circle of daylight far above",
    # 지상 — 범람체
    "a ruined overgrown city completely covered in vivid colorful fungi and moss like splashes of oil paint, bright daylight",
    "crumbling concrete buildings covered in brilliant orange, violet, teal and yellow fungal growth, bright soft daylight",
    "close-up of strange glowing colorful mushrooms and lace-like fungus on a broken stone wall, bright daylight",
    "golden spores drifting through sunbeams over a field of colorful moss, dreamy bright light",
    f"{SUIT} standing amazed in a street of ruins overgrown with vivid colorful fungi, bright daylight",
    f"{SUIT} kneeling and touching a bright violet fungus with a gloved hand, bright daylight",
    "fine white fungal threads like a web spreading over a fallen tree trunk, close-up, bright soft light",
    "a wide empty highway overgrown with rainbow colored fungus and tall grass, bright daylight",
    "three people in plain pale grey protective suits walking in a line through colorful overgrown ruins, bright daylight",
    "a vast colorful fungal forest with giant mushroom caps taller than trees, bright misty daylight",
    # 늪 · 늪인
    "a wide misty swamp covered with glowing colorful fungi and still water, soft bright morning light",
    "still swamp water reflecting colorful fungal growth and a pale sky, soft light, peaceful",
    "a calm human figure standing waist deep in a colorful fungal swamp, body partly covered with soft moss and mushrooms, peaceful face, soft light",
    f"{SUIT} sitting at the edge of a colorful glowing swamp, listening quietly, soft morning light",
    "a swarm of tiny glowing flies drifting in a sunbeam over a colorful swamp, soft light",
    "close-up of dense glowing fungal threads connected like a network of neurons, soft colorful light",
    # 연구소
    "a bare white room of an old children's shelter with small plain beds in a row, soft window light",
    "unlabeled glass jars with colorful fungal samples on a plain white laboratory shelf, soft bright light",
    f"{SEONO} sitting alone against a white wall of a bare locked room, soft light",
    f"{IJEF} standing still in a long bare white corridor, cold soft light, serious",
    f"{TAERIN} and {IJEF} facing each other in a bare white room, tense and sad, soft light",
    # 경계 지역 · 결말
    f"{TAERIN} walking alone through a field of colorful fungi toward a bright horizon, from behind, golden light",
    "a gentle boundary where a green meadow meets a field of colorful fungi, bright soft sunlight",
    "a glowing orange and pink sunset over a quiet overgrown city covered in colorful moss",
    f"{TAERIN} standing on a hill watching a brilliant sunset, wind in her short black hair, golden light",
    "a small group of people sitting together in a sunny meadow edged with colorful fungi, peaceful, bright daylight",
    "bright morning sun rising over hills covered with colorful moss and green grass, hopeful",
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
            seed = int(os.environ.get("SEED_BASE", "66000")) + i * 100 + k * 7
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

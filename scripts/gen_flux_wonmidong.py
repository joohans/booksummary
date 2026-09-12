#!/usr/bin/env python3
"""「원미동 사람들」 Flux 무드 이미지 배치 생성

무료 스톡에 1980년대 한국 변두리 이미지가 사실상 없다(195장 중 38장이
유럽·중국·제품컷이라 폐기). 만세전과 같은 처방으로 실사 42장 + Flux 38장을 섞는다.

⛔ 글자 차단은 소재로 한다 ([[project_flux_text_problem]]) — 간판·현판·신문·
   가격표·버스 행선판을 장면에서 아예 뺀다. 구멍가게는 '내부 선반'으로만 그린다.
★ 저장은 반드시 mood_*.jpg — 렌더러는 glob("mood_*.jpg") 만 읽는다
   ([[project_render_image_order]])
"""
import base64, json, sys, time, urllib.request
from pathlib import Path

# 포트는 매번 /health 의 model·loaded 로 확인 ([[feedback_thumbnail_gpu151]])
FLUX = "http://192.168.0.150:9010/generate"
OUT = Path("assets/images/A_Distant_and_Beautiful_Place")

BASE = ("cinematic film still, late 1980s South Korean suburban neighborhood, "
        "pale concrete and red brick, muted overcast palette, soft winter daylight, "
        "35mm film grain, shallow depth of field, quiet everyday mood, no text anywhere")

SCENES = [
    # 사람 — 밀려온 사람들
    "a middle-aged Korean man in a worn windbreaker carrying a gas cylinder up a narrow concrete alley, seen from behind",
    "a pregnant Korean woman in her thirties standing beside a small loaded moving truck on a bare suburban street",
    "a Korean family unloading bundles and a wardrobe from a small truck in front of a two-story brick rowhouse",
    "an old Korean farmer in rubber boots watering a small vegetable plot squeezed between concrete buildings",
    "close-up of an old Korean farmer's weathered hands pressing soil around seedlings",
    "a thin young Korean man in his twenties sitting alone on concrete steps, knees drawn up",
    "a seven-year-old Korean girl in a padded jacket standing alone at the mouth of a narrow alley, seen from behind",
    "a small Korean girl crouching to look at something on the ground in a concrete alley",
    "a Korean man carrying a stack of coal briquettes on a wooden carrier frame up an alley, seen from behind",
    "a middle-aged Korean woman in an apron standing in the doorway of a tiny corner shop, arms folded",
    "two middle-aged Korean women arguing across crates of vegetables on a concrete pavement",
    "a Korean laborer squatting to eat from a metal bowl on a half-demolished concrete floor",
    "close-up of a Korean workman's hands tightening a pipe fitting under a tiled washroom basin",
    "a young Korean woman in a cheap sequined dress sitting alone under a bare bulb backstage",
    "a middle-aged Korean man asleep sitting upright on a night bus, blurred city lights outside the window",
    # 동네 — 원미동
    "narrow concrete alley between two-story brick rowhouses with laundry lines overhead, overcast winter light",
    "a dead-end alley with a blue painted iron gate and a plastic water tank on the roof above",
    "rows of identical two-story brick rowhouses in a new suburban district, muddy unpaved road in front",
    "a small cabbage field surrounded on every side by new concrete buildings",
    "a half-built apartment block behind a fence of corrugated metal sheets, winter sky",
    "interior of a tiny neighborhood grocery, wooden shelves of tinned goods and an old refrigerator, dim bulb",
    "crates of cabbages and white radishes stacked outside a shop on a concrete pavement",
    "an empty dirt lot with piles of construction sand and one bare tree",
    "an empty public bathhouse washroom, tiled walls, plastic stools, steam",
    "a cramped semi-basement room with a small window at ceiling height and a folded quilt on the floor",
    "a rooftop with plastic water tanks and laundry lines, low rowhouses stretching beyond",
    "a stairwell of an old concrete building, worn steps and a single dusty window",
    "an empty suburban bus stop at dusk under one streetlamp",
    "a snow covered alley with coal briquette ash scattered across the snow",
    "a bare persimmon tree behind a low brick wall in winter",
    "a narrow alley at night lit by a single yellow streetlamp, wet concrete underfoot",
    "a curtained shop window glowing warm at dusk seen from an empty street",
    # 소품·상징
    "close-up of stacked coal briquettes beside the rusted iron door of a stove",
    "a red plastic basin and rubber slippers beside a tap in a concrete yard",
    "laundry frozen stiff on a line against a grey winter sky",
    "a chipped enamel bowl of steaming rice on a low table in a dim room",
    "a pair of worn leather work gloves resting on a pile of bricks",
    "a bicycle with a delivery crate leaning against a concrete wall in an alley",
]


def generate(prompt: str, seed: int) -> bytes | None:
    body = json.dumps({"prompt": prompt, "width": 1920, "height": 1080,
                       "steps": 4, "seed": seed}).encode()
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
    made, t0 = 0, time.time()
    for i, scene in enumerate(SCENES, 1):
        for k in range(per):
            img = generate(f"{BASE}, {scene}", i * 1000 + k * 7)
            if not img:
                continue
            path = OUT / f"mood_flux_{i:02d}_{k+1}.jpg"
            path.write_bytes(img)
            made += 1
            print(f"[{made}] {path.name} ({time.time()-t0:.0f}s) {scene[:52]}", flush=True)
    print(f"\n✅ {made}장 생성 / {time.time()-t0:.0f}초")


if __name__ == "__main__":
    main()

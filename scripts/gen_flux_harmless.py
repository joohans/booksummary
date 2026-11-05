#!/usr/bin/env python3
"""「내게 무해한 사람」(최은영) Flux 무드 이미지 배치 생성

소설집 7편 — 그 여름(고교 운동장의 축구공, 이경과 수이, 여름 강가·자전거, 서울로 떠난 뒤 멀어짐)
→ 601, 602(아파트 이웃 두 소녀, 베란다) → 지나가는 밤(오래 멀어진 자매, 겨울 펜션)
→ 모래로 지은 집(이십대 친구 셋, 바닷가 모래집) → 고백(고교 시절 세 친구, 성당·기도) → 손길(이모와 조카)
→ 아치디에서(북유럽 바닷가 마을, 이방인) → 마무리(빈 운동장·창가의 빛).
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 학교 건물·교실 칠판·아파트 호수판·간판 금지, 얕은 심도·자연.
★ 배경은 장면별로만(BASE 금지). 밤 장면 금지(겨울밤도 실내 따뜻한 낮빛으로). 인물마다 「Korean … black hair」 명시.

    SEED_BASE=52000 .venv/bin/python scripts/gen_flux_harmless.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Someone_Harmless_to_Me_flux"))   # 검수 후 옮긴다

BASE = ("quiet literary film still, soft natural daylight, bright enough to see clearly, not dark, "
        "muted pastel palette of pale blue, soft grey and warm beige, extreme shallow depth of field, soft bokeh, gentle film grain, "
        "tender melancholy mood, fully clothed modest figures, no signboards, no signs, no logos, no labels, "
        "no text, no letters, no numbers, no writing anywhere, no watermark, no signature")

GYEONG = "a Korean teenage girl with short black hair, in a plain white short-sleeve blouse, 2000s"
SUI = "a sporty Korean teenage girl with a black ponytail and tanned skin, in a plain navy track jacket, 2000s"
GYEONG20 = "a Korean woman in her twenties with shoulder-length black hair, in a plain beige cardigan"
SUI20 = "a Korean woman in her twenties with a black ponytail, in a plain grey hoodie"
GIRLS = "two Korean girls of about ten with black hair, in plain cotton T-shirts, 1990s"
SISTERS = "two Korean sisters in their thirties with black hair, in plain knit sweaters"
FRIENDS = "three Korean friends in their twenties with black hair, in plain casual clothes, 2000s"
HIGH3 = "three Korean high school girls with black hair, in plain white blouses and navy skirts, 2000s"
WOMAN = "a Korean woman in her late twenties with long black hair, in a plain dark wool coat"

SCENES = [
    # 그 여름
    "a sunlit dirt sports field edged with tall green trees on a bright summer afternoon, empty, heat haze",
    "a worn white soccer ball rolling on dry dirt in bright summer sunlight, close-up, dust in the air",
    f"{GYEONG} holding her cheek on a sunlit dirt field, surprised, soft focus green trees behind",
    f"{SUI} kneeling beside {GYEONG} on a sunlit dirt field, looking worried, warm afternoon light",
    f"{GYEONG} and {SUI} sitting side by side on grassy riverbank steps, summer afternoon, soft light on the water",
    f"{GYEONG} and {SUI} riding one bicycle along a quiet riverside path, green summer leaves, motion blur",
    f"close-up of two teenage girls' hands almost touching on warm grass, summer sunlight, shallow depth of field",
    f"{SUI} laughing with her eyes closed under dappled summer sunlight through leaves, close-up portrait",
    f"{GYEONG20} looking out of a bus window at passing green fields, pensive, soft daylight, reflections",
    f"{SUI20} standing alone on an empty riverbank, wind in her hair, overcast soft light",
    f"{GYEONG20} and {SUI20} sitting apart on a park bench, not looking at each other, pale autumn light",
    "fallen yellow ginkgo leaves on an empty park bench, soft autumn light, close-up",
    # 601, 602
    f"{GIRLS} leaning over a sunny apartment balcony railing with potted plants, looking at each other, 1990s",
    f"{GIRLS} sitting on a living room floor with crayons and blank paper, warm afternoon light, 1990s",
    "a quiet sunlit Korean apartment living room with a low wooden table and lace curtains, 1990s, empty",
    f"a Korean girl of about ten with black hair hugging her knees in a corner near a window, sad, soft light, 1990s",
    # 지나가는 밤
    "a small wooden cabin among snowy pine trees on a bright winter afternoon, smoke from the chimney",
    f"{SISTERS} sitting at a small wooden table with two steaming mugs of tea in a warm cabin, awkward silence, daylight",
    f"{SISTERS} walking apart along a snowy forest path, footprints in the snow, soft grey light",
    "two steaming mugs of tea on a wooden windowsill, snowy trees blurred outside, close-up",
    "old family photographs face down on a wooden table, soft window light, close-up, no faces",
    # 모래로 지은 집
    f"{FRIENDS} sitting together on a wide sandy beach on a bright breezy day, laughing, 2000s",
    "a small sandcastle on a beach with a gentle wave about to reach it, soft daylight, close-up",
    f"{FRIENDS} walking barefoot along the shoreline at golden hour, long shadows, from behind",
    f"{GYEONG20} sitting alone on an empty beach hugging her knees, overcast pale sky, melancholy",
    "a half-washed-away sandcastle on wet sand, soft grey sea behind, close-up",
    "a small rented room with a single bed and a desk by a bright window, plain walls, 2000s, empty",
    # 고백
    f"{HIGH3} sitting on a low stone wall under blooming cherry trees, sharing snacks, spring daylight",
    f"{HIGH3} walking arm in arm along a quiet tree-lined path, spring sunlight, from behind",
    "a quiet empty chapel interior with wooden pews and soft colored light from a plain glass window",
    f"{WOMAN} sitting alone in a wooden pew of a quiet chapel, head bowed, soft window light",
    f"a Korean high school girl with long black hair looking down with teary eyes, soft spring light, close-up",
    "a single white lily lying on a wooden pew, soft window light, close-up",
    f"{WOMAN} sitting across a small table from an older Korean woman, listening, tea cups, warm daylight",
    # 손길
    f"a Korean woman in her fifties with short black hair gently brushing a young Korean girl's black hair, warm window light",
    "an older woman's hand resting on a child's hand on a cotton blanket, close-up, warm soft light",
    # 아치디에서
    "a remote green coastal village with a few white cottages under a wide pale northern sky, sheep on the hills",
    "a windswept grassy cliff above a grey-blue sea, soft overcast light, wildflowers in the wind",
    f"{WOMAN} standing on a windy grassy cliff looking at the sea, hair blowing, from behind",
    f"{WOMAN} and a young man with curly brown hair walking on a grassy coastal path, talking, soft daylight",
    # 마무리
    "an empty sunlit dirt sports field in late summer, long shadows of trees, quiet",
    "sheer white curtains moving in a breeze by a bright open window, soft summer light",
    f"{GYEONG20} standing by a bright window with her eyes closed, soft light on her face, close-up portrait",
    "sunlight sparkling on a calm river surface, extreme shallow depth of field, dreamy",
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
            seed = int(os.environ.get("SEED_BASE", "52000")) + i * 100 + k * 7
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

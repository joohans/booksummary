#!/usr/bin/env python3
"""「클라라와 태양」(가즈오 이시구로) Flux 무드 이미지 배치 생성

가게 진열창의 에이에프 클라라와 태양 → 노숙인과 개의 회복 → 조시의 선택 → 들판 위 조시의 집·어머니·가정부 멜라니아
→ 이웃 소년 릭과 그의 어머니 → 모건 폭포 → 헛간과 지는 해 → 도시의 쿠팅스 기계 → 초상화 작업실의 비밀 → 폭풍 뒤의 햇살과 회복
→ 성장한 조시·멀어지는 릭 → 야적장에서 기억을 정리하는 클라라.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 가게 간판·도시 거리·화면·포스터·책·기계 표지 금지 → 들판·맨벽 실내·클로즈업.
클라라는 「robot」 단어 대신 인형 같은 소녀로 묘사(금속 기계가 나오지 않게). 35mm 사진풍 BASE. ★ 배경은 장면별로만(BASE 금지). 밤 장면 금지.

    .venv/bin/python scripts/gen_flux_klara.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Klara_and_the_Sun_flux"))   # 검수 후 옮긴다

BASE = ("35mm film still, warm natural daylight, bright enough to see clearly, not dark, "
        "soft warm palette of golden sunlight, pale green, sky blue and warm grey, shallow depth of field, gentle film grain, "
        "quiet, tender, wistful but hopeful mood, no screens, no signboards, no signs, no logos, no labels, no text, no letters, no numbers, no writing anywhere")

KL = "a calm doll-like young woman with short dark bob hair, pale smooth skin, large observant eyes, simple plain grey dress, gentle still posture"
JO = "a thin pale American teenage girl of fourteen with long light brown hair, tired but bright smile, plain sweater"
MO = "an elegant tense American woman in her forties with dark hair pulled back, plain dark coat, worried eyes"
RI = "an American teenage boy of fifteen with messy brown hair, kind serious face, plain checked shirt"
SCENES = [
    # 가게 진열창과 태양
    "golden morning sunlight pouring through a large plain shop window onto a polished empty floor, dust motes, no signs",
    f"{KL} standing behind a large plain glass window, face turned up toward the sun, warm light on her face",
    f"close-up of {KL} with eyes half closed, basking in a beam of sunlight, serene",
    "a quiet empty city street at early morning seen through glass, soft blurred plain buildings, warm sunrise, no signs",
    "an old homeless man in a worn coat lying on a sidewalk beside his small dog in early morning shade, plain wall behind, gentle and respectful",
    "an old man in a worn coat sitting up on a sidewalk in a bright beam of morning sunlight, his small dog standing beside him, hopeful",
    f"{KL} watching from behind glass with wonder, morning sun on her face, soft focus background",
    # 조시와의 만남
    f"{JO} pressing her hand on a plain glass window and smiling at someone inside, morning light",
    f"{JO} and {MO} walking on a sunny sidewalk, the girl looking back over her shoulder, blurred plain buildings",
    f"{KL} and {JO} sitting together on a window seat in a bright bedroom, sunlight across them",
    # 조시의 집과 들판
    "a modern wooden country house standing alone at the edge of vast golden fields of tall grass, wide sky, morning",
    "vast fields of tall golden grass swaying under a wide blue sky, a lone distant barn on the horizon",
    f"{JO} lying pale in a bed under a soft quilt in a bright plain bedroom, window light, {KL} sitting beside her",
    f"{MO} standing in a sunlit plain kitchen with a coffee cup, staring out the window, worried",
    "a stern middle-aged housekeeper with grey hair in a plain apron standing in a doorway of a bright plain room, arms folded",
    f"close-up of {KL} watching quietly from the corner of a bright plain room, attentive eyes",
    # 릭
    f"{RI} walking through tall golden grass toward a wooden country house, sunny afternoon",
    f"{JO} and {RI} sitting close on a wooden porch step, laughing, warm afternoon light",
    f"{RI} flying a small handmade bird-shaped drone kite over golden fields, only sky behind, no text",
    "a small old cottage among tall grass across the field, a frail woman with grey hair standing at the door, soft light",
    f"{KL} and {RI} walking side by side along a dirt path through tall grass, late afternoon",
    # 모건 폭포
    "a waterfall cascading into a clear pool among green rocks and pine trees, mist and sunlight, wide view",
    f"{MO} and {KL} standing at a wooden railing near a misty waterfall, the woman looking at the girl intently",
    f"close-up of {MO} looking at someone with a strange longing expression, waterfall mist behind",
    "a wooden picnic table in a pine forest clearing near a waterfall, empty, soft dappled light",
    # 헛간과 지는 해
    "an old weathered wooden barn standing alone in golden fields with the sun setting directly behind it, long shadows",
    f"{KL} walking alone through tall golden grass toward a distant barn at sunset, back view",
    "the inside of an old empty wooden barn with golden sunset light streaming through the wide open doors and gaps in the planks, hay on the floor",
    f"{KL} standing inside an old wooden barn facing the setting sun through the open doors, hands together, pleading",
    "the orange setting sun sinking behind a field of tall grass, glowing horizon, peaceful",
    # 도시와 쿠팅스 기계
    "a large dirty yellow construction machine on a road with three tall smoke stacks belching grey smoke, hazy sky, no markings, no text",
    "a hazy sky darkened by grey smoke from a construction machine over a city skyline, sun dim behind the haze, no signs",
    f"{KL} standing on a plain sidewalk gazing up at a grey hazy sky, determined, blurred street behind",
    # 초상화의 비밀
    "a bright minimalist artist studio with high plain white walls and skylights, an empty easel and a draped cloth figure, no paintings",
    f"{MO} pulling back a white sheet from a lifelike life-size doll that looks like a teenage girl with light brown hair, bright plain studio",
    f"close-up of {KL} looking at something unsettling, still face, plain white studio wall behind",
    # 폭풍과 회복
    "dark storm clouds breaking apart over golden fields, a bright beam of sunlight bursting through, dramatic",
    f"{JO} in a bed bathed in brilliant golden sunlight pouring through a window, her face peaceful, bright plain bedroom",
    f"{JO} sitting up in bed in warm sunlight, smiling weakly, {MO} holding her hand, tears of relief",
    # 성장과 이별
    f"{JO} as a healthy young woman of eighteen with long light brown hair carrying a suitcase toward a car on a country road, bright morning",
    f"{RI} as a young man standing alone in golden grass watching someone leave, wistful",
    # 야적장
    f"{KL} sitting still on the ground in a wide quiet open yard of scattered old metal scraps under a pale wide sky, peaceful, soft daylight",
    f"close-up of {KL} with a faint gentle smile, eyes closed, warm sunlight on her face, soft blurred open sky",
    "a wide golden field under a vast bright sky with the sun shining high, warm and hopeful",
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

#!/usr/bin/env python3
"""「연을 쫓는 아이」(할레드 호세이니) Flux 무드 이미지 배치 생성

1970년대 카불 — 아미르와 하산, 석류나무 언덕, 겨울 연싸움 대회 → 골목에 떨어진 파란 연(폭력 장면은 그리지 않는다)
→ 죄책감·이별 → 1980년대 미국 캘리포니아의 아미르와 바바 → 파키스탄에서 걸려 온 전화 → 폐허가 된 고향
→ 하산의 아들 소랍 → 다시 연을 날리는 공원.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 시장·간판·가게·책 표지·현판 금지, 하늘·산·마당·인물 위주.
★ 35mm film still BASE. 배경은 장면별로만. 밤 장면 금지(밝기 ≥60). 인물은 「Afghan … dark hair」 명시. 무기·폭력 묘사 금지.

    SEED_BASE=47000 .venv/bin/python scripts/gen_flux_kite.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Kite_Runner_flux"))   # 검수 후 옮긴다

BASE = ("35mm film still, soft natural daylight, bright enough to see clearly, not dark, "
        "warm palette of dusty ochre, sky blue, pomegranate red and snowy white, shallow depth of field, light film grain, "
        "fully clothed modest figures, no weapons, no logos, no text, no letters, no signs, no numbers, no writing anywhere, no watermark, no signature")

AMIR = "a slim Afghan boy about twelve with neat dark hair, in a clean wool sweater and trousers, 1970s"
HASSAN = "a small Afghan boy about eleven with a shaved head and a round gentle face, in a plain loose tan shirt, 1970s"
BABA = "a tall broad-shouldered Afghan man in his forties with thick dark hair and a beard, in a dark suit, 1970s"
ADULT = "an Afghan man in his late thirties with short dark hair and a trimmed beard, in a plain shirt and jacket, 2000s"
SOHRAB = "a thin quiet Afghan boy about ten with dark hair and sad eyes, in a plain loose shirt"

SCENES = [
    # 1970년대 카불
    "a wide view of a dusty valley city of flat-roofed mud houses under snow-capped mountains, clear blue sky, 1970s Afghanistan",
    f"{AMIR} and {HASSAN} running side by side up a grassy hill, laughing, mountains behind",
    f"{AMIR} and {HASSAN} sitting under a pomegranate tree heavy with red fruit on a sunny hillside",
    "close-up of ripe red pomegranates hanging on a branch against a blue sky",
    f"{HASSAN} aiming a slingshot at a distant tree branch on a sunny hillside, playful",
    f"{BABA} standing proudly in the sunny walled garden of a large white villa with rose bushes",
    f"{AMIR} sitting alone on a garden bench writing in a plain notebook, the pages blank from this angle, looking wistful",
    f"{BABA} looking down coolly at {AMIR} in a sunny courtyard, the boy looking up hopefully",
    f"{HASSAN} sweeping a sunny stone courtyard with a broom, smiling shyly",
    "a modest mud-brick servant's hut at the back of a big garden, a loquat tree beside it, soft afternoon light",
    # 겨울 연싸움 대회
    "dozens of bright colorful paper kites in a clear winter sky above snowy flat rooftops, 1970s Afghanistan",
    f"{AMIR} holding a wooden spool of kite string on a snowy rooftop, squinting at the sky",
    f"{HASSAN} holding the spool beside {AMIR} on a snowy rooftop, both looking up at the sky",
    "close-up of a wooden spool wound with glass-coated kite string, a boy's gloved hands, snow",
    "a single blue paper kite soaring high against a pale winter sky",
    "two kites crossing strings high in a bright winter sky, one string snapping",
    f"{AMIR} raising his arms in triumph on a snowy rooftop, crowd of tiny figures on other rooftops",
    f"{HASSAN} running away down a snowy dirt lane chasing a falling kite, seen from behind",
    "a narrow empty snowy mud-walled alley in soft winter light, footprints in the snow",
    "a blue paper kite lying torn on the snow at the end of an empty alley, close-up",
    # 죄책감과 이별
    f"{AMIR} standing frozen behind a mud wall corner, face pale with fear, snowy alley",
    f"{AMIR} walking home alone in the snow, head down, guilty expression",
    f"close-up of {AMIR} lying awake in bed, morning light, troubled eyes",
    "a wrapped birthday present and a shiny wristwatch hidden under a thin mattress, close-up",
    "a small man and a boy carrying bundles walking away from a big villa gate in the rain, seen from far behind",
    "an empty mud-brick hut with a single folded blanket, dusty sunbeam through a doorway",
    # 미국
    "a dusty truck driving across a bare desert road under a wide pale sky, 1980s, seen from far away",
    f"{BABA} older and grey-haired, in a worn work jacket at a gas station forecourt in California sunshine, 1980s, no signs",
    "a modest small apartment living room in 1980s California, sunlight through blinds, plain walls",
    f"{ADULT} typing at a typewriter by a sunny window in a small apartment, plain blank paper",
    f"{ADULT} and an elegant Afghan woman with long dark hair walking together in a sunny California park, 1980s",
    f"{BABA} old and frail, grey-haired, resting in an armchair by a sunny window, gentle smile",
    f"close-up of {ADULT} holding a telephone receiver to his ear, shocked expression, plain wall",
    # 귀향
    "a winding dusty mountain road through a barren rocky pass under a hazy sky, a lone car far away",
    "ruined crumbling mud-brick houses in a dusty city under a hazy sky, empty street, no people",
    f"{ADULT} standing in the dusty ruins of an old walled garden, a dead pomegranate tree beside him, sorrowful",
    "a withered pomegranate tree on a dry hillside under a pale sky",
    f"close-up of {SOHRAB} looking down silently in a dim plain room lit by a window, soft light",
    f"{ADULT} kneeling to meet the eyes of {SOHRAB} in a plain sunlit room",
    f"{ADULT} and {SOHRAB} sitting apart on a bench in a sunny green park, silent",
    # 다시 연을
    "a bright colorful kite rising over a green park with families, sunny spring day, California",
    f"{ADULT} showing {SOHRAB} how to hold a kite string in a sunny park, the boy watching",
    f"close-up of {SOHRAB} with a faint first smile, looking up at the sky, sunny park",
    f"{ADULT} running across a sunny grassy park chasing a falling kite, seen from behind, joyful",
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
            seed = int(os.environ.get("SEED_BASE", "47000")) + i * 100 + k * 7
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

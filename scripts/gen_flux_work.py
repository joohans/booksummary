#!/usr/bin/env python3
"""「일의 기쁨과 슬픔」(장류진) Flux 무드 이미지 배치 생성

표제작: 판교 IT 회사 막내 안나 → 중고 거래 앱 파워 셀러 「거북이알」과의 만남 → 카드 포인트 월급·포인트로 산 물건
→ 조성진 공연·홍콩행 비행기. 수록작: 빛나 언니(결혼 준비) · 새벽의 방문자들(원룸) · 탐페레 공항(핀란드 노인)
· 다소 낮음(무명 뮤지션·낡은 냉장고) · 후쿠오카 · 도움의 손길(가사도우미) · 첫 출근(아이스 아메리카노).
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — ⚠️ 현대 한국+가게·간판은 거의 다 폐기(10/14).
→ 화면·모니터·휴대폰 화면·표·청첩장 금지, 얕은 심도 클로즈업·민무늬 벽·창가로. 인물마다 「Korean … black hair」 명시.
★ 배경은 장면별로만(BASE 금지). 밤 장면 금지(b<60). 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_work.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-19 /health 로 9010 확인
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Joys_and_Sorrows_of_Work_flux"))   # 검수 후 옮긴다

BASE = ("quiet contemporary literary film still, soft natural daylight, bright enough to see clearly, not dark, "
        "muted pastel palette of soft white, pale mint, warm beige and light grey, extreme shallow depth of field, soft bokeh, gentle film grain, "
        "wry, tender, everyday mood, no screens, no monitors, no signboards, no signs, no logos, no labels, no text, no letters, no numbers, no writing anywhere")

AN = "a Korean woman in her late twenties with shoulder-length black hair in a casual office cardigan"
TE = "a Korean woman in her thirties with black hair tied back, plain sweater, calm resilient face"
SCENES = [
    # 판교 사무실
    "a bright modern open-plan office with white desks and plants, people blurred far away, plain white walls, shallow depth of field, no screens visible",
    f"{AN} sitting at a white desk holding a paper cup of iced americano, looking tired, plain white wall behind, close-up",
    f"{AN} sitting in a glass meeting room, chin on hand, bored, colleagues blurred, plain walls",
    "close-up of a hand holding a tall iced americano with condensation, soft window light",
    "a lanyard employee badge lying face down on a white desk beside a coffee cup, close-up, soft light",
    "glass office towers seen from below against a pale blue sky, bright daylight, no signs, abstract",
    # 거북이알
    f"{AN} and {TE} sitting across from each other at a small wooden café table by a window, coffee cups, soft daylight, close-up, blurred background",
    f"{TE} smiling slightly, sitting by a sunlit café window, close-up portrait",
    "a neat row of brand-new unopened plain cardboard boxes stacked in a small apartment, soft daylight, no labels",
    f"{TE} carefully wrapping a small item in plain brown paper on a living room floor, soft daylight",
    "close-up of hands handing over a plain paper shopping bag between two people on a quiet street corner, bright daylight, no logos",
    "a single plain credit card lying face down on a wooden table, close-up, soft light, no logos",
    f"{TE} standing alone on an empty concert stage looking at rows of empty red seats, soft stage light, bright",
    # 월급날·기쁨
    "a grand piano on an empty concert hall stage under warm bright light, red velvet seats in soft focus",
    "audience silhouettes applauding in a bright concert hall, warm light, blurred",
    "view from an airplane window of white clouds and a blue sky, bright daylight",
    f"{AN} smiling with eyes closed on a bright spring sidewalk, cherry blossoms blurred behind, close-up",
    # 잘 살겠습니다
    "a white wedding bouquet of roses on a table, soft window light, close-up",
    "two Korean women with black hair having lunch at a small restaurant table, one talking eagerly, the other forcing a polite smile, plain wall, soft daylight",
    "a small white envelope lying unopened on a desk next to a teacup, soft light, no writing",
    # 새벽의 방문자들
    "a small tidy studio apartment with a single bed and a window, early morning pale light, plain walls",
    "a Korean woman with long black hair sitting on a bed hugging her knees, looking at the door anxiously, pale early morning light",
    "close-up of an apartment front door chain lock, soft morning light",
    # 탐페레 공항
    "a quiet small airport waiting area with large windows and snow outside, bright daylight, nobody around, no signs",
    "a very old Finnish man with white hair and a kind smile in a wool coat sitting by a big airport window, snow outside, bright",
    "a young Korean man with black hair and a backpack sitting next to an old Finnish man at an airport window, both looking at the snow, bright daylight",
    "a snowy runway with a small airplane seen through a big window, bright winter daylight",
    "a young Korean man with black hair reading a handwritten letter at a desk in a small room, the letter seen from behind, soft window light",
    # 다소 낮음 · 후쿠오카 · 도움의 손길 · 첫 출근
    "a young Korean man with messy black hair playing an acoustic guitar beside an old humming white refrigerator in a small apartment kitchen, soft daylight",
    "a small empty live music club stage with a single microphone stand and warm lights, bright",
    "a Korean man and woman with black hair walking along a calm riverside promenade in a Japanese city, seen from behind, bright daylight, no signs",
    "a middle-aged Korean housekeeper with short permed black hair wiping a kitchen counter in a bright new apartment, plain white walls",
    "a spotless bright apartment living room with a sofa and sunlight on the wooden floor, plain walls",
    f"{AN} walking to work on a sunny morning crosswalk holding an iced coffee, people blurred, no signs",
    f"{AN} looking out of an office window at sunset sky, calm faint smile, soft golden light",
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

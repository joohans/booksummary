#!/usr/bin/env python3
"""「시간을 건너는 집」(김하연) Flux 무드 이미지 배치 생성

여름의 하얀 운동화 → 아이들에게만 보이는 낡은 이층집(시간의 집) → 네 중학생(선미·자영·이수·강민)의 일상과 상처
→ 집 안에서 함께하는 밥·케이크·대화 → 계절이 바뀌는 팔월~십이월 → 12월 31일 세 개의 문 → 4년 뒤의 봄.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 간판·교실 칠판·명찰·교복 마크·병원 표지·휴대폰 화면 금지,
실내는 맨벽·나무 바닥, 야외는 골목 담장·강변·하늘. 35mm film still BASE. 밤 장면 금지. 인물마다 「Korean … black hair」.

    SEED_BASE=60000 .venv/bin/python scripts/gen_flux_house.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_House_That_Crosses_Time_flux"))   # 검수 후 옮긴다

BASE = ("35mm film still, gentle magical realism, soft natural daylight, bright enough to see clearly, not dark, "
        "warm pastel palette of cream white, soft sky blue, sage green and honey wood, shallow depth of field, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no numbers, no writing anywhere, no watermark, no signature")

SUNMI = "a tired Korean middle school girl of fifteen with black hair in a low ponytail, in a plain navy cardigan"
JAYOUNG = "a timid Korean middle school girl of fifteen with shoulder-length black hair and bangs, in a plain grey hoodie"
ISU = "a guarded Korean middle school boy of fifteen with messy black hair falling over his eyes, in a plain black jacket"
KANGMIN = "a cheerful Korean middle school boy of fifteen with neat short black hair and a bright smile, in a plain white shirt"
FOUR = ("four Korean middle school kids of fifteen with black hair, two girls and two boys, in plain casual clothes "
        "without any prints")
GRANDMA = "a kind old Korean woman in her seventies with silver hair in a bun, in a soft beige cardigan"

SCENES = [
    # 하얀 운동화
    "a pair of brand-new plain white canvas sneakers without any logos on a wooden floor in a beam of summer sunlight, close-up",
    "a pair of plain white canvas sneakers left on a stone doorstep, summer morning light, shallow depth of field",
    f"{SUNMI} lacing up plain white canvas sneakers, close-up of hands, soft morning light",
    # 시간의 집
    "an old two-story wooden house with a pale green roof standing alone at the end of a quiet hillside lane, summer daylight, slightly dreamlike",
    "an old wooden front door half open with warm golden light spilling out, ivy on the plain wall, soft afternoon",
    "a sunlit old living room with honey wood floors, a worn sofa, lace curtains and a tall grandfather clock, no numbers on the clock face",
    "a wooden staircase leading up to a second floor, dust floating in a beam of sunlight, quiet and mysterious",
    "an antique pocket watch with a blank face and no numbers lying on a lace tablecloth, soft window light, close-up",
    f"{GRANDMA} smiling at the front door of an old wooden house, warm light behind her",
    f"{GRANDMA} pouring barley tea into four cups at a wooden kitchen table, soft light",
    # 선미
    f"{SUNMI} sitting beside a hospital bed holding her sleeping mother's hand, plain white wall, soft window light",
    f"{SUNMI} staring out of a window with tired eyes, rain drops on the glass, soft grey light",
    "a thin woman's hand and a girl's hand holding each other on a white blanket, close-up, soft light",
    # 자영
    f"{JAYOUNG} walking alone along a plain concrete wall with her head down, overcast daylight",
    f"{JAYOUNG} sitting alone on a bench hugging her knees under a big tree, soft daylight",
    f"{JAYOUNG} curled up on her bed facing a plain wall, afternoon light through curtains",
    # 이수
    f"{ISU} sitting on a rooftop ledge looking at the sky, wind in his hair, bright cloudy day, plain rooftop",
    f"{ISU} standing alone under a bridge by a river, hands in pockets, hazy daylight",
    f"{ISU} looking at his own reflection in a puddle, close-up, soft grey light",
    # 강민
    f"{KANGMIN} laughing and waving at the gate of a hillside lane, bright summer light",
    f"{KANGMIN} looking down with a hidden sad expression when no one is watching, soft window light, close-up",
    # 함께
    f"{FOUR} sitting around a wooden dining table eating together and laughing, warm afternoon light in an old house",
    f"{FOUR} sitting on wooden stairs of an old house talking quietly, soft sunlight",
    f"{FOUR} lying on a wooden floor looking up at the ceiling, sunlight patterns, relaxed",
    "a homemade strawberry cream cake with four lit candles on a wooden table, warm light, close-up, no writing on the cake",
    f"{FOUR} around a cake with candles, faces glowing, warm golden light",
    f"{JAYOUNG} and {SUNMI} sharing earphones on a sunny window seat, gentle smiles",
    f"{ISU} quietly handing a plain white sneaker back to {JAYOUNG} on a hillside lane, soft daylight",
    "four pairs of plain white canvas sneakers lined up at the entrance of an old wooden house, close-up, warm light",
    "a stack of plain blank notebooks and a pencil on a wooden desk by a window, soft light, close-up",
    # 계절
    "a quiet hillside lane with low plain walls and a persimmon tree in early autumn, soft afternoon light",
    "ginkgo leaves turning yellow over a quiet hillside lane, bright autumn day",
    "the first light snow falling on the roof of an old wooden house, soft bright winter daylight",
    f"{SUNMI} standing alone on a windy riverside path in winter, from behind, soft bright overcast",
    # 사건
    f"{JAYOUNG} cornered against a plain rooftop wall by shadowy figures, tense, overcast daylight, seen from a distance",
    "a single white sneaker lying abandoned on a grey concrete rooftop, overcast light, close-up",
    f"{ISU} sitting alone on a plain bench in a bare white room, head in his hands, cold daylight",
    # 세 개의 문
    "three tall old wooden doors side by side in a sunlit upstairs hallway, each with a different soft glow, mysterious, symmetrical",
    "a girl's hand reaching for an old brass door handle, soft golden light from the gap, close-up",
    f"{FOUR} standing in front of three tall old wooden doors, seen from behind, soft magical light",
    "an old wooden door opening onto a field of bright white light, dust particles floating",
    # 4년 뒤
    "cherry blossom petals falling over a quiet riverside path in spring, bright soft sunlight",
    "a Korean young woman of nineteen with black hair and a young man with black hair recognizing each other on a cherry blossom path, gentle smiles, spring light",
    "a pair of worn white sneakers on spring grass with cherry blossom petals, close-up, bright soft light",
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
            seed = int(os.environ.get("SEED_BASE", "60000")) + i * 100 + k * 7
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

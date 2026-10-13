#!/usr/bin/env python3
"""「시간을 파는 상점」(김선영) Flux 무드 이미지 배치 생성

2010년대 한국 고등학생 온조 — 알바 실패, 인터넷 상점 개업, 의뢰 셋(PMP 반환·할아버지와 점심·편지 배달), 새벽 옥상.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 화면(노트북·휴대폰)은 뒤에서 보거나 빛만, 시계는 숫자 없는 시계, 교실은 칠판·게시물 없이 창가만.
   간판·교복 명찰·편지 글씨·가게 메뉴판은 전부 글자다 — 화면에 넣지 않는다.
→ 처음부터 밝은 낮빛으로 받는다(밝기 ≥60). 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_timeshop.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-13 /health 로 9010 확인
OUT = Path("assets/images/The_Shop_That_Sells_Time_flux")   # 검수 후 옮긴다

BASE = ("bright cinematic film still, contemporary South Korea 2010s, soft natural daylight, warm peach, mint and cream palette, "
        "gentle film grain, tender coming-of-age mood, shallow depth of field, "
        "no screens with content, no signs, no labels, no posters, no name tags, no books with titles, "
        "no text, no letters, no numbers, no writing anywhere")

SCENES = [
    # 도입 · 시간을 판다
    "close-up of a thoughtful Korean high school girl of seventeen with a ponytail resting her chin on her hand by a sunny window, school uniform without name tag",
    "an antique pocket watch with a plain blank face and no numbers lying open on a wooden desk in warm sunlight, close-up",
    "a teenage girl seen from behind typing on a laptop at her desk at night, the screen only a soft glow, warm desk lamp, cozy small room",
    "many plain clocks without numbers floating softly in a dreamy pastel sky, surreal and gentle",
    # 아빠 · 소방관
    "a firefighter in a helmet and turnout coat walking through bright morning mist, seen from behind, heroic and warm",
    "a faded family photo feeling: a smiling father carrying a little girl on his shoulders in a summer valley with a stream, bright",
    "a mother and teenage daughter sitting close on a small sofa in a modest apartment, warm evening lamp light, tender",
    # 알바 실패
    "a cozy neighborhood bakery interior with trays of fresh bread under warm light, a teenage girl in an apron frowning, no signs",
    "steaming bowls of Vietnamese rice noodle soup on a busy restaurant counter, close-up, warm light",
    "a tired teenage girl in an apron sitting on a back step of a restaurant holding her head, bright afternoon alley",
    # 첫 의뢰 · PMP
    "a row of grey metal school lockers in a sunny empty hallway, one locker slightly open, no labels",
    "close-up of a small black portable media player with a blank dark screen and white earphones lying on a school desk, sunlight",
    "an empty Korean classroom in golden afternoon light with rows of wooden desks and chairs, curtains blowing, no blackboard visible",
    "a teenage girl secretly slipping a small object into a desk drawer in an empty classroom, nervous, sunlit",
    "a group of high school students whispering in a hallway, suspicious glances, bright daylight, uniforms without name tags",
    # 강토 할아버지 · 점심
    "a dignified elderly Korean man with white hair and a calm face sitting at a table in a quiet traditional Korean restaurant, warm light",
    "a beautiful Korean lunch table with rice, soup and many small side dishes in brass bowls, close-up from above, bright",
    "an old man and a teenage girl eating lunch together in silence at a low wooden table, gentle sunlight through paper doors",
    "close-up of an old man's wrinkled hands holding a spoon over a bowl of rice, soft light",
    "an elderly woman alone at the window of an empty apartment looking out, soft lonely afternoon light, seen from behind",
    # 크로노스 · 카이로스
    "a great flowing river of golden light shaped like a spiral of time in the sky over a city at dawn, abstract and luminous",
    "a single dandelion seed floating in a beam of sunlight, frozen moment, close-up, dreamy",
    "an hourglass with glowing pink sand on a windowsill, sunlight behind, close-up, no markings",
    # 편지 배달
    "a teenage girl walking up a quiet hillside lane with a plain blank envelope in her hand, wildflowers along the path, bright spring day",
    "a stack of plain unmarked envelopes tied with a ribbon beside pressed wildflowers on a wooden table, soft light",
    "a small sunny playground of a childcare center with children's shoes lined up at the door, warm and peaceful, no signs",
    "a white birch forest with wind moving through the leaves, bright dappled sunlight",
    # 친구들
    "two teenage girls laughing together on a school rooftop bench under a blue sky, uniforms, carefree",
    "a quiet studious teenage girl wearing big headphones sitting alone on a bench, looking wistful, bright schoolyard",
    "a tall handsome teenage boy in a school uniform standing alone by a window, thoughtful profile, soft daylight",
    "a teenage boy and girl talking on a riverside bench at sunset, warm golden light, seen from behind",
    "a big bear-like kind male teacher with a beard smiling warmly in a sunny school corridor",
    # 위기 · 새벽 옥상
    "a teenage girl running through an empty city street at dawn, pale blue and pink sky, urgent",
    "the flat rooftop of a tall apartment building at sunrise with a railing and a vast pink sky, empty, quiet",
    "two teenagers in casual clothes bursting onto an apartment rooftop at sunrise, breathless, seen from behind",
    "a teenage boy sitting hunched near a rooftop railing at sunrise, alive, a hand reaching to his shoulder",
    "the sun rising over a Korean city skyline with apartment blocks and mountains, warm golden light flooding everything",
    # 바람의 언덕 · 에필로그
    "a grassy hilltop with tall grass bending in the wind under a huge bright sky, three teenagers standing together seen from behind",
    "a teenage girl with her eyes closed and hair blowing in the wind on a hilltop, peaceful smile, golden light",
    "a mother and daughter walking arm in arm along a cherry blossom path in bright spring sunshine, seen from behind",
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
            seed = 83000 + i * 100 + k * 7
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

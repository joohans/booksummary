#!/usr/bin/env python3
"""「제5도살장」(커트 보니것) Flux 무드 이미지 배치 생성

1장 작가의 고백 → 벌지 전투 → 포로 열차 → 드레스덴 제5도살장 지하 → 폭격 → 잿더미 → 에드거 더비의 찻주전자
→ 전후 미국 교외 → 비행접시·트랄파마도어 동물원 → 시간 여행 → 봄, 새 한 마리.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 시력표·열차 표기·군복 휘장·간판은 글자가 붙는다. 「no markings, no insignia」. 거리는 폐허·안개로.
→ 전쟁물이지만 처음부터 밝은 톤(밝기 ≥60). 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_slaughterhouse.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-18 /health 로 9010 확인
OUT = Path("assets/images/Slaughterhouse_Five_flux")   # 검수 후 옮긴다

BASE = ("painterly cinematic film still, 1940s and 1960s, bright soft diffused daylight, "
        "muted wintry blue-grey with warm amber accents, bright enough to see clearly, not dark, "
        "extreme shallow depth of field, soft bokeh, gentle film grain, absurd melancholic and humane mood, "
        "no markings, no insignia, no signs, no logos, no text, no letters, no numbers, no writing anywhere")

SCENES = [
    # 1장 작가 · 소년 십자군
    "a middle-aged writer with a mustache and curly hair typing at a desk by a window, cigarette smoke, thoughtful, close-up",
    "an angry middle-aged woman in a 1960s kitchen glaring at two men drinking at the table, warm light",
    "a group of very young boy soldiers with baby faces in oversized helmets, frightened, close-up, bright overcast light",
    # 빌리 · 벌지 전투
    "a tall skinny awkward young American soldier in a thin coat without a helmet stumbling through a snowy forest, lost, bright winter light",
    "snowy Ardennes forest in winter with tall pine trees and pale fog, quiet, bright",
    "a stocky angry young soldier shouting at a skinny frightened soldier in the snow, close-up",
    "prisoners of war walking in a long line through a snowy field with raised hands, seen from afar, pale winter light",
    "close-up of worn wooden clogs on bleeding feet in the snow",
    # 포로 열차
    "the inside of a crowded wooden freight railway car with prisoners sitting in straw, light through slats, no markings",
    "a long old steam freight train crossing a snowy plain at dawn, seen from afar, no markings",
    # 시간에서 풀려남
    "a man's face dissolving into many overlapping moments of his life, double exposure, surreal, bright",
    "a bewildered man blinking in a doorway that opens from a snowy battlefield into a sunny 1950s living room, surreal",
    "an old clock with melting time flowing like sand, surreal, close-up, bright",
    # 드레스덴 · 제5도살장
    "the baroque domes and spires of old Dresden seen across the Elbe river on a bright winter day, beautiful, no signs",
    "a large old brick slaughterhouse building with a cobblestone yard in winter, empty, no signs",
    "prisoners of war sleeping on straw in an underground meat locker with hooks hanging from the ceiling, dim but readable light",
    "a skinny young prisoner in a tiny ill-fitting coat with a fur collar, absurd and sad, close-up",
    # 폭격
    "a distant city on the horizon glowing with orange fire under a night sky, seen from afar, bright flames",
    "frightened prisoners and guards huddled together in a cellar, dust falling from the ceiling, close-up",
    # 잿더미
    "a vast landscape of white ash and broken stone ruins like the surface of the moon under a pale sky, silent, bright",
    "prisoners digging through rubble with shovels in a ruined city, dust in sunlight",
    "close-up of a dented old teapot lying in grey ash and rubble, soft light",
    "a gentle middle-aged soldier with grey temples holding a teapot, sad calm face, close-up",
    # 전후 미국
    "a quiet 1950s American suburban street with tidy houses and green lawns on a sunny day, no signs",
    "a gentle optometrist in a white coat adjusting eyeglasses on a patient, close-up, warm light, no charts",
    "a 1950s wedding couple posing awkwardly, the groom tall and skinny, the bride plump and smiling, soft light",
    "a small private airplane wreck on a snowy mountain slope, bright winter light, no markings",
    # 트랄파마도어
    "a glowing flying saucer hovering over a suburban backyard at dusk, soft light, cinematic",
    "a transparent geodesic dome in an alien zoo furnished like an ordinary 1960s living room, strange green alien figures watching outside, bright",
    "strange small green alien beings shaped like plumber's plungers with a hand and a single eye, gentle, surreal, bright",
    "a starry cosmic sky with all moments of time shown at once like a mountain range, surreal, luminous",
    # 뭐 그런 거지
    "a lone bare tree in a snowy field with a single bird on a branch, quiet, bright",
    "an old man in a hospital bed looking out the window calmly, soft daylight",
    # 봄 · 새
    "a ruined street in spring with green leaves sprouting from the rubble and sunlight, hopeful",
    "close-up of a small songbird singing on a broken branch in spring sunlight, bokeh",
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
            seed = 79000 + i * 100 + k * 7
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

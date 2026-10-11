#!/usr/bin/env python3
"""「마의 산」(토마스 만) Flux 무드 이미지 배치 생성 (스톡 보충용)

1907~1914년 스위스 다보스의 결핵 요양원 베르크호프에서 보낸 7년.
교훈: 건물 정면·실내 벽은 간판·액자 글씨를 부른다 → 알프스 설경·발코니·얕은 심도 클로즈업 위주.
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 포트는 /generate 1회로 확인
OUT = Path("assets/images/The_Magic_Mountain_flux")   # 스톡 AI 검증이 Flux 까지 깎지 않도록 따로 받아 검수 후 옮긴다

BASE = ("contemplative painterly film still, Swiss Alps around 1910, Belle Epoque, cold clear mountain light, "
        "muted palette of snow white, pine green and pale gold, film grain, very shallow depth of field, background blurred out of focus, "
        "no text, no signs, no letters, no numbers, no writing anywhere, no logos")

SCENES = [
    # 도착
    "a small steam train climbing a narrow mountain railway through snowy alpine gorges, 1907",
    "a young man in a 1900s travelling coat and bowler hat looking out of a train window at towering alpine peaks, wide-eyed",
    "a grand white sanatorium with long balconies on a pine-covered alpine slope above a valley, evening light, seen from far away",
    # 요양원 일상
    "patients wrapped like cocoons in camel-hair blankets lying on deck chairs on a long open balcony facing snowy mountains",
    "close-up of a glass mercury thermometer held between fingers against a blurred alpine window",
    "a long elegant dining hall table set with white linen and silver, sunlight, blurred guests, 1900s",
    "close-up of a young man's hand holding a pocket watch, snowy mountains blurred behind",
    # 쇼샤
    "a slender woman with Kirghiz eyes and reddish hair in a 1910 dress walking through a dining room, a glass door swinging behind her, seen by a young man",
    "close-up portrait of a mysterious Russian woman of 1910 with slanted grey-green eyes, soft light, blurred background",
    "a carnival night in a 1910 sanatorium hall, paper lanterns, masked guests dancing, a young man and a woman talking closely in the shadows",
    "close-up of a small silver pencil being handed from a woman's hand to a man's hand, warm lamplight",
    "close-up of an old glass x-ray plate held up to a window, the ghostly image of ribs and lungs glowing",
    # 요아힘
    "a serious young man in a 1910 military uniform saying goodbye on a snowy railway platform, steam rising",
    "a pale dying young man lying in bed with a soldier's moustache, his cousin sitting beside him holding his hand, soft window light",
    # 세템브리니 · 나프타
    "an elegant Italian man with a black moustache in a worn checked suit gesturing passionately while walking on a snowy mountain path with a young man",
    "a thin sharp-faced man in round glasses and a dark suit arguing intensely, close-up, blurred alpine background",
    "two men arguing on a snowy forest path while a young man between them listens, pine trees, cold breath visible",
    # 눈
    "a lone young man on old wooden skis crossing a vast empty snowfield under a white sky, tiny figure",
    "a blinding alpine blizzard, a small figure struggling through swirling snow, white-out",
    "a man leaning exhausted against the wall of a snowed-in wooden hay hut during a blizzard, eyes closed",
    "a dream vision of a sunny southern seashore with graceful young people and flowers, soft golden light, dreamlike",
    # 페퍼코른
    "a massive old Dutchman with a white lion-like mane and a deeply lined face raising a glass of champagne, candlelight, blurred guests",
    "a group of people around a table at night with champagne glasses and playing cards, candlelight, laughter",
    "a waterfall in an alpine gorge, mist and roaring water, a small group of people watching",
    # 결투
    "two men facing each other with old pistols in a snowy forest clearing at dawn, a young man watching in horror",
    "a pistol fired into the grey sky, smoke, snowy pine trees",
    # 음악 · 시간
    "close-up of a gramophone horn and a spinning shellac record in a dim room, warm light",
    "a linden tree in winter beside a stone well, snow falling, quiet",
    "an hourglass with sand running on a windowsill, snowy mountains blurred behind",
    "the same balcony and deck chairs empty under heavy snow, seasons passing",
    # 전쟁
    "a muddy World War One battlefield in rain, soldiers running through smoke and shell craters, grey",
    "a young soldier in a 1914 German uniform stumbling through mud and rain, singing to himself, seen from behind",
    "a soldier's boot stepping on a hand in the mud, smoke, rain, dark",
    # 덧장면
    "snowy alpine peaks glowing pink at dawn above a sea of clouds",
    "a dark pine forest with deep snow and soft blue light at dusk",
    "a warm lit sanatorium window at night seen from the snowy slope, solitary",
    "close-up of a red cheek and a feverish young man's face wrapped in a blanket, cold air",
    "a young man reading a thick botany book under a lamp on a balcony at night, stars over the mountains",
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
    base, scenes, tag = BASE, SCENES, "f"
    OUT.mkdir(parents=True, exist_ok=True)
    made = 0
    t0 = time.time()
    for i, scene in enumerate(scenes, 1):
        prompt = f"{base}. {scene}"
        for k in range(per):
            seed = 53000 + i * 100 + k * 7
            img = generate(prompt, seed)
            if not img:
                continue
            path = OUT / f"mood_{tag}{i:02d}_{k+1}.jpg"
            path.write_bytes(img)
            made += 1
            print(f"[{made}] {path.name}  ({time.time()-t0:.0f}s)  {scene[:50]}", flush=True)
    print(f"\n✅ {made}장 생성 / {time.time()-t0:.0f}초", flush=True)


if __name__ == "__main__":
    main()

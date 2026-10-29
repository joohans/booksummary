#!/usr/bin/env python3
"""「망원동 브라더스」(김호연) Flux 무드 이미지 배치 생성

망원동 8평 옥탑방 → 무명 만화가 영준 · 캐나다에서 혼자 돌아온 기러기 아빠 김 부장 · 이혼 통보받은 스토리 작가 싸부
· 공무원 수험생 삼척동자 → 마트 빨리 먹기 대회·TV → 집주인 할아버지와 손자 → 망원시장·한강 → 추석 술판
→ 콩나물해장국집 · 화재 구조 · 선화와 웹툰.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — ⚠️ 현대 한국+가게·간판·시장은 거의 다 폐기(10/14).
→ 시장은 음식 클로즈업으로만, 간판·화면·책장 금지. 인물마다 「Korean … black hair」 명시. 35mm 사진풍 BASE(서명 0 실측).
★ 배경은 장면별로만(BASE 금지). 밤 장면 금지(b<60). 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_mangwon.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Mangwon_dong_Brothers_flux"))   # 검수 후 옮긴다

BASE = ("35mm contemporary film still, warm natural daylight, bright enough to see clearly, not dark, "
        "soft warm palette of sunlit beige, faded green, sky blue and warm grey, shallow depth of field, gentle film grain, "
        "wry, warm, slightly comic everyday mood, no screens, no signboards, no signs, no logos, no labels, no text, no letters, no numbers, no writing anywhere")

YJ = "a Korean man in his mid thirties with messy black hair and stubble, wearing a faded t-shirt"
KB = "a chubby Korean man in his forties with short black hair and a tired kind face, wearing a wrinkled polo shirt"
SB = "a thin Korean man in his late fifties with grey-streaked black hair and a scruffy beard, wearing an old cardigan"
SC = "a skinny Korean man in his twenties with black hair and glasses, wearing a grey hoodie"
SCENES = [
    # 옥탑방
    "a small rooftop room on top of an old low-rise Korean residential building, green plastic water tank, potted plants, clothes drying on a line, bright summer sky",
    "rooftop view over a quiet neighborhood of low brick houses in summer daylight, hazy blue sky, rooftops only",
    f"{YJ} lying on a floor mattress in a tiny cluttered rooftop room, staring at the ceiling, plain wall, summer daylight",
    f"close-up of {YJ} sketching with a pencil on blank white paper at a low table, plain wall behind, soft window light",
    "close-up of pencils, erasers and blank white drawing paper scattered on a low wooden table, soft daylight",
    # 김 부장
    f"{KB} standing at a rooftop door holding a big travel suitcase, looking awkward, bright daylight",
    f"{KB} sitting alone on a plastic stool on a rooftop, looking at a small framed family photo turned away from camera, quiet sadness, daylight",
    "a single large suitcase standing in the corner of a small plain room, soft daylight",
    # 싸부
    f"{SB} with a flushed drunk face leaning on a rooftop railing at dusk-like golden afternoon light, laughing",
    f"{SB} sitting cross-legged on a floor, gesturing passionately while explaining a story idea, plain wall, warm daylight",
    # 빨리 먹기 대회
    "close-up of a big bowl of noodles and chopsticks on a plain table at an eating contest, steam, blurred crowd behind",
    f"{KB} and {SC} side by side eating noodles furiously at a long table, cheeks full, blurred crowd, bright daylight",
    f"{SC} raising both arms in victory with a big plain cardboard box, blurred crowd cheering, bright daylight",
    # 삼척동자
    f"{SC} carrying a big plain cardboard box up an outdoor concrete staircase to a rooftop, sweating, bright daylight",
    f"{SC} studying with a thick blank-covered workbook on a small folding table on a rooftop, earnest face, daylight",
    "four Korean men of different ages sitting on a floor in a tiny rooftop room, eating instant noodles from a shared pot, laughing, plain walls, warm daylight",
    "four pairs of mismatched slippers lined up at the door of a tiny room, close-up, soft daylight",
    # 집주인 할아버지와 석이
    "a stern Korean grandfather in his seventies with white hair and a cane standing on a rooftop, scolding, bright daylight",
    "a Korean teenage boy with dyed brown hair and headphones around his neck, sulky face, sitting on concrete stairs, daylight",
    # 다툼·실패
    f"{YJ} and {KB} arguing in a tiny room, pointing at each other, comic mood, plain wall, daylight",
    f"{KB} sitting on a park bench with his head in his hands, blurred trees, daylight",
    "a pile of crumpled papers beside a wastebasket on a wooden floor, close-up, soft light",
    # 망원시장 (음식 클로즈업만)
    "close-up of fresh vegetables, peppers and cabbages piled on a traditional market stall, warm daylight, shallow depth of field, no signs",
    "close-up of hot fried snacks and skewers on a market stall tray, steam, warm light, no signs",
    "close-up of a paper bag of warm croquettes held in a hand, warm daylight, no logos",
    # 한강
    "the wide Han River in Seoul under a soft golden late afternoon sky, people jogging on a riverside path, far away, bright",
    "four Korean men of different ages walking along a riverside path under a soft golden afternoon sky, seen from behind",
    "four Korean men of different ages sitting on a riverside grassy bank with canned drinks, sunset glow, seen from behind, bright warm light",
    "close-up of a plastic bag of convenience store snacks and canned beer on grass, warm afternoon light, no logos",
    # 추석
    "close-up of Korean holiday food on a low table: jeon pancakes, songpyeon rice cakes, fruit, warm light",
    "four Korean men of different ages sharing holiday food and drinks around a low table on a rooftop, warm golden light, laughing",
    "a full round harvest moon rising over rooftops in a pale blue early evening sky, bright",
    # 사랑·선화
    f"a Korean woman in her early thirties with shoulder-length black hair, wearing a simple blouse, smiling shyly on a quiet residential street, daylight",
    f"{YJ} and a Korean woman with shoulder-length black hair sharing an umbrella on a quiet alley, light rain, bright overcast day",
    f"{YJ} and a Korean woman with shoulder-length black hair sitting at a small café table by a window, talking, soft daylight",
    # 해장국집
    "close-up of a steaming bowl of Korean bean sprout hangover soup with rice, warm light",
    f"{KB} wearing a white apron, stirring a big steaming pot in a small restaurant kitchen, proud smile, plain tiled wall, warm light",
    "a small busy Korean soup restaurant with people eating at simple tables, blurred, warm daylight, no signs",
    # 화재 구조
    "grey smoke rising from a window of a low-rise residential building, firefighters far away, bright daylight",
    f"{SB} with a soot-smudged face helping a Korean woman and a young girl down outdoor stairs, dramatic but bright daylight",
    f"{SB} standing in front of a lecture room whiteboard that is completely blank, teaching, students blurred, daylight",
    # 결말
    f"{YJ} drawing comic panels with a pen on blank paper, focused smile, close-up, morning light",
    "the empty tiny rooftop room tidied up, morning sunlight pouring through the window, plain walls",
    "four Korean men of different ages standing together on a rooftop looking at the morning sky, seen from behind, hopeful bright light",
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

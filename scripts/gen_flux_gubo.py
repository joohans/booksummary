#!/usr/bin/env python3
"""「소설가 구보씨의 일일」 Flux 무드 이미지 배치 생성 (스톡 보충용)

1934년 여름, 스물여섯 살 소설가 구보의 경성 하루(정오~새벽 두 시) → 장면을 Flux 로 채운다.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 1930년대 서울 도심은 간판 시대다(천변풍경 폐기율 54%). 가게·역·전차 **바깥 정면**은 그리지 않고
   **실내**(다방·전차 안·대합실·카페·방)와 **인물 뒷모습·하늘·비·밤길**로 간다. 도시 배경이라 장면 수를 1.5배로 잡는다.
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 포트는 /generate 1회로 확인(2026-10-08 9010 정상)
OUT = Path("assets/images/A_Day_in_the_Life_of_Kubo_the_Novelist_flux")   # 스톡 AI 검증이 Flux 까지 깎지 않도록 따로 받아 검수 후 옮긴다

BASE = ("melancholy painterly film still, Seoul (Gyeongseong) in the summer of 1934, modernist mood, "
        "soft natural light, muted sepia, slate blue and warm ochre palette, film grain, quiet lonely atmosphere, "
        "no text, no signboards, no shop signs, no banners, no posters, no letters, no writing, no numbers")

SCENES = [
    # 집 · 어머니
    "an old Korean mother in a white hanbok sewing alone on the wooden floor of a traditional house, looking toward the gate with quiet worry",
    "a young man in a 1930s straw boater hat and round glasses, holding a walking stick, stepping out through a wooden middle gate of a hanok, seen from behind",
    "an empty neat bedding laid out on the floor of a small room at midnight, a lamp still lit, a wall clock, an old mother sitting beside it",
    # 한낮 거리 · 다리
    "a thin young man in a white linen suit, round glasses and a walking stick standing alone at the corner of a small stone bridge at noon, hesitating, harsh summer sun",
    "a lonely young man walking along a wide dusty 1930s boulevard under a glaring summer sky, his long shadow on the ground, seen from behind",
    "a dizzy young man pressing his hand to his forehead under the bright noon sun on a city street, blurred passersby",
    # 화신상회 · 승강기
    "a young Korean couple with a small child in 1930s modern clothes waiting happily before an ornate brass elevator door inside a department store",
    "a solitary young man in glasses watching a brass elevator door close inside an art deco department store lobby",
    # 전차
    "interior of a 1930s Seoul tram car, wooden seats and hanging straps, summer light through windows, a young man in glasses standing alone in the corner",
    "a young woman with a parasol sitting by a tram window, seen in profile, a young man in glasses stealing a glance from a distance",
    "five old copper coins lying in an open palm, close-up, warm light",
    "a young woman with a parasol stepping down from a tram onto a platform island, the tram pulling away",
    # 다방 오후
    "interior of a dim 1930s Seoul tea room, rattan chairs, a gramophone, young men in suits smoking listlessly, tired eyes, cigarette haze",
    "a young man in round glasses alone at a corner table in a dim 1930s tea room with a cup of black tea and a cigarette, lost in thought",
    "a small dog lying on its side on the wooden floor of a 1930s tea room, half-closed lonely eyes",
    "a gramophone with a spinning record on a wooden counter in a 1930s cafe, warm lamp light",
    # 회상 · 소년기
    "a fifteen-year-old boy blushing at the doorway of a hanok while a lovely older girl in hanbok greets him on a summer evening",
    "a boy secretly reading an old storybook by candlelight under a quilt at night",
    # 대한문 · 남대문
    "an old palace gate under a pale summer sky, a nearly empty plaza, a small lonely figure in a white suit",
    "a few porters with wooden A-frame carriers resting idly in the shade of an old stone city gate on a still hot afternoon",
    # 경성역 대합실
    "a crowded third-class railway waiting room in the 1930s, people in hanbok and western clothes sitting with bundles, nobody talking, high arched windows",
    "an exhausted old woman in a faded hanbok sitting on a bench in a railway waiting room, empty eyes",
    "a single peach rolling across a cement floor of a railway station, a young mother with a baby on her back hesitating",
    "two idle men in worn panama hats and linen coats standing by a ticket gate, scheming expressions, 1930s",
    "a vulgar smiling man flaunting a gold pocket watch, a pretty young woman beside him, a thin man in glasses looking away uneasily",
    # 친구 · 황혼
    "two young men in suits laughing at a tea room table, one robust, one thin with round glasses, soda water and tea",
    "five red apples arranged in a row on a wooden cafe table, close-up",
    "a city crossroads at golden dusk in 1930s Seoul, people heading home, a young man in glasses standing still among them",
    "two friends parting at dusk, one boarding a tram, the other left standing alone on the street",
    # 동경 회상
    "a Tokyo coffee shop in autumn in the 1930s, a young Korean student in glasses picking up a dropped notebook from under a corner table",
    "a young man and a young Japanese-style dressed woman in a 1930s cloche hat walking together shyly on a Tokyo street on a Sunday",
    "a young woman in a raincoat without umbrella walking away alone down a rainy evening street, shoulders drooping, wet hair, seen from behind",
    "a young man and a young woman walking in silence in a misty rainy park at dusk, heads bowed",
    # 저녁 · 밤
    "a steaming bowl of Korean beef bone soup on a wooden table in a humble 1930s eatery, two friends eating",
    "a young man kicking pebbles on a wide empty boulevard at night, lonely, streetlights",
    "two little children happily holding a large watermelon each, a young man in glasses smiling at them under a street lamp at night",
    "a telegraph delivery boy on a bicycle speeding down a dark quiet street at night",
    "two men walking silently along a dim tree-lined street at night, a cloudy starless sky",
    # 카페 · 새벽
    "interior of a 1930s cafe at night, waitresses in modern dresses sitting with two young men at a table with beer bottles, warm lamp light, smoke",
    "a young man in glasses writing in a notebook at a cafe table at night while waitresses laugh around him",
    "rain streaming down a cafe window at night, blurred warm lights outside",
    "a wide city crossroads at two in the morning, fine rain, wet pavement reflecting lamps, a few tired people walking home",
    "a young man in glasses walking home alone in fine rain at night without an umbrella, quickening his steps, seen from behind",
    "a light still glowing in the window of a small hanok at night in the rain, a mother waiting inside",
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


# 2차(--set 2): 1차 88장 중 약 70%가 간판·현판·벽 글씨로 폐기 → 건물·벽 장식을 아예 화면에서 뺀다.
#   클로즈업·인물 뒷모습·하늘·비·맨벽 실내만. BASE 에서도 도시 이름을 뺐다(지명이 간판을 부른다).
BASE2 = ("melancholy painterly film still, summer 1934, East Asian modernist era, soft natural light, muted sepia, "
         "slate blue and warm ochre palette, film grain, quiet lonely atmosphere, plain bare walls with nothing hanging on them, "
         "no text, no signs, no frames, no calligraphy, no posters, no letters, no numbers, no writing anywhere")

SCENES2 = [
    "close-up of an old Korean mother's wrinkled hands sewing white cloth with needle and thread, warm window light",
    "an old woman in a white hanbok dozing with her head on her arm on a bare wooden floor at night, a single oil lamp",
    "close-up of a pair of worn leather shoes and a wooden walking stick on the stone step of a traditional house",
    "a thin young man in a white linen suit and straw boater hat, seen from behind, standing alone under a huge pale summer sky with towering clouds",
    "a young man in round glasses and white linen suit squinting up at the blazing summer sun, close-up portrait, sweat on his brow",
    "close-up portrait of a pale melancholy young Korean man in round wire glasses, 1930s haircut, looking out a window, soft light",
    "a young man's hand holding a closed plain notebook and a walking stick, close-up, linen suit sleeve",
    "the inside of a brass elevator cage closing, warm golden light, art deco grille pattern, nobody inside",
    "close-up of a young woman's gloved hands resting on a closed parasol on her lap, 1930s summer dress",
    "a tram window with summer scenery blurring past, a young man's reflection faintly in the glass",
    "a cup of black tea and a cigarette in a glass ashtray on a small round marble table, smoke curling, dim light",
    "rattan chairs and small round tables in a dim empty tea room with plain walls, afternoon light through a curtain",
    "an old wind-up gramophone with a large brass horn playing a record, close-up, warm lamp light, dark background",
    "close-up of a gold pocket watch dangling on a chain from a man's vest pocket, smug posture",
    "a glass of iced milky drink and a dish of ice cream on a cafe table, 1930s, soft light",
    "a crowd of travelers in hanbok sitting silently on long wooden benches under high arched windows, seen from behind, light beams",
    "an old weary woman in a faded white hanbok, close-up portrait, deep wrinkles, empty distant eyes",
    "a ripe peach lying alone on a grey cement floor, soft light, shallow depth of field",
    "two young men laughing together at a small table, one robust and one thin with round glasses, dim warm light, plain wall behind",
    "five red apples on a white plate on a marble table, still life, soft window light",
    "silhouettes of people walking home along a wide road at golden dusk, long shadows, a lone figure standing still",
    "a young Korean student in glasses picking up a dropped notebook from a wooden floor under a cafe table, autumn light",
    "close-up of a nail clipper beside a cup of coffee on a wooden table, autumn afternoon light",
    "a young woman in a 1930s cloche hat and coat walking beside a shy young man in glasses along a tree-lined autumn path",
    "a young woman in a beige raincoat without umbrella walking away down a rainy park path at dusk, wet hair, drooping shoulders, seen from behind",
    "a young man in glasses standing alone in the rain watching a distant figure disappear, misty dusk, puddles",
    "two bowls of steaming milky Korean beef bone soup on a simple wooden table, rice, kimchi, warm light",
    "a young man in a white suit kicking a pebble on a wide empty dark road, lonely, single streetlamp glow",
    "two small children in 1930s clothes hugging large striped watermelons and grinning, under a warm street lamp at night",
    "a young man walking alone on a dark tree-lined road at night under a cloudy sky, the faint glow of a lamp",
    "warm-lit interior of a 1930s cafe at night, young women in modern dresses with short wavy hair laughing around a table with beer glasses, smoke, plain walls",
    "close-up of a fountain pen writing in a small notebook on a cafe table at night, beer glass beside it, blurred laughing figures",
    "a sweet young cafe girl of sixteen with dimples smiling shyly at a table, warm lamp light, 1930s bob haircut",
    "an elegant woman over forty in white mourning hanbok standing alone on a dark rainy street at night, dignified sad face",
    "fine rain falling at night over a wide empty crossroads, wet asphalt reflecting warm lamps, a few tired figures in the distance",
    "a young man in glasses walking briskly home in fine night rain without umbrella, hands in pockets, seen from behind, wet pavement",
    "a single warm lit paper window of a small tiled-roof house at night in the rain, the silhouette of an old mother waiting inside",
    "close-up of a small open notebook page with a single large hand-drawn X mark in ink, nothing else on the page",
]

def main() -> None:
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    second = "--set" in sys.argv and sys.argv[sys.argv.index("--set") + 1] == "2"
    base, scenes, tag = (BASE2, SCENES2, "g") if second else (BASE, SCENES, "f")
    OUT.mkdir(parents=True, exist_ok=True)
    made = 0
    t0 = time.time()
    for i, scene in enumerate(scenes, 1):
        prompt = f"{base}. {scene}"
        for k in range(per):
            seed = (43000 if second else 41000) + i * 100 + k * 7
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

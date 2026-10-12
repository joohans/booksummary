#!/usr/bin/env python3
"""「서울, 1964년 겨울」 Flux 무드 이미지 배치 생성

1964년 겨울밤 서울 — 포장마차, 중국집, 불구경, 여관, 이튿날 아침 눈. 세 남자의 하룻밤을 Flux 로 채운다.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 1960년대 서울 도심은 간판·네온 시대다. 가게 정면·백화점·거리 원경은 그리지 않고
   처음부터 **얕은 심도 클로즈업 · 인물 뒷모습 · 눈 · 불빛 보케 · 맨벽 실내**로 간다
   (마의 산·소유냐 존재냐에서 이 방식으로 글자 폐기 0).
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_seoul1964.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-12 /health 로 9010 확인
OUT = Path("assets/images/Seoul_Winter_1964_flux")   # 스톡 AI 검증이 Flux 까지 깎지 않도록 따로 받아 검수 후 옮긴다

BASE = ("melancholy painterly film still, a winter night in the mid 1960s, East Asian city, cold blue and amber palette, "
        "soft film grain, very shallow depth of field, background completely blurred into soft bokeh, lonely quiet atmosphere, "
        "plain bare walls with nothing hanging on them, "
        "no text, no signs, no signboards, no neon letters, no posters, no calligraphy, no letters, no numbers, no writing anywhere")

SCENES = [
    # 포장마차
    "two young men in 1960s winter coats sitting side by side at a small street food tent at night, steam rising, seen from behind, warm lamp glow",
    "close-up of skewers of small roasted sparrows on a charcoal grill, sparks, steam, night",
    "close-up of two small glasses of clear soju on a worn wooden counter, a kerosene lamp glowing behind, bokeh",
    "close-up portrait of a young Korean man in thick black-rimmed glasses and a wool coat, breath visible in the cold, thoughtful eyes",
    "close-up portrait of a plain young Korean man in a worn overcoat with tired eyes, looking down at his drink, warm lamp light",
    "a housefly resting on the rim of a glass, extreme close-up, soft warm light",
    # 비밀 자랑 — 밤 풍경(원경 금지, 불빛만)
    "a row of street lamps receding into a snowy night, one lamp dark among the lit ones, very blurred background",
    "three softly glowing windows high on a dark wall at night, everything else dark, snowflakes falling",
    "a tram trolley pole touching an overhead wire and throwing a bright blue spark against the dark night sky, close-up",
    "a man's thumbnail pressing a mark into a painted wooden door handle, extreme close-up",
    "a young man counting bricks on a plain dark wall at night with his eyes, seen from behind, cold breath",
    # 사내의 등장 · 중국집
    "a weary man in his mid thirties in a shabby overcoat and old hat, close-up portrait, sad hollow eyes, stubble, warm dim light",
    "three men sitting around a small round table in a humble eatery with plain walls, steaming dishes, quiet heavy mood, warm light",
    "close-up of a bowl of black bean noodles and a pot of tea on a wooden table, steam, warm dim light",
    "close-up of a trembling hand holding a thin bundle of old paper money, no printing visible, shadows",
    "close-up of a man covering his face with both hands at a table, shoulders hunched, dim warm light",
    # 귤 · 넥타이
    "a small pile of bright tangerines in a paper bag under a lamp at night, cold blue background bokeh",
    "a man peeling a tangerine with cold fingers on a snowy night street, close-up, breath steam",
    "close-up of a new striped necktie being held up in a man's hand, soft lamp light, blurred background",
    # 소방차 · 불구경
    "the red glow of a large fire lighting up the night sky behind dark rooftops, sparks flying, smoke, seen from a distance",
    "three men in winter coats standing still and watching a fire at night, seen from behind, faces lit orange",
    "close-up of a man's face lit by orange firelight, tears in his eyes, mouth open as if calling out",
    "a white handkerchief bundle flying through the air into roaring flames, sparks, night",
    "a crowd of silhouettes watching a burning building at night, orange glow, smoke, nobody helping",
    "a red fire engine rushing through a dark snowy street at night, motion blur, headlights, no lettering",
    # 월부 책값 · 골목
    "a man in an old overcoat knocking on a plain wooden gate in a dark narrow alley at night, seen from behind, a single bare bulb",
    "a narrow dark alley in winter at night, snow on the ground, a single bare light bulb, nobody there",
    "three men walking slowly down a dark empty snowy street at night, seen from behind, long shadows",
    # 여관
    "a long dim corridor of a cheap old inn with sliding paper doors, warm weak light, nobody there",
    "close-up of a hand writing in a guest register with a pen, the page blurred and unreadable, dim lamp",
    "a small bare inn room with a thin folded blanket and a water kettle on the floor, single bulb, plain walls",
    "a man sitting alone in the dark of a small inn room, back against a plain wall, knees drawn up, faint light from the door",
    "two closed sliding paper doors side by side in a dark corridor, light behind one of them",
    "a young man lying under a thick blanket in a dark room, eyes open, staring at the ceiling",
    # 아침
    "pale grey winter dawn light through a frosted paper window, an empty room, quiet",
    "a few ants crawling on a bare wooden floor near a man's shoe, extreme close-up",
    "two young men in winter coats hurrying out of a narrow alley in the early morning, seen from behind, snow beginning to fall",
    "a young man in black-rimmed glasses standing alone under bare tree branches as snow falls, seen from a distance, grey morning",
    "close-up of two men's hands shaking in the cold, coat sleeves, falling snowflakes",
    "a young man stepping onto an old 1960s bus in the snowy morning, seen from behind, fogged windows",
    "snow falling quietly on bare tree branches against a grey sky, close-up, melancholy",
    "a lone figure in a long coat walking away down a wide snowy road in the grey morning, footprints behind him",
]


# 2차(--set 2): 1차 84장은 「1960s East Asian city night」가 **가짜 한자 네온 간판**을 거의 모든 컷에 끌어들였다
#   (글자 없는 컷 약 20장). 도시·거리라는 말을 빼고 **가게 없는 눈 골목·맨 콘크리트 벽·단색 어둠 배경 클로즈업·실내**만 쓴다.
BASE2 = ("melancholy painterly film still, a cold snowy winter night long ago, cold blue and amber palette, soft film grain, "
         "very shallow depth of field, plain dark background, quiet lonely atmosphere, "
         "no shops, no storefronts, no neon, no illuminated signs, no signboards, no posters, no banners, "
         "no text, no letters, no characters, no calligraphy, no numbers, no writing anywhere")

SCENES2 = [
    "two young men in winter coats sitting on stools under a canvas tent flap, warm kerosene lamp light, steam, plain dark night behind them",
    "close-up of a small charcoal brazier glowing orange with skewers roasting, sparks rising into pure darkness",
    "close-up of two small glasses and a green glass bottle on a rough wooden plank, warm lamp glow, black background",
    "close-up portrait of a young man in thick black-rimmed glasses and a dark wool coat, breath steaming, pure black background, warm side light",
    "close-up portrait of a tired plain young man in a worn overcoat looking down, warm lamp side light, pure dark background",
    "a quiet snowy lane between plain grey concrete walls at night, a single bare street lamp, snow falling, nobody there",
    "a single street lamp glowing in falling snow against a dark sky, close-up, snowflakes in the light",
    "a blue electric spark flashing on an overhead wire against a black night sky, snow falling",
    "close-up of a weary middle-aged man in an old felt hat and shabby coat, sad hollow eyes, stubble, warm dim light, plain dark wall",
    "three men in winter coats sitting around a small round table with steaming bowls, a plain bare wall, a single hanging bulb, heavy silence",
    "close-up of a steaming bowl of noodles with black sauce and chopsticks on a wooden table, warm dim light, dark background",
    "close-up of a man's hands covering his face, dim warm light, dark background",
    "close-up of a paper bag of bright tangerines on snow, night, soft warm light",
    "close-up of cold red hands peeling a tangerine in the snow, steam of breath, dark background",
    "close-up of a striped necktie draped over a man's hand, warm lamp light, dark background",
    "huge orange flames and sparks rising into a black night sky, smoke, seen over a dark snowy wall",
    "three men in long winter coats seen from behind standing in the snow, faces lit by a distant orange fire glow, dark night",
    "close-up of a man's tearful face lit by orange firelight, mouth open calling out, smoke drifting, dark background",
    "a small white cloth bundle tumbling into roaring orange flames, sparks bursting, dark background",
    "a man in an old overcoat standing before a plain wooden gate in a snowy lane at night, a single bare bulb above, seen from behind",
    "three men walking slowly side by side down a snowy lane between plain walls at night, seen from behind, long shadows from one lamp",
    "a dim narrow corridor with sliding paper doors and a worn wooden floor, weak warm light, nobody there",
    "a small bare room with a thin folded blanket on the floor and a brass kettle, a single bare bulb, plain paper walls",
    "a man sitting alone on the floor of a small dark room against a plain paper wall, knees drawn up, faint light from a crack in the door",
    "a young man lying under a thick quilt in a dark room, eyes open, staring at the ceiling, faint blue light",
    "pale grey dawn light through a frosted paper window, an empty bare room, quiet",
    "a few ants on worn wooden floorboards near the toe of a leather shoe, extreme close-up, grey morning light",
    "two young men in winter coats hurrying out of a snowy lane in grey early morning, seen from behind, plain walls",
    "a young man in black-rimmed glasses standing alone under bare snowy tree branches, falling snow, grey morning, open empty field behind",
    "close-up of two hands shaking in the cold, coat sleeves, falling snowflakes, grey background",
    "snow falling quietly on bare black tree branches against a pale grey sky",
    "a lone figure in a long coat walking away along a wide snowy empty road under a grey sky, footprints behind him",
    "close-up of falling snowflakes and the warm blur of a single lamp, night, abstract",
    "close-up of a shabby black leather bag of books on snow, night, warm lamp light",
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
    second = "--set" in sys.argv and sys.argv[sys.argv.index("--set") + 1] == "2"
    base, scenes, tag = (BASE2, SCENES2, "g") if second else (BASE, SCENES, "f")
    OUT.mkdir(parents=True, exist_ok=True)
    made = 0
    t0 = time.time()
    for i, scene in enumerate(scenes, 1):
        prompt = f"{base}. {scene}"
        for k in range(per):
            seed = (66000 if second else 64000) + i * 100 + k * 7
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

#!/usr/bin/env python3
"""「괭이부리말 아이들」 Flux 무드 이미지 배치 생성 (스톡 보충용)

1990년대 말 인천 만석동 바닷가 달동네의 아이들 이야기 → 장면을 Flux 로 채운다.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 학교 교실(칠판)·구치소·교회·가게·현수막은 빼고, 아이들·골목 계단·지붕·바다·부두·불빛만 그린다.
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).
"""
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

FLUX = "http://192.168.0.150:9010/generate"   # 포트는 /health 로 확인(2026-10-07 9010 정상)
OUT = Path("assets/images/The_Children_of_Gwaengiburimal_flux")   # 스톡 AI 검증이 Flux 까지 깎지 않도록 따로 받아 검수 후 옮긴다

BASE = ("warm realistic painterly film still, Incheon South Korea in the late 1990s, a poor seaside hillside neighborhood "
        "of small slate- and tin-roofed houses near the harbor and factories, soft natural light, muted teal and warm amber palette, "
        "film grain, tender and hopeful mood, no text, no signboards, no banners, no letters, no writing, no posters")

SCENES = [
    # 괭이부리말
    "a hillside neighborhood of tiny houses by the sea with harbor cranes and factory chimneys in the distance, late afternoon",
    "a narrow winding alley with concrete steps between low houses, laundry hanging, children's sandals by a door",
    "stacked coal briquettes beside a small blue door in winter, a cat sleeping on top",
    "a stray cat sitting on a low wall overlooking the grey sea and a small harbor",
    # 숙자와 숙희
    "eleven-year-old Korean twin girls with identical bob haircuts in 1990s clothes, one sweeping the yard, the other daydreaming at the gate",
    "a girl of eleven cooking rice on a small gas burner in a tiny kitchen while her twin sister reads comics on the floor",
    "a tired young Korean mother, visibly pregnant, sitting on a low step with her twin daughters leaning on her",
    "a dockworker in a work jacket and helmet riding a small motorcycle along a harbor road at dusk",
    "the harbor at dawn, stacks of pulp bales and a crane, empty and silent, grey sky",
    # 동수·동준·명환
    "a fourteen-year-old Korean boy with tired eyes sitting alone on concrete stairs at night, hood up",
    "two teenage boys slumped against a wall in a dark alley, one holding a crumpled plastic bag, a man's shadow approaching",
    "a younger boy of ten standing at an open door at night waiting, worried face, a bare light bulb",
    # 영호
    "a sturdy young Korean man in his twenties in work clothes carrying a sleeping teenage boy on his back up alley stairs at night",
    "a small house interior at night: a young man, two teenage boys and a younger boy sharing ramen and kimchi around a low table, warm light",
    "a young man in a construction helmet at a building site at dawn, the sea behind, determined",
    # 명희 선생님
    "a young Korean female teacher in her twenties in a 1990s cardigan standing at the top of the neighborhood stairs, looking down with mixed feelings",
    "a young female teacher and a stocky young man talking on a seawall at sunset, serious conversation",
    "a young female teacher sitting with a teenage boy on a bench by the harbor, listening to him",
    # 변화 · 호용
    "a teenage boy in a factory work uniform walking home at dusk with a schoolbag over his shoulder, whistling",
    "a teenage boy kneading bread dough in a small bakery kitchen, flour on his hands, proud smile",
    "a small hungry boy of eight in a too-big jacket standing in falling snow at a door on Christmas Eve, warm light from inside",
    "a crowded warm room at night with a young man, a young woman, a mother with a baby, twin girls and boys making kimchi together",
    "a young woman carrying boxes up narrow stairs into a tiny attic room with a small window overlooking the sea",
    # 희망
    "children running down the alley stairs in the morning toward the sea, sunlight breaking through clouds",
    "the hillside neighborhood at sunrise, golden light over the rooftops and the harbor, seagulls",
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
            seed = 37000 + i * 100 + k * 7
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

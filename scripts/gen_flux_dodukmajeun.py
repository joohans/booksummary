#!/usr/bin/env python3
"""「도둑맞은 가난」 Flux 무드 이미지 배치 생성 (스톡 보충용)

1970년대 서울 판자촌의 여공 이야기는 무료 스톡에 거의 없다 → 장면을 Flux 로 채운다.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 핵심 소재가 「공장」「통장」「판자촌 골목」이지만 간판·통장 지면·공장 표어·벽면 가득한 실내는 뺀다.
   Flux 는 인물·연탄·냄비·지붕·골목 계단·창밖 불빛만 그린다.
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).
"""
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

FLUX = "http://192.168.0.150:9010/generate"   # 포트는 /health 로 확인(2026-10-06 9010 정상)
OUT = Path("assets/images/Stolen_Poverty_flux")   # 스톡 AI 검증이 Flux 까지 깎지 않도록 따로 받아 검수 후 옮긴다

BASE = ("realistic painterly film still, Seoul in the mid 1970s, a crowded hillside shantytown of tin and board shacks, "
        "muted grey-brown and cold blue palette with warm coal-fire glow, film grain, quiet, proud and melancholy mood, "
        "no text, no signboards, no slogans, no letters, no writing, no posters, no calendars, no newspapers")

SCENES = [
    # 판자촌 · 가족
    "a hillside of tightly packed tin-roofed shacks at dusk, thin smoke rising from chimneys, seen from a distance",
    "a narrow steep alley with stone steps between shacks at night, a single bare bulb",
    "cylindrical coal briquettes stacked by a low wooden door in winter, frost on the ground",
    "a glowing coal briquette in a small iron stove, close-up, red embers in the dark",
    "an empty small room at dawn with folded bedding and a cold stove, eerie stillness",
    "a young Korean woman in plain 1970s work clothes standing alone at a shack door looking down at the city lights",
    # 나 · 가난은 소명
    "a young woman factory worker in a 1970s uniform and headscarf walking home up a hillside alley at dusk, determined face",
    "rows of young women at sewing machines in a dim factory hall, seen from behind, overhead lamps",
    "a young woman eating a simple meal of rice and dried anchovies alone on a low table in a tiny room, lamplight",
    "a dented aluminum pot boiling on a small coal stove, steam, close-up",
    # 상훈과의 동거
    "a young Korean man and woman in 1970s work clothes sitting side by side on a low step outside a shack, sharing a cigarette-free quiet moment, shy smile",
    "a young couple sharing one quilt beside a small coal stove in a cramped room, winter night, warm glow",
    "a young man in work clothes looking at a bowl of dried anchovies on a low table with a strange, uncomfortable expression",
    "a small bankbook-shaped cloth pouch tucked under a folded quilt, close-up, no writing",
    "a young woman angrily turning away from a young man in a tiny room, tension",
    "a young woman sitting alone on the threshold of a shack at night waiting, empty alley",
    # 대학생으로 돌아온 상훈
    "a clean-cut young man in a crisp white shirt and pressed trousers standing awkwardly in a muddy shantytown alley, out of place",
    "a well-dressed young man lecturing a seated young woman in a shabby room, she stares at the floor",
    "a large wealthy Western-style house with a garden and iron gate on a sunny hill, 1970s, seen from far below",
    "a young woman pushing a well-dressed young man out of a low doorway, fierce expression",
    # 도둑맞은 가난
    "a rain-stained old wooden chest with one side sagging, in a dim corner, close-up",
    "a battered vinyl suitcase with a broken zipper on a worn floor mat",
    "a stack of dented aluminum bowls and pots on a shelf, harsh light revealing every scratch",
    "a young woman sitting alone in a bare shabby room in harsh daylight, hugging her knees, ashamed",
    "the lights of a modern 1970s city at night seen from a dark hillside shantytown, a lone figure on the edge",
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
            seed = 36000 + i * 100 + k * 7
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

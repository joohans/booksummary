#!/usr/bin/env python3
"""「욕망이라는 이름의 전차」(테네시 윌리엄스) Flux 무드 이미지 배치 생성

1947년 뉴올리언스, 블랑시·스탠리·스텔라·미치. 종이 등, 하얀 옷, 포커의 밤, 생일 저녁, 정신병원 의사.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 위저드 베이커리(10/14) 2차 방식: 얕은 심도 · 민무늬 벽 · 클로즈업. 거리·가게 정면 금지.
→ 전차 행선지판·트럼프 카드 숫자·맥주병 라벨·버스표·신문은 전부 글자다. 카드는 뒷면만, 병은 무지, 표는 백지.
→ 폭력 장면은 그리지 않는다. 처음부터 밝은 톤. 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_streetcar.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-13 /health 로 9010 확인
OUT = Path("assets/images/A_Streetcar_Named_Desire_flux")   # 검수 후 옮긴다

BASE = ("1940s cinematic film still, humid New Orleans summer, extreme shallow depth of field, soft creamy bokeh, "
        "plain faded plaster walls, warm amber light with soft teal shadows, gentle film grain, sultry melancholy mood, "
        "no signs, no posters, no labels, no playing card faces, no newspapers, no tickets with print, "
        "no text, no letters, no numbers, no writing anywhere")

SCENES = [
    # 도착
    "a delicate blonde woman in her thirties in a white summer dress and white gloves holding a small suitcase, standing uncertainly, soft bokeh",
    "close-up of a woman's gloved hand holding a worn leather suitcase handle, warm light",
    "an old wooden streetcar passing in a soft blur of afternoon light, side view only, no destination sign, motion blur",
    "a narrow wooden staircase leading up the outside of an old shabby two-story house, wrought iron railing, humid afternoon, no signs",
    # 벨 리브
    "a grand white southern plantation mansion with columns, overgrown and decaying, under a hazy sky, oak trees with spanish moss",
    "spanish moss hanging from old oak trees in golden haze, melancholy",
    "a faded silk dress and pearls spilling out of an open steamer trunk, close-up, warm light",
    # 스탠리
    "a muscular dark-haired young man in a sweat-stained bright T-shirt, cocky expression, close-up portrait, warm harsh light",
    "a young man's hands tearing through papers and silk clothes in an open trunk, close-up, aggressive",
    "a young pregnant woman with brown hair in a simple cotton dress smiling tenderly, soft window light",
    # 포커의 밤
    "men's hands around a round table under a single hanging bulb, cards held face down, cigarette smoke, green felt, close-up",
    "a plain old radio on a windowsill in warm lamplight, close-up",
    "a young woman descending a wooden staircase at night toward a man on his knees, warm light from above, emotional",
    # 종이 등 · 환상
    "a bare light bulb covered with a delicate paper lantern casting soft colored light, close-up, plain wall",
    "a woman's hand gently placing a paper lantern over a bare light bulb, close-up",
    "a woman in a white robe sitting in a steamy claw-foot bathtub, seen from behind, soft warm haze, modest",
    "a woman's face reflected in an old mirror, powdering her cheek, soft dim light, close-up",
    "a white moth fluttering near a warm light in darkness, close-up",
    "a woman in a white dress dancing alone to imagined music in a dim room, soft blur, dreamy",
    # 미치 · 고백
    "a shy broad-shouldered man in his thirties in a plain suit holding a hat, gentle eyes, soft bokeh",
    "a man and a woman sitting close on a dark porch at night, soft warm light from a window, intimate conversation, seen from behind",
    "a young man with a gentle face in 1930s clothes, soft dreamy portrait, faded like a memory",
    "a dance floor in a dim casino with blurred couples and a polka band, warm haze, memory",
    "close-up of a woman's tearful eyes in soft lamplight, regret",
    # 폭로 · 생일
    "a man reading a plain blank sheet of paper with a cruel smile, close-up, warm harsh light",
    "a birthday cake with candles on a small kitchen table, one empty chair, warm dim light",
    "a small blank paper envelope being slid across a table toward a woman's hand, close-up",
    "a torn paper lantern hanging from a bare glaring light bulb, harsh light, close-up",
    "a man standing in a doorway with harsh light behind him, face in shadow, menacing silhouette",
    # 결말
    "a hospital-like dim corridor seen through a doorway, soft focus, ominous stillness",
    "close-up of a woman's gloved hand resting gently on a stranger's arm, soft light",
    "a doctor in a dark suit gently offering his arm, seen from behind, soft hazy light",
    "a young woman cradling a newborn baby and weeping, soft window light",
    "a vase of fading white flowers on a table in a dim room, still life, melancholy",
    "a misty street at dawn with an old streetcar's lights disappearing in fog, side view, no signs",
    "rain on a window at night with blurred warm lights, jazz mood, melancholy",
    "a trumpet player's silhouette in a smoky blue haze, close-up, blues mood",
    "magnolia blossoms in soft humid morning light, close-up",
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
            seed = 87000 + i * 100 + k * 7
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

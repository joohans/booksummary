#!/usr/bin/env python3
"""「당신들의 천국」 Flux 무드 이미지 배치 생성

스톡 80장 중 29장이 지중해 마을·HDR 일몰·관광 요트라 폐기했다(1960~70년대 한국 섬은
무료 스톡에 없다). 실사 51 + Flux 29 로 채운다. → [[project_image_pool_double]]

⛔ 글자는 소재로 막는다 ([[project_flux_text_problem]]) — 동상 비문·간판·현판·표지판을
   장면에서 뺀다. 동상은 **빈 받침대**나 뒷모습으로만 그린다.
★ 저장은 반드시 mood_*.jpg ([[project_render_image_order]])
"""
import base64, json, sys, time, urllib.request
from pathlib import Path

FLUX = "http://192.168.0.150:9010/generate"   # 포트는 매번 /health 로 확인
OUT = Path("assets/images/Your_Paradise")

BASE = ("cinematic film still, 1960s South Korean island, overcast grey-blue palette, "
        "cold sea light, desaturated, 35mm film grain, quiet solemn mood, "
        "documentary realism, no text anywhere")

SCENES = [
    # 간척 — 이 작품의 중심 사건
    "a long line of Korean men in worn work clothes carrying stones on wooden A-frame carriers across a tidal flat",
    "Korean laborers waist deep in grey seawater passing rocks hand to hand, overcast sky",
    "an unfinished stone embankment stretching into a grey sea, low tide",
    "close-up of cracked worn hands gripping a wet stone",
    "wooden A-frame carriers left standing on a mudflat at dusk, nobody around",
    "a crowd of villagers seen from behind watching the sea from a raw earth embankment",
    "a breach in a half-built sea wall with water rushing through, grey daylight",
    "an exhausted Korean man sitting alone on a pile of stones, head down, sea behind him",
    # 섬·병원
    "a low single-story brick hospital ward on a windswept island, 1960s, empty yard",
    "a long empty corridor of an old island infirmary, pale light from high windows",
    "rows of identical low buildings behind a stone wall on an island hillside",
    "an iron gate in a stone wall separating a pine grove from a compound",
    "a pine grove bent by sea wind on a rocky island slope",
    "a stone path climbing between low walls toward the sea",
    "an empty stone pedestal on a bare hilltop overlooking the sea",
    "a wooden boat arriving at a small island jetty, few figures waiting",
    "a bare flagpole on an island parade ground, overcast",
    "the seawall promenade of an island village at dusk, one figure walking",
    # 사람
    "a Korean man in a plain military-style jacket standing alone facing the sea, seen from behind",
    "a middle-aged Korean doctor in a white coat standing in a doorway of an old ward, dim interior",
    "an elderly Korean man with a walking stick standing on a rocky shore, white traditional clothes",
    "two Korean men talking on a stone embankment, distance between them, grey sea behind",
    "a young Korean woman in a white jeogori standing at a window looking out at the sea",
    "a small group of islanders gathered in silence on a dirt yard, seen from a distance",
    "a Korean bride and groom in simple 1960s clothes standing awkwardly side by side outdoors",
    # 상징
    "reeds bending flat in strong sea wind under a grey sky",
    "a single wooden boat pulled up on a stony shore, no people",
    "rain falling on grey seawater, close-up",
    "a narrow wooden pier disappearing into fog over the sea",
]


def generate(prompt: str, seed: int) -> bytes | None:
    body = json.dumps({"prompt": prompt, "width": 1920, "height": 1080,
                       "steps": 4, "seed": seed}).encode()
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
    made, t0 = 0, time.time()
    for i, scene in enumerate(SCENES, 1):
        for k in range(per):
            img = generate(f"{BASE}, {scene}", i * 1000 + k * 7)
            if not img:
                continue
            path = OUT / f"mood_flux_{i:02d}_{k+1}.jpg"
            path.write_bytes(img)
            made += 1
            print(f"[{made}] {path.name} ({time.time()-t0:.0f}s) {scene[:50]}", flush=True)
    print(f"\n✅ {made}장 생성 / {time.time()-t0:.0f}초")


if __name__ == "__main__":
    main()

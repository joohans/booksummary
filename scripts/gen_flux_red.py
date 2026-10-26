#!/usr/bin/env python3
"""「빨강의 자서전」(앤 카슨) Flux 무드 이미지 배치 생성

신화 프롤로그: 붉은 섬·붉은 소 떼·헤라클레스의 과업(도기 그림은 그리스 문자가 붙으니 금지).
현대 운문 소설: 어깨에 작은 빨간 날개를 단 소년 게리온 → 형의 그늘·어머니 → 자서전(공책 뒷면만)
→ 소년 헤라클레스와의 사랑·이별 → 카메라·사진 → 부에노스아이레스 재회(거리 대신 실내·창가) → 페루 안데스·앙카시
→ 새벽 화산으로 날아오르는 게리온.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]). ★ 배경은 장면별로만(BASE 금지, 초정리 편지 10/21).
→ 남미 도시 거리·간판은 빼고 하늘·산·실내·클로즈업. 밤 장면 금지(지구 끝의 온실 10/22 b<60) — 화산 불빛도 「bright morning」.
→ 산출물은 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_red.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-19 /health 로 9010 확인
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Autobiography_of_Red_flux"))   # 검수 후 옮긴다

BASE = ("quiet literary film still, soft natural daylight, bright enough to see clearly, not dark, "
        "muted pastel palette of warm red, soft volcanic grey and pale sky blue, extreme shallow depth of field, soft bokeh, gentle film grain, "
        "tender, lyrical, melancholy yet luminous mood, no signboards, no signs, no logos, no labels, no text, no letters, no numbers, no writing anywhere")

GB = "a boy with red skin tone and small red feathered wings"
SCENES = [
    # 신화
    "a small rocky island in a calm blue Atlantic sea under bright daylight, red cliffs, seen from afar",
    "a herd of red cattle grazing on a green island meadow by the sea, bright daylight",
    "a muscular ancient Greek hero wearing a lion skin walking along a rocky shore, seen from behind, bright daylight, painterly",
    "close-up of a single red feather lying on white sand, bright daylight",
    # 소년 게리온
    f"{GB} of about six sitting alone on a rocky beach, small red wings folded on his back, looking at the sea, bright daylight",
    f"{GB} of about six hiding behind a wooden door, only his eyes and the tip of a red wing visible, soft daylight",
    "a gentle mother with warm smile kneeling to button a little boy's coat in a sunny kitchen, the boy's small red wings peeking out, soft light",
    "the shadow of a tall older boy falling across a wooden floor of a bedroom, a small child's toy marbles scattered, soft afternoon light",
    f"close-up of a child's hands holding a pencil over a notebook seen from the blank back cover, soft window light, no writing",
    f"{GB} of about ten lying on a bed writing in a notebook, the notebook seen from behind, small red wings, soft daylight",
    # 헤라클레스
    f"{GB} of fourteen with small red wings under a jacket, shy, at a crowded small-town bus stop, soft daylight, blurred people, no signs",
    "a confident handsome teenage boy of sixteen with tousled dark hair and a leather jacket, smiling, bright daylight, close-up",
    f"two teenage boys sitting on the hood of an old car on an empty country road at golden afternoon, laughing, one with small red wings",
    "two teenage boys lying in tall summer grass looking at the sky, bright daylight, tender",
    "a dark dormant volcano seen across green fields in bright daylight, two small figures in the foreground",
    f"{GB} of fourteen standing alone in a field, the other boy walking away in the distance, overcast soft light, heartbreak",
    # 사진
    "close-up of an old film camera held by young hands, soft daylight",
    "black-and-white photographs drying on a line in a small room, images blurred, soft red safelight mixed with daylight from a window",
    f"a young man with small red wings under a coat photographing a quiet sea through a camera, bright daylight",
    "a long exposure photograph look of waves on a rocky shore, soft mist, bright daylight",
    # 부에노스아이레스
    f"a young man of twenty-two with small red wings hidden under a long coat sitting in a sunlit café by a large window, alone, close-up, blurred background, no signs",
    "two young men meeting again in a sunlit hotel lobby, surprised, blurred background, no signs",
    "a handsome young Peruvian man with long black hair and a gentle face, close-up portrait, soft daylight",
    "three young men walking together across a wide sunlit plaza, seen from behind, blurred, no signs",
    "view from an airplane window over white clouds and the Andes mountains, bright daylight",
    # 페루
    "the snowy peaks of the Andes above a green valley in bright morning light",
    "a narrow mountain road winding through the Peruvian Andes, an old car far away, bright daylight",
    "a young Peruvian man gently touching a red feather on another young man's shoulder blade, soft light, close-up, tender",
    "a small rural Andean village with adobe houses under a bright blue sky, no signs",
    "a young man with small red wings sitting on a hotel bed, looking out the window at mountains, contemplative, soft daylight",
    # 화산과 비상
    "a smoking volcano with a faint orange glow at its crater under a bright pale morning sky, Andes",
    f"a young man with large red wings spread wide standing on a mountain ridge at bright sunrise, seen from behind, majestic",
    "a figure with red wings flying high toward a volcano in a bright morning sky, small in the frame, cinematic",
    "close-up of red wings against a bright sky, feathers glowing in sunlight",
    "three young men standing together watching a distant volcano's glow from a hillside in bright early morning light, seen from behind",
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

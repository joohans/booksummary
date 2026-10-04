#!/usr/bin/env python3
"""「숙영낭자전」 Flux 무드 이미지 배치 생성 (스톡 63장 보충용)

글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 이 작품의 핵심 소재가 「불태워진 책」「일기장 뒷면」「실록」이지만
   책·일기·두루마리·문서·현판·비석은 장면에서 아예 뺀다. Flux 는 인물·공간·저승만 그린다.
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).
"""
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

FLUX = "http://192.168.0.150:9010/generate"   # 포트는 /health 로 확인(2026-09-29 9010 정상)
OUT = Path("assets/images/The_Tale_of_Lady_Sukyeong")

BASE = ("cinematic painterly film still, Joseon Korea in the 1400s, Andong in Gyeongsang province, "
        "soft moonlight and candlelight, misty indigo and warm ivory palette, film grain, sorrowful romantic mood, "
        "no text, no signboards, no hanging plaques, no inscriptions, no calligraphy, no banners")

SCENES = [
    # 천상 인연 · 꿈
    "a celestial fairy woman in flowing white and jade hanbok descending through moonlit clouds, ethereal glow",
    "a young Joseon scholar asleep at a low desk by candlelight, a translucent fairy woman appearing beside him in a dream",
    "a hidden valley of jade-green ponds and pink blossoms deep in misty mountains, otherworldly paradise",
    "a young scholar lying sick on a quilt, staring at a painted portrait of a beautiful woman hung on a plain wall, candle",
    "a pair of small golden child figurines on a low wooden table beside a candle, dim room",
    "a lovesick young man in white hanbok walking alone along a mountain path toward distant mist",
    "a young man and a fairy woman meeting under a blossoming tree beside a jade pond, mist, tender",
    # 혼인 · 행복
    "a young Joseon couple in fine hanbok walking hand in hand through a sunlit hanok courtyard garden",
    "a young mother in hanbok holding a baby with a little girl beside her on a wooden veranda, warm afternoon",
    "a family of four in a lamplit hanok room at night, children sleeping, peaceful",
    # 과거길 · 밤
    "a young man in travel clothes looking back with longing at a woman standing at a hanok gate at dawn",
    "a young man climbing over a low earthen wall at night under the moon, urgent",
    "a lamplit paper-screen window at night with two shadow silhouettes inside, seen from a dark courtyard",
    "an old Joseon nobleman with a cane standing in a dark courtyard listening at a paper door, suspicious face",
    # 모함
    "a jealous young maidservant in plain hanbok peering from behind a pillar in the dark, cunning eyes",
    "a maidservant handing a pouch of coins to a rough man in a dark alley at night",
    "a shadowy man leaping over a courtyard wall at night, an old man with a raised sword chasing, moonlight",
    "servants holding torches crowding a hanok courtyard at night, tense commotion",
    "a young woman in white hanbok with loose long hair kneeling on the stone ground of a courtyard at night, bound, servants around",
    "an old mother-in-law in hanbok weeping and embracing a kneeling young woman in a courtyard at night",
    # 옥비녀 · 자결
    "a young woman throwing a jade hairpin high into the night sky, moonlight, dramatic",
    "a jade hairpin stuck upright deep in a stone step, glowing faintly in moonlight, close-up",
    "an old nobleman in bare socks rushing down stone steps to clasp a young woman's hands in remorse, night",
    "a young mother giving a white folding fan to her small daughter by candlelight, tears, intimate",
    "a single candle burning beside an empty silk quilt in a dark room, sorrowful stillness",
    "a little girl crying beside a covered figure on a bed, holding her baby brother, dim dawn light",
    # 귀향 · 파랑새
    "a young official in red robes on horseback riding hurriedly along a country road at dusk",
    "a young man kneeling in grief beside a figure covered with white silk in a candlelit room",
    "a small bright blue bird bursting upward from a dim room into the moonlight, feathers glowing",
    "two blue birds circling above a hanok courtyard at night under a full moon",
    "a maidservant kneeling in fear before a furious young man in red official robes, torches, night",
    # 재생 · 결말
    "a young woman in white rising and waking with a gentle glow in a candlelit room, miracle, soft light",
    "a radiant heavenly court in the clouds, a jade emperor figure on a throne of light, distant and luminous",
    "a happy reunion in a sunlit courtyard, a young couple embracing, children running to them",
    "a gentle young bride in hanbok bowing with a young wife beside her, harmony, spring blossoms",
    "an old Joseon king receiving a petition from a young official in a grand hall, warm lantern light",
    "a large joyous family feast in a hanok courtyard with many children and grandchildren, autumn",
    "three elderly figures in white robes ascending into luminous clouds, auspicious light, a dragon in the clouds",
    "a misty Andong river village at dawn with tiled roofs and a winding river, peaceful",
    "white plum blossoms on a branch against a moonlit sky",
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
            seed = 33000 + i * 100 + k * 7
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

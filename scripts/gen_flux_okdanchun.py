#!/usr/bin/env python3
"""「옥단춘전」 Flux 무드 이미지 배치 생성 (스톡 57장 보충용)

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
OUT = Path("assets/images/The_Tale_of_Ok_Danchun")

BASE = ("cinematic painterly film still, late Joseon Korea (17th century), Pyongyang by the Taedong river, "
        "spring, willows and mist, soft teal and warm lantern palette, film grain, emotional dramatic mood, "
        "no text, no signboards, no hanging plaques, no inscriptions, no banners")

SCENES = [
    # 두 정승 · 태몽 · 맹세
    "a blue dragon coiling through five-colored clouds above a misty river at dawn, chasing a white tiger toward the water",
    "a white tiger leaping across a wide river and falling into dark water, a blue dragon above in storm clouds",
    "two young Joseon boys in blue hanbok studying side by side at a low wooden desk in a sunlit village schoolroom, brush and inkstone, no visible writing",
    "two teenage Joseon scholars clasping hands in a solemn vow under an old pine tree, mountains behind",
    "two old Joseon ministers lying ill in separate candlelit rooms, family kneeling in sorrow",
    # 혈룡의 가난
    "a poor young Joseon man in worn white hanbok cutting off his own long hair with a small knife in a bare thatched hut",
    "a young Joseon wife folding her red wedding robe to sell, sad face, poor hut, morning light",
    "an old mother in white hanbok and a young wife waving goodbye at a broken twig gate as a man walks away with a bamboo staff",
    "a lone traveler with a bamboo staff and straw sandals walking a long dusty mountain road, vast landscape",
    "a ragged man in only torn undergarments begging at the closed red gate of a provincial government compound, stern gate guards",
    "a starving ragged man sitting alone on a riverbank stone at dusk, wide river and willow trees",
    # 첫 연광정 잔치 · 대동강
    "a grand riverside pavilion on a cliff above the Taedong river, a lavish feast with many dancers in colorful hanbok, seen from far below on the water",
    "a drunken Joseon governor in red official robes and black hat laughing at a feast table full of dishes, gisaeng around him",
    "a ragged beggar dragged by his topknot by officers and forced to kneel before a feast table",
    "a bound young man in rags lying in a small wooden boat on a wide misty river, two boatmen rowing",
    "a beautiful gisaeng in pale jade hanbok quietly pressing coins into a boatman's hand behind a willow tree",
    "a man lying on a sandy riverbank half covered with sand at dusk, willows, river mist",
    "a young woman in pale jade hanbok kneeling on a sandy shore at sunset, offering a bowl of rice gruel to an exhausted man",
    # 옥단춘의 집
    "a neat small hanok courtyard at night full of blooming flowers and a white crane under the moon",
    "a lamplit hanok room with paper-screen windows, a gisaeng pouring wine into a cup for a tired young man",
    "a gisaeng in hanbok playing a geomungo zither alone on a wooden veranda under a spring moon",
    "a young woman in hanbok packing a cloth travel bundle for a man at dawn, tender farewell at a hanok gate",
    # 서울 · 과거
    "a young scholar entering a clean tiled-roof hanok gate in Seoul, servants bowing, his old mother rushing out in joy",
    "a vast crowd of Joseon scholars in white robes and black hats at a royal examination ground before a palace",
    "a Joseon king on a throne handing three sealed envelopes to a kneeling young official in red robes, dim grand hall",
    "a young royal inspector in disguise in ragged clothes hiding a bronze horse token under his coat, night road",
    # 두 번째 잔치 · 출도
    "a gisaeng combing and tying the topknot of a ragged man after a bath, lamplight, tender scene",
    "a second spring feast at the cliff pavilion, officials of many towns, music and dancers, lanterns lit at dusk",
    "a young woman in white hanbok and a man in rags tied together in a small boat on the river, boatmen hesitating, a drum on the cliff above",
    "a large barrel drum being struck on a riverside cliff at dusk, drummer silhouette, tension",
    "a young woman pulling her skirt over her head, about to jump from a boat into the river, a man grabbing her hand",
    "dozens of runners in dark uniforms rushing down to the river shouting, raising clubs, chaos at a feast",
    "officials fleeing in panic from a riverside feast, overturned tables, a man riding a horse backwards, comic chaos",
    "a terrified governor in red robes tumbling down wooden pavilion steps, hat falling off",
    "a royal inspector in red official robes seated in judgement on a pavilion terrace, a governor bound and kneeling below",
    # 천벌 · 결말
    "a single bolt of lightning striking a small boat in the middle of a dark river, violent storm, spray",
    "a calm Taedong river at sunrise after a storm, an empty drifting boat, willows",
    "a new governor in red robes greeting townspeople warmly in a sunlit courtyard, people bowing in gratitude",
    "a Joseon family gathered in a grand hanok hall, an old mother, a wife and a gisaeng in fine robes, peaceful warm light",
    "two figures in hanbok walking together along a willow-lined riverbank in spring sunlight",
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
            seed = 31000 + i * 100 + k * 7
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

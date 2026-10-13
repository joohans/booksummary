#!/usr/bin/env python3
"""「숙향전」 Flux 무드 이미지 배치 생성

월궁선녀 숙향이 인간 세상에 내려와 다섯 살에 부모를 잃고, 짐승·용녀·화덕진군·마고할미의 도움으로
살아남아 천상배필 이선과 맺어지는 이야기 → 자연·동물·꿈·선계 장면이 대부분이다.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 관아·누각·저잣거리 건물은 현판 글씨가 붙는다(배비장전). 건물은 초가·울타리·창살 클로즈업만,
   나머지는 인물·동물·자연·구름·물·불길.
→ 렌더러가 이미지를 어둡게 처리하므로 처음부터 **밝은 낮·새벽빛**으로 받는다
   (서울 1964년 겨울: 밝기 30~46 컷이 거의 검게 나와 렌더 1회 버림).
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).

    .venv/bin/python scripts/gen_flux_sukhyang.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 2026-10-12 /health 로 9010 확인
OUT = Path("assets/images/The_Tale_of_Suk_Hyang_flux")   # 검수 후 옮긴다

BASE = ("luminous painterly film still, Joseon dynasty Korean folk tale, bright soft daylight, pale jade, peach blossom pink "
        "and warm gold palette, gentle mist, dreamy and tender atmosphere, shallow depth of field, "
        "no buildings with signs, no text, no letters, no calligraphy, no seal stamp, no numbers, no writing anywhere")

SCENES = [
    # 천상 · 적강
    "a celestial maiden in flowing pale silk hanbok floating among bright clouds under a huge pale moon at dawn, ribbons drifting",
    "a young celestial maiden and a young immortal in white robes laughing playfully on a cloud bridge in the bright sky",
    "a celestial maiden descending through soft golden clouds toward green mountains far below, sad expression",
    # 김전 · 거북
    "a kind young scholar in a white robe releasing a large old turtle back into a clear river from a fisherman's net, morning light",
    "a large turtle swimming beneath a man carried by a flooding river, bright water spray, rescue",
    "a Korean couple in hanbok praying before a stone pagoda in a sunny mountain valley, incense smoke",
    "a mother in hanbok holding a newborn baby girl wrapped in silk, soft window light, joyful tears",
    # 피란 · 실종
    "a crowd of refugees in white hanbok fleeing along a dusty mountain road under a bright hazy sky, bundles on their backs",
    "a little five-year-old Korean girl in a tiny pink hanbok sitting alone under a big tree on a hillside, crying, bright afternoon",
    "a rough bandit with a kind face gently lifting a small crying girl onto his shoulders on a sunny forest path",
    "a white crane spreading its wings over a small sleeping girl in a meadow to shade her from the sun",
    "two monkeys bringing fruit to a small girl sitting in a sunny forest clearing",
    "magpies circling over a small girl walking alone through tall grass under a blue sky",
    "a small girl riding on the back of a gentle spotted deer through a bright birch forest",
    # 장 승상 댁 · 사향
    "an elderly noble couple in silk hanbok smiling warmly at a graceful young girl bowing to them in a sunny courtyard with plain walls",
    "a beautiful teenage girl in hanbok embroidering at a low table by a paper lattice window, bright soft light",
    "a jealous maid servant in hanbok peeking from behind a wooden pillar with a scheming smile, bright courtyard",
    "a young woman in hanbok weeping as she leaves through a plain wooden gate, falsely accused, bright day, seen from behind",
    # 투신 · 용녀
    "a young woman in white hanbok standing at the edge of a wide river at dawn, about to throw herself in, mist on the water",
    "a dragon maiden with pearl hair ornaments rising from shimmering river water and catching a falling girl, glowing bubbles",
    # 갈대밭 불 · 화덕진군
    "a young woman trapped in a vast reed field as orange fire spreads around her, bright smoke, golden light",
    "an old fire spirit with a red beard and flowing red robes carrying a young woman on his back through flames, protective",
    # 마고할미
    "a kindly old grandmother with white hair in a plain hanbok reaching out her hand to a starving young woman on a mountain path, morning light",
    "an old grandmother and a young woman sitting together in a small thatched cottage yard among apricot blossoms, warm sunlight",
    "close-up of hands embroidering a silk cloth with colorful thread, a scene of immortals in clouds taking shape, bright window light",
    # 꿈 · 요지연
    "a dream banquet of immortals on a jade terrace above the clouds, peach trees in bloom, musicians, soft radiant light",
    "a young woman asleep on a sleeping mat, a glowing dream of clouds and immortals swirling above her",
    "a finished embroidered silk scroll of clouds, cranes and immortals laid out on a wooden table, bright light",
    # 이선
    "a handsome young scholar in a blue robe and gat hat gazing in astonishment at an embroidered silk cloth, sunlit study with plain walls",
    "a young scholar on horseback traveling along a winding river road through spring mountains, searching",
    "a young scholar bowing respectfully before an old grandmother at a cottage gate among blossoms",
    "a young bride and groom in red and green wedding hanbok shyly facing each other in a simple cottage room, candlelight and morning light",
    # 이 상서 · 처형 위기
    "a stern elderly high official in a dark official robe and hat frowning, seated, plain background",
    "a young woman in white hanbok kneeling in a bright prison yard with wooden bars, calm and dignified",
    "a jailer raising a wooden paddle whose arm suddenly freezes in midair, astonished face, bright courtyard",
    "a middle-aged magistrate in official robes hesitating, tears in his eyes, looking at a kneeling young woman",
    "a mother in hanbok waking from a dream in tears at dawn, soft light through a paper window",
    # 통곡 · 재회
    "a young woman weeping beside a small shaggy dog under a willow tree by a stream, soft afternoon light",
    "a young scholar returning home on horseback in a flower procession after passing the state exam, joyful",
    "an elderly couple tearfully embracing a grown daughter in a bright courtyard of blossoming plum trees",
    # 선약 · 승천
    "a young man climbing toward a misty magical mountain of jade peaks and waterfalls in search of a herb of immortality",
    "a couple in shining white robes ascending into the sky on clouds with cranes, golden light, peaceful",
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
            seed = 71000 + i * 100 + k * 7
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

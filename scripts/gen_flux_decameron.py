#!/usr/bin/env python3
"""「데카메론」(조반니 보카치오) Flux 무드 이미지 배치 생성

1348년 흑사병의 피렌체(텅 빈 골목·버려진 사람들) → 성당의 일곱 여인과 세 청년 → 토스카나 언덕 위 별장 → 정원·분수·월계관·왕과 여왕
→ 백 편의 이야기(거짓 고해의 사기꾼·술탄과 멜키세데크의 세 반지·리자베타의 바질 화분·페데리고의 매·조난자와 상자·수도원 정원·통 속의 남편·
칼란드리노의 돌·그리셀다) → 피렌체로 돌아가는 열 사람.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 필사본·책상·문서·현판·프레스코 근접 금지, 사람·자연·정원 위주.
★ 35mm period film still BASE(삽화풍은 모서리 서명). 배경은 장면별로만. 밤 장면 금지(밝기 ≥60). 노출·선정성 금지.

    .venv/bin/python scripts/gen_flux_decameron.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Decameron_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still, 14th century Tuscany, soft natural daylight, bright enough to see clearly, not dark, "
        "warm palette of terracotta, olive green, cream linen, deep red and sky blue, shallow depth of field, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no inscriptions, no writing anywhere, no watermark, no signature")

WO = "young Italian noblewomen in long flowing 14th century gowns of soft colors, braided hair with flower wreaths"
MEN = "young Italian noblemen in 14th century tunics and hose"
W1 = "a young Italian noblewoman in a long rose-colored 14th century gown, braided auburn hair"
M1 = "a young Italian nobleman in a dark green 14th century tunic, short dark curly hair"

SCENES = [
    # 1 흑사병의 피렌체
    "a deserted narrow cobblestone alley in a medieval Tuscan town, closed wooden shutters, scattered straw, eerie silence, pale overcast daylight",
    "a wooden handcart with shrouded bundles left on an empty medieval street, overcast daylight, somber",
    "a frightened medieval Italian family hurrying away down a dusty road carrying bundles, overcast morning",
    "a sick man in a linen shirt lying on straw in a bare stone room, a woman covering her mouth with a cloth at the door, soft window light",
    # 2 성당에서 만난 열 사람
    f"seven {WO} gathered and whispering together inside a vast bare stone church nave, sunbeams through tall windows",
    f"three {MEN} entering a sunlit stone church doorway, the young women turning to look",
    # 3 언덕 위의 별장으로
    f"a small group of {WO} and {MEN} riding horses up a winding road through Tuscan hills with cypress trees, bright morning",
    "a beautiful villa of pale stone with a loggia on a green Tuscan hilltop surrounded by cypress and olive trees, bright spring day",
    "rolling green Tuscan hills with cypress rows and vineyards under a clear blue sky, wide view",
    # 4 정원과 왕관
    f"{WO} and {MEN} sitting in a circle on the grass of a walled garden beside a stone fountain, telling stories, dappled sunlight",
    f"close-up of a laurel wreath being placed on the head of {W1}, garden background, soft light",
    f"{M1} playing a lute in a sunny garden while young women in medieval gowns listen and smile",
    "a marble fountain with clear water in a garden of roses and orange trees, sunlight sparkling",
    f"{WO} dancing in a ring holding hands on a green lawn, bright afternoon",
    "a long table under a pergola with white linen, bread, fruit and wine jugs, Tuscan garden, bright midday",
    f"{W1} and {M1} walking along a shaded garden path between cypress trees, talking and laughing",
    # 5 이야기들 — 거짓 고해와 성인
    "an old cunning Italian man on his deathbed confessing piously to a kindly elderly friar in a brown robe, soft window light, bare stone room",
    "a crowd of medieval villagers kneeling and reaching to touch a funeral bier carried by friars, bright daylight, square of plain stone",
    # 세 반지
    "a medieval sultan in silk robes and turban sitting on cushions in a sunlit arched hall of plain stone, questioning an old bearded merchant",
    "close-up of three identical gold rings resting on a dark velvet cloth in soft light",
    "an old bearded Jewish merchant in a long robe gesturing calmly while explaining, warm light, plain wall behind",
    # 리자베타의 바질
    "a sorrowful young Italian woman in a plain medieval dress embracing a large terracotta pot of green basil by a window, soft daylight",
    "close-up of a lush basil plant growing in an old terracotta pot on a stone windowsill, sunlight",
    # 페데리고의 매
    "a poor young Italian knight in a worn tunic holding a peregrine falcon on his gloved hand, rustic farm courtyard, bright day",
    "a noble lady in an elegant medieval gown visiting a humble stone farmhouse, the poor knight bowing, sunlight",
    "close-up of a peregrine falcon perched on a leather glove, sharp eyes, soft background",
    # 조난자와 상자
    "a shipwrecked man clinging to a floating wooden chest in a calm blue sea, bright daylight",
    "a medieval merchant ship with square sails on a sparkling Mediterranean sea, bright sunny day",
    # 수도원과 성직자
    "a young gardener in rough clothes working in a monastery vegetable garden, nuns in habits watching curiously from a cloister arch, sunny",
    "a plump friar in a brown robe preaching with dramatic gestures to villagers in a sunny square, the villagers amused",
    # 꾀 많은 아내와 남편
    "a comic medieval scene: a bewildered husband peering inside a large wooden barrel while his clever wife stands with hands on hips, rustic courtyard, bright day",
    "a laughing young Italian woman in a medieval dress whispering a secret behind her hand, warm light, plain wall",
    # 칼란드리노
    "a foolish medieval painter in a red cap searching excitedly for magic stones on a pebbly riverbank, two friends laughing behind him, bright day",
    "a clear shallow river flowing over smooth pebbles in the Tuscan countryside, sunlight",
    # 그리셀다
    "a humble young peasant girl in a plain dress carrying a water jar on her shoulder near a small stone cottage, bright morning",
    "a medieval marquis on horseback in fine clothes stopping before a humble peasant cottage, sunny countryside",
    "a patient young woman in a simple grey dress standing with dignity in a sunlit stone hall, calm face",
    # 6 열흘, 그리고 귀환
    f"{WO} and {MEN} laughing together on a sunny terrace overlooking Tuscan hills",
    f"{W1} listening intently with chin on hand, garden background, soft golden light",
    f"{M1} telling a story with expressive gestures, others reacting with laughter, garden, bright day",
    "golden late afternoon light over a quiet villa garden with empty chairs around a fountain",
    f"the group of {WO} and {MEN} riding horses down the hill toward a distant medieval walled city, bright morning",
    "a distant view of a medieval Tuscan walled city with a cathedral dome under a clear sky, morning haze",
    "a single red rose and a laurel wreath lying on a stone bench in a sunlit garden",
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

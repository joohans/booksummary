#!/usr/bin/env python3
"""「안티고네」(소포클레스) Flux 무드 이미지 배치 생성

테베 성문 전투와 두 형제의 죽음 → 크레온의 포고 → 새벽 성문 밖 안티고네와 이스메네
→ 들판의 시신에 흙을 덮는 안티고네 → 파수꾼에게 붙잡힘 → 왕궁 앞 크레온과의 대면
→ 하이몬의 간청 → 바위 동굴 → 눈먼 예언자 테이레시아스 → 동굴의 비극 → 홀로 남은 크레온.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 비문·두루마리·주화·방패 문양 금지.
사진풍 영화 스틸 BASE(삽화풍은 모서리 서명이 붙는다). 그리스 인물은 얼굴·나이를 명시.

    SEED_BASE=67000 .venv/bin/python scripts/gen_flux_antigone.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/Antigone_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still of ancient Greece, classical tragedy, soft natural Mediterranean light, bright enough to see clearly, not dark, "
        "shallow depth of field, light film grain, "
        "fully clothed modest figures, no logos, no text, no letters, no numbers, no inscriptions, no writing anywhere, no watermark, no signature")

ANTI = "a resolute young Greek woman of twenty with long dark hair, in a plain undyed linen robe"
ISME = "a gentle frightened young Greek woman of eighteen with dark braided hair, in a plain pale blue linen robe"
CREON = "a stern grey-bearded Greek king of sixty with a plain gold circlet, in a dark red wool robe"
HAEMON = "a passionate young Greek man of twenty-two with short dark curly hair, in a plain white tunic"
TIRES = "a very old blind Greek prophet with a long white beard and clouded eyes, leaning on a wooden staff, led by a young boy"
GUARD = "a nervous middle-aged Greek soldier with a plain bronze helmet and a plain leather cuirass"

SCENES = [
    # 전쟁과 두 형제
    "massive ancient stone city walls and a great wooden gate under a pale dawn sky, smoke rising in the distance",
    "a dusty battlefield outside ancient city walls at dawn, abandoned plain round shields and broken spears on the ground",
    "two plain bronze helmets lying side by side in the dust, soft morning light",
    "an army of ancient soldiers retreating across a wide plain toward distant hills, dust in golden light",
    "a quiet ancient Greek city of white stone houses on a hill, morning after a battle, peaceful light",
    # 크레온의 명령
    f"{CREON} standing on the steps of a columned stone palace, raising his hand to give a command, bright daylight",
    "elderly Greek men in plain robes gathered on palace steps, listening in silence, bright daylight",
    "close-up of a plain gold circlet resting on a stone table, soft light",
    "an empty stone throne in a columned hall with sunlight falling through, bright",
    # 안티고네와 이스메네
    f"{ANTI} and {ISME} whispering together outside a stone gate at dawn, soft blue light",
    f"{ISME} turning away with tears, hands over her face, soft dawn light, blurred background",
    f"close-up of {ANTI}, determined eyes, wind in her hair, soft dawn light",
    f"{ANTI} walking alone along a dusty path outside the city walls in the early morning, from behind",
    # 매장
    "a wide barren plain with dry grass and scattered stones under a hazy sky, crows circling far away",
    "close-up of a young woman's hands letting dry soil fall from her palms, soft warm light",
    f"{ANTI} kneeling in a field, sprinkling handfuls of earth over a shape covered by a plain cloth, golden light",
    "a small clay jug pouring water onto dry earth, close-up, soft warm light",
    "a dust storm sweeping across a dry plain at midday, bright hazy sunlight",
    f"{GUARD} standing in a dry field, looking worried, bright daylight",
    f"{GUARD} leading {ANTI} by the arm along a stone road toward a palace, bright daylight",
    # 대면
    f"{CREON} glaring down from a stone platform, angry, bright daylight through columns",
    f"{ANTI} standing straight and proud before a king in a columned hall, calm face, bright daylight",
    f"{ANTI} looking up toward the sky with quiet conviction, soft light",
    f"{ISME} kneeling and pleading in a columned hall, soft light",
    "an ancient Greek chorus of elderly men in plain grey robes standing in a semicircle in a stone theater, bright daylight",
    # 하이몬
    f"{HAEMON} speaking earnestly to an older bearded king in a stone courtyard, bright daylight",
    f"{CREON} turning his back in anger in a stone courtyard, bright daylight",
    f"{HAEMON} walking away quickly between white columns, distressed, bright daylight",
    "a sunlit inner courtyard of an ancient Greek palace with an olive tree, quiet",
    # 동굴
    "the dark rocky entrance of a cave in a sunlit hillside, large stones piled beside it",
    f"{ANTI} being led by soldiers up a rocky hillside path toward a cave, bright overcast light",
    f"{ANTI} looking back toward the city one last time, wind, golden light",
    "a single beam of daylight falling into a bare rock chamber, dust in the air",
    "soldiers pushing a large stone to close a cave entrance on a sunny hillside",
    # 테이레시아스
    f"{TIRES} walking slowly through a palace gate, bright daylight",
    "a flock of birds wheeling and fighting in a pale sky over ancient city walls",
    "smoke rising from a small stone altar on a hill, soft light",
    f"{CREON} with a shocked face, hand on his forehead, bright daylight through columns",
    # 비극과 끝
    f"{CREON} hurrying up a rocky hillside with soldiers, desperate, overcast bright light",
    "the opened entrance of a rock cave with stones rolled aside, soft grey light",
    "a white linen veil caught on a rock, fluttering in the wind, soft light",
    "a dignified grey-haired Greek queen in a plain dark robe standing alone by a palace doorway, sorrowful, soft light",
    f"{CREON} sitting alone on palace steps, head bowed in grief, soft evening light",
    "golden sunset over ancient stone city walls and a quiet plain, peaceful and sad",
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
            seed = int(os.environ.get("SEED_BASE", "67000")) + i * 100 + k * 7
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

#!/usr/bin/env python3
"""「사자왕 형제의 모험」(아스트리드 린드그렌) Flux 무드 이미지 배치 생성

1970년대 스웨덴 작은 아파트의 병약한 동생 칼과 형 요나탄 → 하얀 비둘기 → 낭기열라 벚나무 골짜기(초원·농가·말)
→ 비둘기 키우는 소피아 → 산맥을 넘어 들장미 골짜기(성벽·병사·억압된 마을) → 마티아스 할아버지 오두막
→ 동굴·폭포·용 카틀라 → 산 위 형제 → 낭길리마의 빛.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]) — 자연·농가·클로즈업 위주, 가게·간판·책 금지.
깃발·문장(紋章)은 부정어로 못 막으니 병사는 「plain grey cloaks」로만.
BASE 는 사진풍 「35mm period film still」(모서리 서명 0 실측), 「drama」 금지.

    SEED_BASE=73000 .venv/bin/python scripts/gen_flux_lionheart.py 2     # 장면당 2장
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")
OUT = Path(os.environ.get("FLUX_OUT", "assets/images/The_Brothers_Lionheart_flux"))   # 검수 후 옮긴다

BASE = ("35mm period film still, 1970s Scandinavian fantasy adventure film, soft natural daylight, "
        "bright enough to see clearly, not dark, light film grain, "
        "no logos, no text, no letters, no numbers, no signs, no writing anywhere, no watermark, no signature")

KARL = "a pale thin ten-year-old Swedish boy with tousled light blond hair in a plain wool sweater"
JONATAN = "a handsome thirteen-year-old Swedish boy with golden blond hair and a kind confident smile in a plain linen shirt"
BROTHERS = f"two Swedish brothers, {JONATAN} and {KARL}"
SOFIA = "a strong Swedish woman in her forties with braided brown hair in a plain blue peasant dress"
MATTIAS = "a kind old Swedish man with a white beard in a plain brown wool coat"
SOLDIERS = "soldiers in plain grey cloaks and simple iron helmets without emblems"

SCENES = [
    # 현실 — 1970년대 스웨덴 작은 아파트
    f"{KARL} lying in a narrow bed by a small window in a modest old apartment, soft afternoon light, simple wooden furniture",
    f"{JONATAN} sitting at the edge of a bed telling a story to his little brother, warm lamp light, plain wallpaper",
    f"close-up of {KARL} listening with wide hopeful eyes, soft window light",
    "a pair of hands holding a hard golden rusk biscuit over a plain blanket, close-up, warm light",
    "a white dove perched on a windowsill of an old apartment, soft morning light, plain wall",
    "an old Scandinavian town street of yellow plaster houses in winter afternoon, soft snow, no shops",
    # 낭기열라 — 벚나무 골짜기
    "a green valley full of blossoming cherry trees beside a clear river, bright spring morning, wide view",
    f"{BROTHERS} running across a meadow of wildflowers under blossoming cherry trees, bright sunlight",
    "an old red wooden Swedish farmhouse with white trim beside a river, cherry blossoms, bright day",
    f"{JONATAN} and {KARL} riding two horses, a white horse and a brown horse, along a riverbank, bright morning",
    "two horses, a white horse and a chestnut horse, grazing in a sunny green pasture by a stream",
    f"{KARL} sitting by a campfire by a riverbank in golden evening light, smiling",
    f"{BROTHERS} fishing from a small wooden boat on a calm river, bright summer day",
    "a small wooden kitchen in a farmhouse with a stone hearth and copper pots, warm sunlight through a window",
    f"{SOFIA} standing among white doves in a sunny farmyard, doves flying around her",
    "many white doves flying over a green valley with cherry trees, bright blue sky",
    "a white dove with a small rolled paper tied to its leg, close-up, blurred green background",
    "a quiet green forest path with dappled sunlight and moss covered stones",
    f"{JONATAN} looking towards distant mountains from a hilltop, wind in his hair, bright afternoon",
    # 산맥을 넘어
    "a narrow mountain path along steep grey cliffs, mist below, soft daylight",
    f"{KARL} alone on horseback crossing a rocky mountain pass, cold clear morning",
    "a shallow rocky cave entrance in a mountainside with soft light coming in, moss and ferns",
    f"{KARL} hiding behind rocks in a sunlit mountain cave, frightened eyes, soft light",
    # 들장미 골짜기 — 억압
    "a valley of wild roses below a long grey stone wall, overcast daylight, wide view",
    "a high grey stone wall with a heavy wooden gate in a quiet valley, overcast but bright",
    f"{SOLDIERS} standing guard at a wooden gate, overcast daylight, seen from a distance",
    "a poor medieval Scandinavian village of grey wooden cottages with thatched roofs, gloomy but bright overcast day",
    "thin hungry villagers in plain worn wool clothes standing silently in a muddy village lane, overcast daylight",
    f"{MATTIAS} standing at the door of a small wooden cottage, warm smile, soft daylight",
    f"{MATTIAS} and {KARL} sitting at a rough wooden table with bread and soup, warm window light",
    "a hidden trapdoor in a wooden cottage floor slightly open, soft light, close-up",
    f"{JONATAN} in a plain cloak secretly meeting villagers in a barn, soft light through wooden slats",
    "white wild roses climbing an old stone wall, close-up, soft daylight",
    # 카르마 폭포·용 카틀라
    "a huge waterfall crashing into a deep river gorge surrounded by dark rocks, mist, bright daylight",
    "a great dark cave mouth beside a roaring waterfall, mist and spray, daylight",
    "an enormous ancient fire-breathing dragon with dark green scales emerging from a cave by a waterfall, dramatic but visible daylight",
    "close-up of a dragon's golden eye with scales, soft light, shallow depth of field",
    "a long brass horn lying on a flat rock by a river, close-up, plain background",
    f"{BROTHERS} crouching behind a boulder watching a distant waterfall, tense, bright daylight",
    "a wide river in a mountain gorge after a storm, calm water, soft light breaking through clouds",
    # 결말 — 형제·낭길리마
    f"{JONATAN} lying wounded and pale in a wooden cabin, {KARL} holding his hand, soft window light",
    f"{BROTHERS} on horseback riding toward high green mountains, sunrise",
    f"{JONATAN} carrying {KARL} on his back at the edge of a high green cliff above a misty valley, golden sunrise",
    "a beautiful valley of light far below green cliffs, soft golden morning mist, apple trees in bloom",
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
            seed = int(os.environ.get("SEED_BASE", "73000")) + i * 100 + k * 7
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

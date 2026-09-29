#!/usr/bin/env python3
"""「설공찬전」 Flux 무드 이미지 배치 생성 (스톡 66장 보충용)

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
OUT = Path("assets/images/The_Tale_of_Seol_Gongchan")

BASE = ("cinematic painterly film still, early 1500s Joseon Korea, muted cold palette "
        "of indigo, grey and ash, faint warm candle accents, soft mist, deep shadows, "
        "film grain, quiet eerie somber mood, no text, no signboards, no inscriptions")

SCENES = [
    # 순창 설씨 집안 · 죽음
    "a Joseon nobleman in grey hanbok kneeling alone before a small wooden ancestral shrine table with a single candle, dim room",
    "a young Joseon man in white mourning hanbok lying pale on a quilt, family gathered in shadow around him",
    "a fresh grave mound on a misty hillside, bare tree, one man in white mourning clothes standing with bowed head",
    "an elderly Joseon father weeping quietly on the wooden veranda of a hanok at dusk, empty courtyard",
    "a young bride in red and green wedding hanbok seen from behind walking through a gate into fog",
    # 빙의
    "a beautiful young woman in flowing white hanbok descending from a dark sky, dancing in mid-air above a hanok courtyard at sunset",
    "a young Joseon man in white hanbok collapsed on the stone steps of an outhouse at dusk, servants running toward him",
    "close-up of a young Joseon man's face with wide unfocused eyes, lit from below by candlelight, dark room",
    "a young man in hanbok sitting rigidly on a wooden floor eating rice with his left hand, family watching in fear from the doorway",
    "a young Joseon man sitting alone under an old apricot tree beside a small pavilion behind a house, blue dusk, mist",
    "a translucent ghostly figure of a young man standing behind a seated identical young man, candlelit hanok room",
    "a straw rope twisted the wrong way hung across the outer gate of a hanok at night, lantern light",
    "a young man's contorted body on a wooden floor, limbs twisted, an old servant fainting beside him, candle overturned",
    "an old Joseon uncle bowing to the ground pleading, hands pressed together, before his possessed nephew in a dim room",
    "two young Joseon scholars in hanbok arriving at a gate at night carrying a lantern, wary faces",
    # 무당 김석산
    "a Joseon shaman in white robe striking the air with a peach-wood branch inside a dim hanok room, incense smoke",
    "a peach-wood branch and red cinnabar powder on a low wooden table, candle flame, dark room",
    "a shaman's silhouette in a doorway at night, red ribbons fluttering, moonlit courtyard",
    # 저승 단월국
    "a lone figure in white hanbok walking along a dark sea shore toward a distant walled city glowing faintly at the horizon, night",
    "a vast gate of an underworld city opening at dawn hour, endless line of pale figures waiting in mist",
    "an underworld tribunal hall lit by cold blue lanterns, a towering armored king seated on a high throne, small souls below",
    "a soul in torn hanbok kneeling on stone, a giant iron whip raised above, ledgers of judgement glowing behind (no legible writing), dark hall",
    "an old dignified Joseon ancestor in official robes seated calmly in a shadowy underworld court, extending a hand toward a frightened young man",
    "rows of pale souls walking across a grey plain under a starless sky toward a black sea",
    "a hell landscape of dark fire pits and chains, tiny figures, seen from far above, mostly darkness",
    "a woman in hanbok seated at an official's desk in a spirit court, other spirits bowing to her, cold blue light",
    # 염라왕 · 성화 황제
    "an immense palace of the underworld king, black pillars and red lacquer, far grander than any earthly palace, mist below",
    "a grand feast in a dark palace hall, kings and ministers of many ages seated in long rows, cold lantern light",
    "a Chinese emperor in golden robes standing small before a giant dark-robed judge seated on a vermilion throne, dark hall",
    "an emperor's envoy in official dress kneeling and pleading before a towering throne in shadow",
    "a bronze cauldron boiling over a fire in a dark stone hall, steam rising, guards in shadow",
    # 채수 · 쾌재정 · 필화
    "an old Joseon scholar in plain hanbok sitting alone in a hilltop pavilion overlooking a river valley, autumn evening",
    "a small wooden pavilion on a hill above a misty river, one lamp lit inside, dusk",
    "an aging Joseon official walking away from a palace gate at dawn, back turned, long shadow",
    "a court of Joseon officials in black hats and robes arguing in a great hall, the king's throne in shadow",
    "a bonfire in a palace courtyard at night, soldiers throwing bundles into the flames, sparks rising into darkness",
    "ash and burnt fragments drifting in the wind across a stone courtyard at dawn",
    "a Joseon scholar in a dim room at night writing on the back of a bound ledger by candlelight, seen from behind, no visible writing",
    "a hidden bundle wrapped in cloth tucked under the floorboards of a hanok, thin shaft of light",
    "a single candle flame in total darkness, faint smoke curling upward",
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
            seed = 29000 + i * 100 + k * 7
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

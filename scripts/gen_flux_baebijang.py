#!/usr/bin/env python3
"""「배비장전」 Flux 무드 이미지 배치 생성 (스톡 보충용)

조선 후기 제주, 위선적인 비장이 기생 애랑과 방자의 계교에 망신당하는 희극.
교훈(구보·태평천하·소유냐 존재냐): 실내 벽은 서예 액자를 부른다 → 얕은 심도 클로즈업·야외·바다·숲 위주.
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 포트는 /generate 1회로 확인
OUT = Path("assets/images/The_Tale_of_Bae_Bijang_flux")   # 스톡 AI 검증이 Flux 까지 깎지 않도록 따로 받아 검수 후 옮긴다

BASE = ("playful satirical painterly film still, late Joseon dynasty Korea, Jeju island, 18th century, warm natural light, "
        "lively colors with sea blue and spring green, film grain, very shallow depth of field, background blurred out of focus, "
        "comedic mood, no text, no signs, no calligraphy, no scrolls, no banners, no letters, no writing anywhere")

SCENES = [
    # 출발 · 맹세
    "a stiff self-righteous young Joseon official in a black gat hat and blue robe bowing solemnly to his old mother and wife at a gate, raising his hand as if swearing an oath",
    # 풍랑
    "a small wooden sailing ship tossed by huge waves in a storm at sea, officials in robes clinging to the mast in terror",
    "seasick Joseon officials in robes collapsed on the deck of a rocking ship, green faces, comedic",
    # 제주 도착
    "the black volcanic rock coast of Jeju island with turquoise sea and a stone harbor, a small ship arriving, bright day",
    "Mount Hallasan rising above green fields and black stone walls of Jeju under a clear sky",
    # 정 비장 이별 · 발치
    "a weeping middle-aged official in a gat hat kneeling on a beach handing over bundles of silk and treasure to a beautiful young gisaeng in a colorful hanbok",
    "close-up of a pair of old pliers holding a single human tooth, a weeping official's hand open below, comedic",
    "a stiff young official in a gat hat watching from a distance with a scornful smirk, arms crossed, sea wind",
    # 내기
    "a cheeky young servant boy in rough cotton clothes grinning slyly and shaking hands with a stiff young official, making a bet",
    # 봄놀이 · 애랑
    "a spring outing in a green Jeju valley, officials in robes sitting on mats with wine, gisaeng dancing, azaleas blooming",
    "a beautiful gisaeng in a light hanbok washing her hair by a clear forest stream among spring flowers, seen from a distance through leaves",
    "a young official in a gat hat peeking through bushes with wide eyes and an open mouth, flustered, comedic",
    "a young official clutching his stomach pretending to be sick while the others walk away, sly sideways glance",
    # 상사병 · 편지
    "a young official lying lovesick on a mat staring at the ceiling, sighing, a half-eaten bitten apple beside him",
    "close-up of a folded letter on hanji paper being secretly passed between two hands, no writing visible",
    # 개가죽 두루마기 · 담 구멍
    "a young official wearing a ridiculous shaggy dog-skin coat and a shabby straw hat sneaking through a moonlit lane, comedic",
    "a man in a dog-skin coat stuck halfway through a small hole at the bottom of a black stone wall at night, legs kicking, comedic",
    # 애랑의 방
    "a beautiful gisaeng in hanbok sitting by candlelight smiling mischievously, a nervous official kneeling opposite her, warm glow",
    # 남편 행세 · 자루 · 궤
    "a frightened man hiding inside a large cloth sack in the corner of a dark room, only his feet sticking out, candlelight",
    "a large wooden storage chest with a man's terrified eyes peeking from a gap in the lid, dark room, candlelight",
    "a sly servant holding a burning torch over a wooden chest pretending to set it on fire, a gisaeng covering her laugh",
    "a sly servant pretending to saw a wooden chest in half with a big saw, comedic, lamplight",
    # 동헌
    "servants carrying a heavy wooden chest on poles across a government courtyard at dawn, officials watching and grinning",
    "a Joseon governor in red official robes sitting on a raised wooden platform trying not to laugh, attendants around",
    "men disguised as boatmen splashing water and rocking a wooden chest, pretending it is at sea, crowd laughing",
    "a naked man seen from behind crawling out of a wooden chest and flailing his arms as if swimming on a dry dirt courtyard, crowd laughing, comedic, tasteful",
    "a crowd of Joseon officials, soldiers and gisaeng doubled over in laughter in a courtyard, bright morning",
    "a red-faced official wrapped in a blanket bumping his head against a wooden pillar, comedic",
    # 결말
    "a humiliated young official sitting alone on black volcanic rocks by the sea at sunset, head in hands",
    "a small ship on the sea at sunset with a gisaeng in hanbok and an official standing together on deck, smiling",
    # 덧장면
    "close-up of a bitten red apple in an official's hand, comedic",
    "close-up portrait of a beautiful clever Jeju gisaeng with a knowing smile, flowers in her hair, blurred sea behind",
    "close-up portrait of a cheeky servant boy laughing, blurred green background",
    "a black gat hat lying abandoned on a dirt courtyard",
    "Jeju black stone walls and yellow canola flowers under a blue sky",
    "waves crashing on black volcanic rocks of Jeju, spray in the sun",
    "a geomungo zither lying on a mat with a cloth sack beside it, candlelight",
    "a wooden chest standing alone in an empty courtyard, morning light, comedic emptiness",
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
    base, scenes, tag = BASE, SCENES, "f"
    OUT.mkdir(parents=True, exist_ok=True)
    made = 0
    t0 = time.time()
    for i, scene in enumerate(scenes, 1):
        prompt = f"{base}. {scene}"
        for k in range(per):
            seed = 51000 + i * 100 + k * 7
            img = generate(prompt, seed)
            if not img:
                continue
            path = OUT / f"mood_{tag}{i:02d}_{k+1}.jpg"
            path.write_bytes(img)
            made += 1
            print(f"[{made}] {path.name}  ({time.time()-t0:.0f}s)  {scene[:50]}", flush=True)
    print(f"\n✅ {made}장 생성 / {time.time()-t0:.0f}초", flush=True)


if __name__ == "__main__":
    main()

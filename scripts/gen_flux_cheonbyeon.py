#!/usr/bin/env python3
"""「천변풍경」 Flux 무드 이미지 배치 생성 (스톡 보충용)

1930년대 서울 청계천변의 일 년(2월~이듬해 1월) → 장면을 Flux 로 채운다.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 1930년대 서울 도심은 간판 시대다(레디메이드 인생 폐기율 36%). 이발소·한약국·포목점·카페가 핵심 무대지만
   가게 **바깥 정면**은 그리지 않고 **실내**와 **개천·빨래터·다리·지붕·인물**로만 간다.
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).
"""
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

FLUX = "http://192.168.0.150:9010/generate"   # 포트는 /health 로 확인(2026-10-08 9010 정상)
OUT = Path("assets/images/Scenes_from_the_Riverside_flux")   # 스톡 AI 검증이 Flux 까지 깎지 않도록 따로 받아 검수 후 옮긴다

BASE = ("warm nostalgic painterly film still, Seoul in the mid 1930s along the open Cheonggyecheon stream, "
        "low tiled roofs and stone embankments, soft natural light, muted sepia, jade and warm ochre palette, film grain, "
        "gentle everyday mood, no text, no signboards, no shop signs, no banners, no posters, no letters, no writing")

SCENES = [
    # 2월 · 빨래터
    "Korean women in 1930s hanbok squatting at a stone laundry place on the edge of a shallow stream, beating clothes with wooden paddles, late winter sun",
    "laundry women chatting and laughing by the stream, steam rising from the cold water, white cloth spread on rocks",
    "an open stream running between stone embankments and rows of tiled roofs in 1930s Seoul, seen from a low arched stone bridge",
    # 이발소 · 재봉이
    "a fifteen-year-old Korean boy in a white barber's apron leaning on a window sill inside a small 1930s barbershop, watching the street with delight",
    "interior of a small 1930s barbershop, an old leather barber chair, a large mirror, scissors and razors on a shelf, soft window light, no signs",
    "a plump wealthy Korean man in his fifties in a Western suit studying his aging face in a barbershop mirror, sighing",
    # 민 주사
    "a wealthy older man in a 1930s suit gambling with cards at a low table in a smoky room with other men",
    "a beautiful young concubine in a silk hanbok secretly meeting a young man under a willow by the stream at night",
    # 창수 · 금순이
    "a country boy of thirteen in rough cotton clothes arriving in the city with a small bundle, staring wide-eyed at the stream and roofs",
    "a clever young errand boy carrying a wrapped herbal medicine parcel briskly along the stream bank",
    "a shy country girl in a plain hanbok standing at the doorway of a modest city house, two stylish 1930s cafe waitresses greeting her",
    "a young woman and a small boy recognizing each other and embracing in tears on a stone bridge, passersby watching",
    # 카페 여급
    "a young 1930s Korean cafe waitress in a modern dress and short wavy hair sitting alone at a cafe table, tired melancholy face, dim interior",
    # 이쁜이
    "a traditional Korean wedding in a small courtyard, the bride in red with face powder dots, neighbors watching happily",
    "a young married woman in hanbok running home exhausted along the stream at dusk, clutching a small bundle",
    "a young woman sleeping deeply on a floor mat while her worried mother sits beside her in a dim room",
    "a young man standing alone on the stream bank watching a bridal palanquin pass in the distance, heartbroken",
    # 만돌 어멈 · 몰락
    "a weary servant woman in plain clothes sitting alone outside a gate with a small child, bruised and silent",
    "a family loading a handcart with their belongings, leaving a house by the stream on a grey day",
    # 한약국 내외 · 평화
    "a young couple in hanbok in a sunny wooden-floored hall with family members listening to an old radio, peaceful afternoon",
    "a young mother holding a newborn baby on a sunny veranda of a tiled house, her husband smiling",
    # 계절
    "spring willows hanging over the stream, children playing on the stone embankment, soft green light",
    "a summer flood rushing down the stream, people watching from the bridge, rain",
    "autumn along the stream, golden light on tiled roofs and drying red peppers",
    "winter on the stream, thin ice on the water, snow on the roofs, a boy walking across the bridge in January",
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
            seed = 39000 + i * 100 + k * 7
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

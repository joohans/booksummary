#!/usr/bin/env python3
"""「하늘은 맑건만」 Flux 무드 이미지 배치 생성 (스톡 보충용)

1930년대 일제강점기 도시의 소년 이야기는 무료 스톡에 거의 없다 → 장면을 Flux 로 채운다.
글자 차단은 소재 선택으로 한다 ([[project_flux_text_problem]]).
→ 핵심 소재가 「고깃간」「지전·은전」「담벼락 낙서」「교실 수신 시간」「활동사진관」이지만
   상점·간판·지폐·칠판·벽 낙서·극장은 장면에서 아예 뺀다(1930년대 도시 = 간판 시대, 폐기율 36% 실측).
   Flux 는 소년·마당·골목(간판 없는 주택가)·하늘·불빛만 그린다.
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).
"""
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

FLUX = "http://192.168.0.150:9010/generate"   # 포트는 /health 로 확인(2026-10-05 9010 정상)
OUT = Path("assets/images/Though_the_Sky_Is_Clear_flux")   # 스톡 AI 검증이 Flux 까지 깎지 않도록 따로 받아 검수 후 옮긴다

BASE = ("nostalgic painterly film still, Korea in the late 1930s, a quiet residential neighborhood of tile-roofed houses, "
        "soft natural light, muted sepia and clear sky-blue palette, film grain, anxious yet tender coming-of-age mood, "
        "no text, no signboards, no shop fronts, no letters, no writing, no posters, no banknotes, no blackboards")

SCENES = [
    # 하늘 · 문기
    "a ten-year-old Korean boy in a 1930s school uniform and cap looking up at a vast clear blue sky, small figure",
    "a ten-year-old boy with a shaved head in a plain white shirt and dark shorts standing in a hanok courtyard, worried face",
    "a boy walking home along a quiet residential lane of tile-roofed houses, holding a straw-wrapped bundle of meat, afternoon",
    "a boy's hand holding a few round silver coins in his palm, close-up, warm light, no writing",
    # 수만이와 돈 쓰기
    "two boys in 1930s clothes whispering together behind a stone wall, one sly and grinning, one hesitant",
    "two boys laughing and kicking a small leather ball on a dirt lane between tile-roofed houses",
    "a boy peering through a pair of old brass binoculars from a hillside over rooftops",
    "two boys sitting on a wooden floor in a dim room watching light from an old magic lantern projector on a cloth sheet",
    # 들킴 · 거짓말
    "a leather ball and brass binoculars placed on a low wooden table in a hanok room, a stern man's shadow beside them",
    "a gentle Korean man in his thirties in a 1930s vest kneeling to speak to a guilty-looking boy in a hanok room",
    "a boy lying awake at night under a quilt staring at the ceiling, moonlight through a paper window",
    # 돈을 던지다 · 협박
    "a boy at dusk throwing something over a low wooden fence into an empty yard, running away",
    "a boy hiding behind a large tree trunk in a schoolyard, peeking out fearfully",
    "a sly boy following another boy down a lane, pointing and calling out, the first boy hunching his shoulders",
    "a boy's hand reaching toward a small cloth purse in a drawer of a wooden chest, dim room, tense",
    # 점순이
    "a young servant girl of about thirteen in a plain hanbok planting flowers in a courtyard garden",
    "a young girl in a plain hanbok crying and leaving through a wooden gate with a small cloth bundle, a boy watching from the veranda",
    # 선생님 댁 · 사고
    "a boy standing hesitantly at the gate of a modest tile-roofed house in the evening, warm lamplight inside",
    "a kind young teacher in a 1930s suit and his wife holding a baby, greeting a nervous boy in a small room",
    "a boy wandering alone down an empty lane at dusk, head down, long shadow",
    "the bright headlights of an old 1930s automobile rushing toward the viewer on a dusky road, motion blur",
    # 병원 · 고백 · 맑은 하늘
    "a boy with a bandaged head lying in a simple white hospital bed, his uncle sitting at the bedside holding his hand, morning light",
    "a boy in a hospital bed looking out a window at a bright clear blue sky, peaceful smile",
    "a wide clear blue autumn sky over tile rooftops, a few white clouds, bright and open",
    "a boy on a hill with his arms spread, face lifted to a brilliant clear sky, freedom",
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
            seed = 35000 + i * 100 + k * 7
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

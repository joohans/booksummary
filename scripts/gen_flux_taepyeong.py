#!/usr/bin/env python3
"""「태평천하」 Flux 무드 이미지 배치 생성 (스톡 보충용)

1937년 가을, 서울 계동 만석꾼 윤 직원 집안의 하루 → 장면을 Flux 로 채운다.
「소설가 구보씨의 일일」 교훈: BASE 에 지명(Seoul/Gyeongseong)을 넣으면 간판·현판이 쏟아진다(1차 폐기 80%).
→ 지명을 빼고 「plain bare walls, no frames, no calligraphy」 + 클로즈업·인물·사물·한옥 마당 위주로 간다.
산출물은 렌더러가 읽도록 반드시 mood_*.jpg ([[project_render_image_order]]).
"""
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

FLUX = os.environ.get("FLUX_URL", "http://192.168.0.150:9010/generate")   # 포트는 /generate 1회로 확인(2026-10-08 9010 정상)
OUT = Path("assets/images/Peace_Under_Heaven_flux")   # 스톡 AI 검증이 Flux 까지 깎지 않도록 따로 받아 검수 후 옮긴다

BASE = ("satirical yet melancholy painterly film still, late 1930s Korea, wealthy traditional household, autumn, "
        "soft natural light, muted sepia, warm ochre and dark green palette, film grain, "
        "plain bare walls with nothing hanging on them, no text, no signs, no frames, no calligraphy, no scrolls, "
        "no posters, no letters, no numbers, no writing anywhere")

SCENES = [
    # 인력거 삯
    "a fat rich old Korean man of seventy in a fine white hanbok coat and black horsehair hat stepping down from a rickshaw, smug face",
    "a thin sweating rickshaw puller in rags holding out his palm, pleading, while a fat old rich man turns away stingily",
    "close-up of an old man's fat hand dropping two small copper coins into a worker's rough palm",
    # 과거 · 화적
    "night raid on a rural tiled-roof house in the 1890s, bandits with torches, flames rising, a young man hiding in the dark",
    "a young Korean man in white clothes kneeling beside his dead father in the ashes of a burned courtyard at dawn, fists clenched in rage",
    # 만석꾼
    "a huge courtyard of a wealthy hanok filled with stacked straw rice sacks, servants carrying more, autumn harvest",
    "an old landlord counting thick bundles of paper money on a low lacquered table in a dim room, an abacus beside him",
    "a heavy iron safe in the corner of a traditional room, an old man's hand resting on it possessively",
    "close-up of a bundle of old land deeds tied with string and a heavy brass key on a wooden table, no writing visible",
    # 인색함
    "a family eating barley rice at a small low table while an old man alone eats white rice at his own table, the others glancing at him",
    "a ragged beggar child at the closed wooden gate of a rich house, the gate shut in his face",
    "an old fat man in hanbok smiling smugly while handing a big sack of money to a stern Japanese police officer in 1930s uniform",
    # 춘심
    "a rich old man of seventy in hanbok grinning lecherously at a fifteen-year-old girl entertainer in a pink hanbok who looks bored",
    "close-up of a shiny gold ring held out in an old man's wrinkled palm toward a young girl's hand",
    "a teenage girl in hanbok and a cheeky schoolboy in a 1930s school cap whispering and laughing behind a wall",
    # 윤 주사 · 마작
    "a middle-aged Korean gentleman in a Western suit playing mahjong with friends in a smoky room at night, tiles on the table, cigarettes",
    "close-up of mahjong tiles scattered on a green cloth table under a hanging lamp, smoke, a glass of liquor",
    "an elegant concubine in silk hanbok with a long pipe lounging in a small decorated room, looking bored",
    # 종수
    "a dissolute young man in a fedora and loose suit drinking and laughing with women in a dim drinking house at night",
    "a young man secretly pressing a carved seal stamp onto a blank paper by lamplight, shifty eyes",
    "a young man in a suit bowing hypocritically before a stern old man in hanbok, holding out his hands for money",
    # 집안
    "a gloomy hanok inner quarters, a middle-aged wife and young daughters-in-law sewing silently with resentful faces",
    "a frail fifteen-year-old boy in hanbok with a vacant face sitting alone on the wooden veranda, a cheeky boy teasing him",
    "a widowed young woman in white mourning hanbok sitting alone by a window in her parents' house",
    # 종학 · 동경
    "a serious young Korean student in a black university uniform and cap reading a book in a small Tokyo boarding room at night",
    "a young student being led away by plainclothes policemen at dawn on a misty street, his books falling to the ground",
    "a telegraph envelope lying unopened on a mahjong table among tiles and cigarette ash",
    # 결말
    "a family lunch in a hanok main hall interrupted, everyone frozen in shock, a fat old man in hanbok rising in fury",
    "a fat old man in hanbok stamping his feet in rage on the wooden floor of a hanok hall, face twisted between fury and tears",
    "an old man in a white hanbok coat walking away down a long dark veranda toward the men's quarters, seen from behind, alone",
    "family members in hanbok kneeling in silence in a dim hall, dark faces, like soldiers who lost their general",
    "the empty courtyard of a grand hanok at dusk, autumn leaves, a single lantern, deep silence",
    "close-up of an old man's trembling clenched fist on his knee, fine hanbok fabric",
    "a crow on the ridge of a tiled roof against a grey autumn sky",
    # 덧장면
    "an old fat man in hanbok sitting cross-legged on a silk cushion, a long bamboo pipe, smugly satisfied, warm afternoon light",
    "close-up portrait of a fat old Korean man of seventy with a sparse white beard, shrewd small eyes, black horsehair hat",
    "a 1930s Korean policeman in a dark uniform and sword standing at a street corner, seen from behind",
    "sacks of rice being loaded onto an ox cart at a rich man's gate at dawn",
]

# 2차(--set 2): 1차는 「wealthy traditional household」 실내라 벽마다 서예 액자·족자가 생겼다(37장 중 온전한 것 3장).
#   「plain bare walls」 지시는 무시된다 → 벽이 화면에 안 들어오게: 얕은 심도로 배경을 날린 클로즈업, 야외 마당·하늘, 검은 배경.
BASE2 = ("satirical yet melancholy painterly film still, late 1930s Korea, autumn, soft natural light, muted sepia, "
         "warm ochre and dark green palette, film grain, very shallow depth of field, background completely blurred out of focus, "
         "no text, no signs, no frames, no calligraphy, no letters, no numbers, no writing anywhere")

SCENES2 = [
    "close-up portrait of a fat old Korean man of seventy in a black horsehair gat hat and white hanbok coat, sly smug grin, blurred autumn background",
    "a rickshaw in an empty autumn lane at dusk, a fat old man in white hanbok and gat climbing down, the thin puller wiping sweat, wide shot with sky",
    "close-up of a rickshaw puller's rough calloused open palm holding two small coins, blurred background",
    "close-up of a fat old man's hand clutching a leather money pouch tightly to his chest, white hanbok sleeve, dark background",
    "a burning tiled-roof farmhouse at night seen from a distance across a field, flames and smoke against the dark sky",
    "silhouettes of bandits with torches running across a dark field at night, embers in the air",
    "a young man in white clothes kneeling alone in ashes at dawn, smoke rising behind him, back view, grey sky",
    "golden rice paddies at harvest under a wide autumn sky, peasants bent over with sickles, far away",
    "straw rice sacks piled high in an open courtyard under a blue autumn sky, tiled roof edges against the sky",
    "close-up of an old wooden abacus and stacks of old paper banknotes tied with string, dark background, warm lamp light",
    "close-up of a heavy black iron safe door with a brass dial, dark background",
    "close-up of a bowl of white rice next to a bowl of coarse barley rice on a small wooden table, dark background",
    "a ragged barefoot boy standing outside a tall closed wooden gate in a stone wall, autumn leaves, sky above",
    "close-up of a fat old man's hand passing a thick envelope to a gloved hand of a uniformed officer, blurred dark background",
    "close-up of a fat old man in a gat hat grinning lecherously, a young girl in pink hanbok blurred in the foreground looking away bored",
    "close-up of a gold ring lying in a wrinkled old palm, dark background",
    "a fifteen-year-old girl in pink hanbok laughing with a schoolboy in a 1930s school cap behind a stone wall under a persimmon tree, blue sky",
    "close-up of mahjong tiles and a glass of liquor on a green cloth under lamplight, cigarette smoke, dark background",
    "close-up of a middle-aged man's hands in a Western suit pushing mahjong tiles, cigarette between fingers, dark smoky background",
    "close-up portrait of an elegant concubine in silk hanbok holding a long thin pipe, bored half-closed eyes, dark background",
    "close-up of a dissolute young man in a fedora laughing with a glass of liquor, dim red lamplight, blurred background",
    "close-up of a young man's hand pressing a carved stone seal stamp, lamplight, dark background",
    "close-up of hands sewing white cloth, a middle-aged woman's resentful face blurred behind, dark background",
    "a frail boy in hanbok sitting alone on a wooden veranda edge looking at the sky, a cheeky boy laughing nearby, outdoor courtyard, autumn",
    "a young widow in white mourning hanbok standing alone under a bare tree in a courtyard, grey sky",
    "close-up of a serious young Korean student in a black university uniform reading a book by lamplight, dark background",
    "a young student in a black uniform being led away by two men in hats on a misty empty street at dawn, books on the ground, back view",
    "close-up of an unopened telegram envelope on a green mahjong table among tiles and cigarette ash, no writing visible",
    "close-up of an old man's face in shock and fury, white beard, gat hat, mouth open, dark background",
    "close-up of an old man's trembling clenched fist on white hanbok fabric",
    "an old man in a white hanbok coat walking away along a dark wooden veranda at dusk, seen from behind, only sky and roof eaves visible",
    "family members in hanbok standing frozen with dark faces in a courtyard at dusk, back lit, silhouettes",
    "an empty courtyard of a grand tiled-roof house at dusk, autumn leaves, a single paper lantern, deep silence, sky",
    "a crow on the ridge of a tiled roof against a grey autumn sky",
    "a persimmon tree with orange fruit over a tiled roof under a pale autumn sky",
    "a 1930s Korean policeman in a dark uniform with a sword walking down an empty dirt lane, seen from behind, autumn trees",
    "an ox cart loaded with rice sacks leaving a tall wooden gate at dawn, misty sky",
    "close-up of a long bamboo smoking pipe with smoke curling, an old fat hand holding it, dark background",
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
    second = "--set" in sys.argv and sys.argv[sys.argv.index("--set") + 1] == "2"
    base, scenes, tag = (BASE2, SCENES2, "g") if second else (BASE, SCENES, "f")
    OUT.mkdir(parents=True, exist_ok=True)
    made = 0
    t0 = time.time()
    for i, scene in enumerate(scenes, 1):
        prompt = f"{base}. {scene}"
        for k in range(per):
            seed = (47000 if second else 45000) + i * 100 + k * 7
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

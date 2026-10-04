#!/usr/bin/env python3
"""Shorts 스프린트 — 「<책> 줄거리」 세로 영상(50초 전후) 제작 파이프라인.

설정: data/shorts/<sprint>.json  (책·연결할 본편·문장별 [대사, 장면 묘사])
산출: assets/shorts/<slug>/  a_NN.wav(문장 TTS) · img_NN.jpg(Flux 세로) · f_NN.png(자막 합성 프레임)
      output/shorts/<slug>.mp4 (GPU150 렌더 후 회수)

단계(각 단계는 이미 있는 산출물을 건너뛴다):
  tts      문장마다 OpenAI tts-1-hd(nova) WAV — 자막과 음성 길이를 문장 단위로 정확히 맞추기 위해
  images   문장마다 Flux 세로 이미지 (150:9010)
  frames   이미지 + 상단 제목 띠 + 문장 자막을 PIL 로 합성 (1080x1920)
  render   GPU150 으로 올려 ffmpeg 렌더(로컬 ffmpeg 금지 규칙) → 회수·검증
  meta     업로드용 메타데이터 json 생성 (output/shorts/<slug>.metadata.json)

사용법:
  make_shorts.py data/shorts/sprint1.json all [--only demian]
  make_shorts.py data/shorts/sprint1.json tts|images|frames|render|meta [--only slug]
"""
import argparse
import base64
import hashlib
import io
import json
import os
import subprocess
import sys
import time
import wave
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from utils.thumbnail_generator import FONT_PATHS_BOLD, FONT_PATHS_REGULAR, _load_font  # noqa: E402

FLUX = "http://192.168.0.150:9010/generate"
GPU = "jsong@192.168.0.150"
KEY = str(Path.home() / ".ssh" / "aws-jsong.pem")
REMOTE = "booksummary_render/shorts"
W, H = 1080, 1920
GAP = 0.25  # 문장 사이 쉼(초)


def shorts_dir(slug):
    d = ROOT / "assets" / "shorts" / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── TTS ──────────────────────────────────────────────────────────
WHISPER = "http://192.168.0.150:9200/v1/audio/transcriptions"  # GPU150 faster-whisper (docker)
TTS_MIN_RATIO = 0.93   # 원고와 받아쓰기 일치도 하한 (0.85 는 단어 삽입·누락을 통과시켰다)
TTS_TRIES = 5

_DIG = "영일이삼사오육칠팔구"


def _num_ko(n):
    """아라비아 숫자를 한자어 읽기로 (받아쓰기 「1980년」↔ 원고 「천구백팔십 년」 비교용)."""
    n = int(n)
    if n == 0:
        return "영"
    out = ""
    for unit, name in ((10000, "만"), (1000, "천"), (100, "백"), (10, "십")):
        q, n = divmod(n, unit)
        if q:
            out += ("" if q == 1 and unit < 10000 else _num_ko(q)) + name
    if n:
        out += _DIG[n]
    return out


def _norm(t):
    import re
    t = re.sub(r"\d+", lambda m: _num_ko(m.group()), t)
    return re.sub(r"[^가-힣A-Za-z]", "", t)


def tts_match(path, line):
    """Whisper 로 받아쓴 뒤 원고와의 일치도(0~1)와 받아쓴 문장을 돌려준다."""
    import difflib
    with open(path, "rb") as f:
        r = requests.post(WHISPER, files={"file": f},
                          data={"model": "Systran/faster-whisper-large-v3", "language": "ko"}, timeout=180)
    r.raise_for_status()
    heard = r.json().get("text", "").strip()
    return difflib.SequenceMatcher(None, _norm(line), _norm(heard)).ratio(), heard


def step_tts(cfg, s):
    """문장마다 TTS → Whisper 로 받아써서 원고와 대조 → 어긋나면 다시 생성(최대 TTS_TRIES 회, 최고점 유지).

    2026-10-04 실측: tts-1-hd 한국어가 90문장 중 6문장을 망가뜨렸다(「백년가약을 맺지만」→「대삽체의
    뺑앤민트고를」, 단어 누락·삽입). 길이 검증만으로는 못 잡는다.
    """
    from openai import OpenAI
    load_dotenv(ROOT / ".env")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    d = shorts_dir(s["slug"])
    report = d / "tts_check.json"
    checked = json.loads(report.read_text(encoding="utf-8")) if report.exists() else {}
    for i, (line, _) in enumerate(s["lines"], 1):
        out = d / f"a_{i:02d}.wav"
        key = f"{i:02d}"
        if out.exists() and checked.get(key, {}).get("line") == line and checked[key]["ratio"] >= TTS_MIN_RATIO:
            continue
        best = None
        if out.exists():
            best = (*tts_match(out, line), out.read_bytes())
        tries = 0
        while (best is None or best[0] < TTS_MIN_RATIO) and tries < TTS_TRIES:
            tries += 1
            audio = client.audio.speech.create(model="tts-1-hd", voice="nova", input=line,
                                               response_format="wav").content
            tmp = d / f"a_{i:02d}.try.wav"
            tmp.write_bytes(audio)
            ratio, heard = tts_match(tmp, line)
            tmp.unlink()
            if best is None or ratio > best[0]:
                best = (ratio, heard, audio)
        out.write_bytes(best[2])
        checked[key] = {"line": line, "ratio": round(best[0], 3), "heard": best[1]}
        flag = "" if best[0] >= TTS_MIN_RATIO else "  ⚠️ 하한 미달 — 귀로 확인"
        print(f"   {s['slug']} {key}: {best[0]:.2f} (재생성 {tries}회){flag}", flush=True)
        report.write_text(json.dumps(checked, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(wav_dur(d / f"a_{i:02d}.wav") for i in range(1, len(s["lines"]) + 1))
    total += GAP * len(s["lines"])
    low = [k for k, v in checked.items() if v["ratio"] < TTS_MIN_RATIO]
    print(f"  TTS {s['book']}: {len(s['lines'])}문장 · 합계 {total:.1f}초 · 하한 미달 {low or '없음'}")
    return total


def wav_dur(p):
    with wave.open(str(p)) as w:
        n = w.getnframes()
        # OpenAI wav 는 헤더의 프레임 수가 0xFFFFFFFF 인 스트리밍 형식일 때가 있다 → 파일 크기로 계산
        if n >= 0x7FFFFFF0 or n == 0:
            data = p.stat().st_size - 44
            n = data // (w.getsampwidth() * w.getnchannels())
        return n / w.getframerate()


# ── Flux 이미지 ──────────────────────────────────────────────────
def step_images(cfg, s):
    d = shorts_dir(s["slug"])
    for i, (_, scene) in enumerate(s["lines"], 1):
        out = d / f"img_{i:02d}.jpg"
        if out.exists():
            continue
        prompt = f"{cfg['style']}. Setting: {s['era']}. Scene: {scene}."
        seed = int(hashlib.md5(f"{s['slug']}-{i}".encode()).hexdigest()[:8], 16)
        for attempt in range(3):
            try:
                r = requests.post(FLUX, json={"prompt": prompt, "width": 1088, "height": 1920,
                                              "steps": 4, "seed": seed}, timeout=180)
                r.raise_for_status()
                img = Image.open(io.BytesIO(base64.b64decode(r.json()["image_base64"]))).convert("RGB")
                img.save(out, quality=93)
                break
            except Exception as e:  # noqa: BLE001
                print(f"   ❌ {s['slug']} {i}: {e}")
                time.sleep(5)
        print(f"  img {s['slug']} {i:02d}", flush=True)


# ── 프레임 합성 ──────────────────────────────────────────────────
def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for word in text.split(" "):
        t = (cur + " " + word).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def outlined(draw, xy, text, font, fill, ow=5):
    x, y = xy
    for dx in range(-ow, ow + 1, 2):
        for dy in range(-ow, ow + 1, 2):
            draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill)


def step_frames(cfg, s):
    d = shorts_dir(s["slug"])
    f_title = _load_font(FONT_PATHS_BOLD, 96)
    f_sub = _load_font(FONT_PATHS_BOLD, 50)
    f_cap = _load_font(FONT_PATHS_BOLD, 64)
    f_tag = _load_font(FONT_PATHS_REGULAR, 40)
    for i, (line, _) in enumerate(s["lines"], 1):
        src = Image.open(d / f"img_{i:02d}.jpg").convert("RGB")
        sw, sh = src.size
        scale = max(W / sw, H / sh)
        src = src.resize((int(sw * scale + 0.5), int(sh * scale + 0.5)), Image.LANCZOS)
        x0, y0 = (src.width - W) // 2, (src.height - H) // 2
        img = src.crop((x0, y0, x0 + W, y0 + H)).convert("RGBA")

        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        for y in range(0, 470):  # 상단 제목 띠 그라데이션
            od.line([(0, y), (W, y)], fill=(0, 0, 0, int(215 * (1 - y / 470) ** 0.8)))
        # 하단 그라데이션 — Flux 가 찍는 가짜 서명·URL 을 가리고, Shorts UI 영역과도 겹친다(2026-10-04 실측)
        for y in range(H - 480, H):
            a = (y - (H - 480)) / 480
            od.line([(0, y), (W, y)], fill=(0, 0, 0, int(245 * min(1, a * 1.25))))
        img = Image.alpha_composite(img, ov)
        dr = ImageDraw.Draw(img)

        title = f"{s['book']} 줄거리"
        tf = f_title
        while dr.textlength(title, font=tf) > W - 120 and tf.size > 60:
            tf = _load_font(FONT_PATHS_BOLD, tf.size - 6)
        tw = dr.textlength(title, font=tf)
        outlined(dr, ((W - tw) / 2, 150), title, tf, (255, 255, 255), 4)
        sub = "1분 요약 · 결말 포함"
        outlined(dr, ((W - dr.textlength(sub, font=f_sub)) / 2, 150 + tf.size + 28), sub, f_sub, (255, 214, 0), 3)

        # 자막: Shorts UI(하단 ~380px·우측 버튼)를 피해 화면 중하단
        cap = wrap(dr, line, f_cap, W - 200)
        lh = f_cap.size + 22
        top = 1180 - (len(cap) * lh) // 2
        box = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(box)
        bd.rounded_rectangle([70, top - 30, W - 70, top + len(cap) * lh + 14], radius=28, fill=(0, 0, 0, 150))
        img = Image.alpha_composite(img, box)
        dr = ImageDraw.Draw(img)
        for k, t in enumerate(cap):
            outlined(dr, ((W - dr.textlength(t, font=f_cap)) / 2, top + k * lh), t, f_cap, (255, 255, 255), 3)
        tag = f"{s['author']} 『{s['book']}』"
        ty = max(1430, top + len(cap) * lh + 40)  # 긴 자막이면 상자 아래로 밀어낸다
        dr.text(((W - dr.textlength(tag, font=f_tag)) / 2, ty), tag, font=f_tag, fill=(235, 235, 235))
        img.convert("RGB").save(d / f"f_{i:02d}.png")
    print(f"  frames {s['slug']}: {len(s['lines'])}장")


def step_thumb(cfg, s):
    """커스텀 썸네일 1080x1920 — 첫 장면 + 큰 제목(자막 없음). 자동 썸네일은 아무 프레임이나 고른다."""
    d = shorts_dir(s["slug"])
    out = ROOT / "output" / "shorts" / f"{s['slug']}_thumb.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    src = Image.open(d / "img_01.jpg").convert("RGB")
    sw, sh = src.size
    scale = max(W / sw, H / sh)
    src = src.resize((int(sw * scale + 0.5), int(sh * scale + 0.5)), Image.LANCZOS)
    x0, y0 = (src.width - W) // 2, (src.height - H) // 2
    img = src.crop((x0, y0, x0 + W, y0 + H)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for y in range(0, 900):
        od.line([(0, y), (W, y)], fill=(0, 0, 0, int(225 * (1 - y / 900) ** 0.9)))
    for y in range(H - 480, H):
        od.line([(0, y), (W, y)], fill=(0, 0, 0, int(245 * min(1, (y - (H - 480)) / 480 * 1.25))))
    img = Image.alpha_composite(img, ov)
    dr = ImageDraw.Draw(img)
    f_book = _load_font(FONT_PATHS_BOLD, 150)
    words = s["book"].split(" ")
    lines = [s["book"]]
    if dr.textlength(s["book"], font=f_book) > W - 120:  # 긴 제목은 두 줄 — 두 줄 길이가 가장 고른 지점에서 나눈다
        best = min(range(1, len(words)), key=lambda k: max(
            dr.textlength(" ".join(words[:k]), font=f_book), dr.textlength(" ".join(words[k:]), font=f_book)))
        lines = [" ".join(words[:best]), " ".join(words[best:])]
        while max(dr.textlength(t, font=f_book) for t in lines) > W - 120 and f_book.size > 90:
            f_book = _load_font(FONT_PATHS_BOLD, f_book.size - 8)
    y = 200
    for t in lines:
        outlined(dr, ((W - dr.textlength(t, font=f_book)) / 2, y), t, f_book, (255, 255, 255), 6)
        y += 175
    f_sub = _load_font(FONT_PATHS_BOLD, 96)
    for t, col in (("줄거리 1분", (255, 214, 0)), ("결말 포함", (255, 255, 255))):
        outlined(dr, ((W - dr.textlength(t, font=f_sub)) / 2, y + 30), t, f_sub, col, 5)
        y += 120
    img.convert("RGB").save(out, quality=92)
    print(f"  thumb {s['slug']}: {out.name}")


# ── 렌더(GPU150) ─────────────────────────────────────────────────
def ssh(cmd, timeout=900):
    return subprocess.run(["ssh", "-n", "-i", KEY, GPU, cmd], capture_output=True, text=True, timeout=timeout)


def step_render(cfg, s):
    slug = s["slug"]
    d = shorts_dir(slug)
    out = ROOT / "output" / "shorts" / f"{slug}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        print(f"  render {slug}: 이미 있음")
        return
    n = len(s["lines"])
    durs = [wav_dur(d / f"a_{i:02d}.wav") + GAP for i in range(1, n + 1)]
    rd = f"{REMOTE}/{slug}"
    ssh(f"mkdir -p {rd}")
    subprocess.run(["rsync", "-a", "-e", f"ssh -i {KEY}", "--include=a_*.wav", "--include=f_*.png",
                    "--exclude=*", f"{d}/", f"{GPU}:{rd}/"], check=True)
    segs = []
    for i, dur in enumerate(durs, 1):
        fr = int(dur * 30) + 1
        # 느린 줌인(문장마다 방향 교대) — 위아래 자막이 잘리지 않을 만큼만
        z = "min(zoom+0.0007,1.06)" if i % 2 else "if(eq(on,0),1.06,max(zoom-0.0007,1.0))"
        segs.append(
            f"ffmpeg -v error -y -loop 1 -i f_{i:02d}.png -i a_{i:02d}.wav "
            f"-filter_complex \"[0:v]scale=1620:2880,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s={W}x{H}:fps=30,format=yuv420p[v];"
            f"[1:a]apad=pad_dur={GAP},loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]\" "
            f"-map \"[v]\" -map \"[a]\" -t {dur:.3f} -c:v libx264 -preset medium -crf 20 -c:a aac -b:a 192k s_{i:02d}.mp4"
        )
    concat = "\n".join(f"file 's_{i:02d}.mp4'" for i in range(1, n + 1))
    script = (f"set -e; cd ~/{rd}; " + "; ".join(segs) +
              f"; printf \"{concat}\\n\" > list.txt; ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy {slug}.mp4;"
              f" ffprobe -v error -show_entries format=duration -of csv=p=0 {slug}.mp4; md5sum {slug}.mp4 | cut -c1-32")
    r = ssh(script, timeout=1800)
    if r.returncode != 0:
        raise SystemExit(f"렌더 실패 {slug}: {r.stderr[-800:]}")
    dur_remote, md5_remote = r.stdout.strip().splitlines()[-2:]
    subprocess.run(["rsync", "-a", "-e", f"ssh -i {KEY}", f"{GPU}:{rd}/{slug}.mp4", str(out)], check=True)
    md5_local = hashlib.md5(out.read_bytes()).hexdigest()
    assert md5_local == md5_remote, f"md5 불일치 {md5_local} {md5_remote}"
    err = ssh(f"ffmpeg -v error -i ~/{rd}/{slug}.mp4 -f null - 2>&1 | wc -l").stdout.strip()
    print(f"  render {slug}: {float(dur_remote):.1f}초 · md5 {md5_local[:8]} · 디코드 오류 {err}")


# ── 메타데이터 ───────────────────────────────────────────────────
def step_meta(cfg, s):
    out = ROOT / "output" / "shorts" / f"{s['slug']}.metadata.json"
    url = f"https://www.youtube.com/watch?v={s['long_video']}"
    title = f"{s['book']} 줄거리 1분 요약 (결말 포함) | {s['author']} #shorts"
    desc = (f"『{s['book']}』({s['author']}) 줄거리를 1분으로 정리했습니다. 결말까지 포함합니다.\n\n"
            f"▶ 전체 해설 본편: {url}\n\n"
            f"#{s['book'].replace(' ', '')} #{s['book'].replace(' ', '')}줄거리 #책요약 #줄거리 #shorts")
    tags = [s["book"], f"{s['book']} 줄거리", f"{s['book']} 요약", f"{s['book']} 결말", f"{s['book']} 해설",
            s["author"], "줄거리", "책요약", "1분 요약", "고전 소설", "shorts"]
    meta = {"video_path": f"output/shorts/{s['slug']}.mp4", "title": title, "description": desc, "tags": tags,
            "language": "ko", "long_video": s["long_video"], "book": s["book"]}
    out.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  meta {s['slug']}: {title} ({len(title)}자)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("step", choices=["tts", "images", "frames", "thumb", "render", "meta", "all"])
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    cfg = json.loads((ROOT / a.config).read_text(encoding="utf-8"))
    items = [s for s in cfg["shorts"] if not a.only or s["slug"] in a.only]
    steps = ["tts", "images", "frames", "thumb", "render", "meta"] if a.step == "all" else [a.step]
    for st in steps:
        print(f"== {st}")
        for s in items:
            globals()[f"step_{st}"](cfg, s)


if __name__ == "__main__":
    main()

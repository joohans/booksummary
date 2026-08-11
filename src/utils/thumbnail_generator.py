"""
Flux 기반 썸네일 자동 생성 유틸리티
GPU 서버(192.168.0.150:9001)의 Flux API 호출
텍스트 오버레이는 PIL로 처리 (Flux는 한글 렌더링 불가)
프롬프트/훅 생성은 외부(Claude Code)에서 받아서 처리

Usage:
    from src.utils.thumbnail_generator import generate_thumbnail

    output_path = generate_thumbnail(
        book_title="죽음의 수용소에서",
        author="빅터 프랭클",
        language="ko",
        hook="극한의 고통 속에서 의미를 찾다",
        image_prompt="A lone man in a dark concentration camp...",
        output_dir="output/",
    )

CLI:
    python src/utils/thumbnail_generator.py \\
        --title-ko "죽음의 수용소에서" --title-en "Man's Search for Meaning" \\
        --author-ko "빅터 프랭클" --author-en "Viktor Frankl" \\
        --hook-ko "극한의 고통 속에서 의미를 찾다" \\
        --hook-en "Find meaning in suffering" \\
        --image-prompt-ko "A lone prisoner silhouette..." \\
        --image-prompt-en "A lone prisoner silhouette..."
"""

import base64
import os
import re
import sys
import time
import textwrap
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont
import io

FLUX_SERVER = os.getenv("FLUX_SERVER_URL", "http://192.168.0.150:9001")
FLUX_TIMEOUT = int(os.getenv("FLUX_TIMEOUT", "120"))

# 폰트 경로 (우선순위 순)
FONT_PATHS_BOLD = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONT_PATHS_REGULAR = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _load_font(paths: list[str], size: int) -> ImageFont.FreeTypeFont:
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _build_flux_prompt(image_prompt: str) -> str:
    """Flux용 최종 프롬프트: 순수 배경 이미지 (텍스트 없음)"""
    return (
        f"{image_prompt} "
        "YouTube thumbnail, 16:9 widescreen. "
        "Left side darker for text overlay area. "
        "Blue geometric accent lines on frame edges (#1A73E8). "
        "Cinematic lighting. Soft watercolor + fine ink pen style. "
        "NO text, NO letters, NO watermark, NOT photorealistic."
    )


def overlay_text(
    img: Image.Image,
    hook: str,
    author: str,
    book_title: str,
    language: str,
    tag: str | None = None,
) -> Image.Image:
    """PIL로 이미지 위에 텍스트 오버레이 — 크고 임팩트 있는 레이아웃"""
    W, H = img.size
    is_ko = language in ("ko", "kr")

    # 폰트 크기: 더 크게
    font_hook = _load_font(FONT_PATHS_BOLD, int(H * 0.115))   # 메인 훅: 크게
    font_title = _load_font(FONT_PATHS_BOLD, int(H * 0.060))  # 책 제목: 굵게
    font_author = _load_font(FONT_PATHS_REGULAR, int(H * 0.044))  # 저자명
    font_tag = _load_font(FONT_PATHS_BOLD, int(H * 0.032))    # 채널 태그

    # 전체 어두운 오버레이 (가독성 확보)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    # 전체에 반투명 어두운 레이어
    for x in range(W):
        # 좌측 70%는 강하게, 우측은 약하게
        if x < int(W * 0.70):
            alpha = int(195 * (1 - x / (W * 0.85)))
        else:
            alpha = int(80 * (1 - (x - W * 0.70) / (W * 0.30)))
        alpha = max(0, min(255, alpha))
        ov_draw.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    accent = "#FFD700"     # 골드 강조색
    blue = "#1A73E8"       # 파란 보조색

    # 상단/하단 강조선
    draw.rectangle([(0, 0), (W, int(H * 0.008))], fill=accent)
    draw.rectangle([(0, H - int(H * 0.008)), (W, H)], fill=accent)
    draw.rectangle([(0, 0), (int(W * 0.006), H)], fill=accent)

    pad_x = int(W * 0.05)
    text_w = int(W * 0.60)  # 텍스트 영역 최대 너비

    def draw_text_outline(pos, text, font, fill, outline_width=4):
        """텍스트 외곽선(stroke) 효과로 가독성 향상"""
        x, y = pos
        # 외곽선 (검정)
        for dx in range(-outline_width, outline_width + 1, 2):
            for dy in range(-outline_width, outline_width + 1, 2):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill="#000000EE")
        draw.text((x, y), text, font=font, fill=fill)

    def get_text_width(text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]

    def wrap_text_by_width(text, font, max_w):
        """너비 기준 텍스트 줄바꿈 — 명시적 \\n 존중, 어절(공백) 단위 우선 (한국어 중간 절단 방지)"""
        lines = []
        for seg in text.split("\n"):
            cur = ""
            for w in seg.split():
                test = (cur + " " + w) if cur else w
                if get_text_width(test, font) <= max_w:
                    cur = test
                    continue
                if cur:
                    lines.append(cur)
                # 어절 하나가 한 줄보다 길면 글자 단위로 분할
                while get_text_width(w, font) > max_w and len(w) > 1:
                    cut = len(w)
                    while cut > 1 and get_text_width(w[:cut], font) > max_w:
                        cut -= 1
                    lines.append(w[:cut])
                    w = w[cut:]
                cur = w
            if cur:
                lines.append(cur)
        return lines

    # ── 훅 문장 (메인 카피) — 중앙 상단 배치 ──
    hook_max_w = int(W * 0.58)
    hook_lines = wrap_text_by_width(hook, font_hook, hook_max_w)[:3]
    line_h = int(H * 0.128)
    total_hook_h = len(hook_lines) * line_h
    hook_start_y = int(H * 0.10)

    # 훅 배경 박스 (반투명)
    box_pad = int(H * 0.018)
    box_x1 = pad_x - box_pad
    box_y1 = hook_start_y - box_pad
    box_x2 = pad_x + hook_max_w + box_pad
    box_y2 = hook_start_y + total_hook_h + box_pad
    box_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    box_draw = ImageDraw.Draw(box_overlay)
    box_draw.rectangle([(box_x1, box_y1), (box_x2, box_y2)], fill=(0, 0, 0, 110))
    img = Image.alpha_composite(img.convert("RGBA"), box_overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    hook_y = hook_start_y
    for line in hook_lines:
        draw_text_outline((pad_x, hook_y), line, font_hook, "#FFFFFF", outline_width=4)
        hook_y += line_h

    # ── 구분선 ──
    sep_y = hook_y + int(H * 0.020)
    draw.rectangle([(pad_x, sep_y), (pad_x + int(W * 0.18), sep_y + 5)], fill=accent)

    # ── 책 제목 ──
    title_y = sep_y + int(H * 0.035)
    title_lines = wrap_text_by_width(book_title, font_title, int(W * 0.58))[:2]
    for line in title_lines:
        draw_text_outline((pad_x, title_y), line, font_title, "#FFD700", outline_width=3)
        title_y += int(H * 0.072)

    # ── 저자명 ──
    author_y = title_y + int(H * 0.010)
    draw_text_outline((pad_x, author_y), author, font_author, "#CCCCCC", outline_width=2)

    # ── 채널 태그 (하단) ──
    if not tag:
        tag = "핵심요약" if is_ko else "Book Summary"
    draw_text_outline((pad_x, H - int(H * 0.085)), tag, font_tag, accent, outline_width=2)

    return img


def check_server_health() -> bool:
    try:
        resp = requests.get(f"{FLUX_SERVER}/health", timeout=5)
        return resp.json().get("status") in ("ok", "ready")
    except Exception:
        return False


def generate_thumbnail(
    book_title: str,
    author: str,
    language: str,
    hook: str,
    image_prompt: str,
    output_dir: str | Path = "output",
    width: int = 1920,
    height: int = 1080,
    steps: int = 4,
    seed: int = -1,
    force: bool = False,
    tag: str | None = None,
) -> Path | None:
    """
    썸네일 생성 메인 함수

    Args:
        hook: 썸네일 메인 카피 (짧고 강렬하게, Claude Code가 생성)
        image_prompt: 배경 이미지 묘사 (영문, Claude Code가 생성)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_title = re.sub(r'[^\w가-힣]', '_', book_title).strip('_')
    lang_suffix = "ko" if language in ("ko", "kr") else "en"
    output_path = output_dir / f"{safe_title}_thumbnail_{lang_suffix}.jpg"

    if output_path.exists() and not force:
        print(f"썸네일 이미 존재: {output_path}")
        return output_path

    print(f"Flux 서버 확인 중 ({FLUX_SERVER})...")
    if not check_server_health():
        print(f"❌ Flux 서버 연결 불가: {FLUX_SERVER}", file=sys.stderr)
        return None

    flux_prompt = _build_flux_prompt(image_prompt)
    print(f"🎨 배경 이미지 생성 중... (hook: {hook})")

    start = time.time()
    try:
        resp = requests.post(
            f"{FLUX_SERVER}/generate",
            json={"prompt": flux_prompt, "width": width, "height": height,
                  "steps": steps, "seed": seed},
            timeout=FLUX_TIMEOUT,
        )
        resp.raise_for_status()
        result = resp.json()
    except requests.Timeout:
        print(f"❌ 타임아웃 ({FLUX_TIMEOUT}초)", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ 생성 실패: {e}", file=sys.stderr)
        return None

    img_b64 = result.get("image_base64", "")
    if not img_b64:
        print("❌ 응답에 이미지 없음", file=sys.stderr)
        return None

    img = Image.open(io.BytesIO(base64.b64decode(img_b64)))
    img = overlay_text(img, hook=hook, author=author,
                       book_title=book_title, language=language, tag=tag)
    img.save(output_path, format="JPEG", quality=95)

    elapsed = time.time() - start
    print(f"✅ 썸네일 저장: {output_path} ({elapsed:.1f}s, seed={result.get('seed', -1)})")
    return output_path


def generate_both_languages(
    book_title_ko: str,
    book_title_en: str,
    author_ko: str,
    author_en: str,
    hook_ko: str,
    hook_en: str,
    image_prompt_ko: str,
    image_prompt_en: str,
    output_dir: str | Path = "output",
    force: bool = False,
) -> dict[str, Path | None]:
    results = {}
    print("\n=== 한국어 썸네일 생성 ===")
    results["ko"] = generate_thumbnail(
        book_title=book_title_ko, author=author_ko, language="ko",
        hook=hook_ko, image_prompt=image_prompt_ko,
        output_dir=output_dir, force=force,
    )
    print("\n=== 영문 썸네일 생성 ===")
    results["en"] = generate_thumbnail(
        book_title=book_title_en, author=author_en, language="en",
        hook=hook_en, image_prompt=image_prompt_en,
        output_dir=output_dir, force=force,
    )
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Flux 썸네일 생성기")
    parser.add_argument("--title-ko", required=True)
    parser.add_argument("--title-en", required=True)
    parser.add_argument("--author-ko", default="")
    parser.add_argument("--author-en", default="")
    parser.add_argument("--hook-ko", required=True, help="한국어 훅 문장 (짧고 강렬하게)")
    parser.add_argument("--hook-en", required=True, help="영문 훅 문장")
    parser.add_argument("--image-prompt-ko", required=True, help="한국어판 배경 이미지 묘사 (영문)")
    parser.add_argument("--image-prompt-en", required=True, help="영문판 배경 이미지 묘사 (영문)")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--language", choices=["ko", "en", "both"], default="both")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--tag", default=None, help="좌하단 채널 태그 (기본: 핵심요약/Book Summary, 일당백은 '일당백' 지정)")
    args = parser.parse_args()

    if args.language == "both":
        results = generate_both_languages(
            args.title_ko, args.title_en,
            args.author_ko, args.author_en,
            args.hook_ko, args.hook_en,
            args.image_prompt_ko, args.image_prompt_en,
            args.output_dir, force=args.force,
        )
        for lang, path in results.items():
            print(f"{lang}: {path}")
    else:
        title = args.title_ko if args.language == "ko" else args.title_en
        author = args.author_ko if args.language == "ko" else args.author_en
        hook = args.hook_ko if args.language == "ko" else args.hook_en
        img_prompt = args.image_prompt_ko if args.language == "ko" else args.image_prompt_en
        path = generate_thumbnail(title, author, args.language, hook, img_prompt,
                                  args.output_dir, force=args.force, tag=args.tag)
        print(f"결과: {path}")

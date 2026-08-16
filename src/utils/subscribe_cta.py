"""
구독 유도 CTA (Call-to-Action) 오버레이 생성 모듈

영상 마지막 N초에 반투명 하단 바와 구독/좋아요 유도 텍스트를 표시합니다.
"""

from __future__ import annotations

import os
from typing import Optional, Tuple

# 언어별 CTA 텍스트
CTA_TEXT = {
    "ko": "이 영상이 도움이 되셨다면 구독과 좋아요 부탁드립니다!",
    "en": "If you enjoyed this, please subscribe and like!",
}

# 언어별 폰트 경로 우선순위 (macOS 우선, 렌더링은 리눅스 GPU 서버에서 도므로 리눅스 경로 필수)
FONT_PATHS = {
    "ko": [
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/AppleGothic.ttf",
        "/Library/Fonts/AppleGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    ],
    "en": [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
}


def _find_font(language: str) -> Optional[str]:
    """언어에 맞는 폰트 경로를 반환합니다."""
    paths = FONT_PATHS.get(language, FONT_PATHS["en"])
    for path in paths:
        if os.path.exists(path):
            return path
    # 영어 폰트로 fallback
    if language != "en":
        for path in FONT_PATHS["en"]:
            if os.path.exists(path):
                return path
    return None


def _get_text_size(draw, text: str, font) -> Tuple[int, int]:
    """텍스트 크기를 반환합니다. Pillow 구버전/신버전 호환."""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        # 구버전 Pillow (< 8.0)
        return draw.textsize(text, font=font)  # type: ignore[attr-defined]


def create_subscribe_cta_clip(
    duration: float = 20.0,
    language: str = "ko",
    resolution: Tuple[int, int] = (1920, 1080),
    opacity: float = 0.85,
    fade_in_duration: float = 1.5,
):
    """
    구독 유도 CTA 오버레이 클립 생성

    영상 하단에 반투명 검은 바와 구독 유도 텍스트를 표시하는 클립을 생성합니다.
    moviepy 구버전/신버전 모두 호환됩니다.

    Args:
        duration: CTA 표시 길이 (초, 기본값 20초)
        language: 언어 코드 ('ko' 또는 'en')
        resolution: 영상 해상도 (width, height)
        opacity: 배경 바의 불투명도 (0.0 ~ 1.0)
        fade_in_duration: 페이드 인 효과 길이 (초)

    Returns:
        moviepy ImageClip 또는 None (PIL/moviepy 없을 때)
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    # moviepy 버전별 import
    moviepy_fadein_fn = None
    try:
        from moviepy.editor import ImageClip  # type: ignore[import]
        try:
            from moviepy.video.fx.all import fadein as _fadein  # type: ignore[import]
            moviepy_fadein_fn = _fadein
        except Exception:
            pass
    except ImportError:
        try:
            from moviepy import ImageClip  # type: ignore[import]
            try:
                from moviepy.video.fx import FadeIn as _FadeIn  # type: ignore[import]
                moviepy_fadein_fn = _FadeIn
            except Exception:
                pass
        except ImportError:
            return None

    width, height = resolution
    bar_height = 120
    bar_y = height - bar_height
    font_size = 42

    # 배경 바 이미지 생성 (RGBA)
    bar_img = Image.new("RGBA", (width, bar_height))
    draw = ImageDraw.Draw(bar_img)

    # 반투명 검은 배경
    alpha = int(opacity * 255)
    draw.rectangle([(0, 0), (width, bar_height)], fill=(0, 0, 0, alpha))

    # 폰트 로드
    font_path = _find_font(language)
    font_obj = None
    if font_path:
        try:
            font_obj = ImageFont.truetype(font_path, font_size)
        except Exception:
            pass
    if font_obj is None:
        font_obj = ImageFont.load_default()

    # CTA 텍스트 (언어 fallback 포함)
    text = CTA_TEXT.get(language, CTA_TEXT["en"])

    # 텍스트 위치 계산 (수평 중앙, 수직 중앙)
    text_width, text_height = _get_text_size(draw, text, font_obj)
    x = (width - text_width) // 2
    y = (bar_height - text_height) // 2

    # 텍스트 그림자 (가독성 향상)
    draw.text((x + 2, y + 2), text, font=font_obj, fill=(0, 0, 0, 200))
    # 흰색 텍스트
    draw.text((x, y), text, font=font_obj, fill=(255, 255, 255, 255))

    # 전체 해상도의 투명 이미지 생성 (바를 하단에 배치)
    full_img = Image.new("RGBA", (width, height))
    full_img.paste(bar_img, (0, bar_y), bar_img)

    import numpy as np
    full_array = np.array(full_img)

    # moviepy ImageClip 생성
    cta_clip = ImageClip(full_array).set_duration(duration)

    # 페이드 인 효과
    if moviepy_fadein_fn is not None and fade_in_duration > 0 and fade_in_duration < duration:
        try:
            cta_clip = cta_clip.fx(moviepy_fadein_fn, fade_in_duration)
        except Exception:
            pass  # 페이드 인 실패 시 그냥 진행

    return cta_clip

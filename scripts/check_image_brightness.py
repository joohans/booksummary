#!/usr/bin/env python3
"""렌더 전 이미지 풀의 밝기 이상치를 걸러낸다.

너무 어두운 사진이 한 장 섞이면 영상에서 4초간 화면이 꺼진 것처럼 보인다
(「수난이대」 실측: 평균밝기 9.8인 목발 클로즈업 1장이 64~67초를 검게 만들었다).
렌더는 1시간 이상 걸리므로 반드시 렌더 전에 돌린다.

사용법:
    .venv/bin/python scripts/check_image_brightness.py assets/images/<영문제목>
    .venv/bin/python scripts/check_image_brightness.py assets/images/<영문제목> --move
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

from PIL import Image, ImageStat

# 평균밝기 임계값 — 이 아래면 영상에서 '검은 화면'으로 읽힌다
DARK_THRESHOLD = 30.0
# 반대쪽 이상치 — 거의 흰 화면
BRIGHT_THRESHOLD = 245.0


def measure(path: Path) -> tuple[float, float]:
    stat = ImageStat.Stat(Image.open(path).convert("L"))
    return stat.mean[0], stat.stddev[0]


def main() -> int:
    ap = argparse.ArgumentParser(description="이미지 풀 밝기 이상치 검사")
    ap.add_argument("image_dir", help="검사할 이미지 디렉터리")
    ap.add_argument(
        "--move",
        action="store_true",
        help="이상치를 _rejected/ 로 옮긴다 (기본은 보고만)",
    )
    ap.add_argument("--dark-threshold", type=float, default=DARK_THRESHOLD)
    ap.add_argument("--bright-threshold", type=float, default=BRIGHT_THRESHOLD)
    args = ap.parse_args()

    d = Path(args.image_dir)
    files = sorted(d.glob("*.jpg"))
    if not files:
        print(f"❌ 이미지가 없습니다: {d}")
        return 1

    rows = [(*measure(f), f) for f in files]
    median = statistics.median(r[0] for r in rows)

    dark = [r for r in rows if r[0] < args.dark_threshold]
    bright = [r for r in rows if r[0] > args.bright_threshold]

    print(f"총 {len(rows)}장 · 평균밝기 중간값 {median:.1f}")

    for label, group in (("너무 어두움", dark), ("너무 밝음", bright)):
        if not group:
            continue
        print(f"\n⚠️  {label} {len(group)}장:")
        for mean, stddev, f in sorted(group, key=lambda r: r[0]):
            print(f"    {mean:6.1f}  σ{stddev:5.1f}  {f.name}")

    outliers = dark + bright
    if not outliers:
        print("\n✅ 이상치 없음 — 렌더 진행 가능")
        return 0

    if args.move:
        rejected = d / "_rejected"
        rejected.mkdir(exist_ok=True)
        for _, _, f in outliers:
            f.rename(rejected / f.name)
        print(f"\n📦 {len(outliers)}장을 {rejected}/ 로 옮겼습니다 → 남은 {len(rows) - len(outliers)}장")
        return 0

    print(f"\n실제로 제거하려면 --move 를 붙여 다시 실행하세요.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

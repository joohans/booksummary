#!/usr/bin/env python3
"""무드 이미지를 밝기 교차 배치로 재명명 — 검은 화면 연속을 막는다.

렌더러는 glob("mood_*.jpg") 를 파일명 순서 그대로 순환시킨다(셔플 없음).
어두운 컷이 몰리면 니코마코스의 "20초 검은 화면"이 재현되므로,
밝기 오름차순 → 절반씩 나눠 밝은/어두운 교차 → mood_001..NNN 으로 재명명한다.
원본 매핑은 image_order.json 에 남긴다. ([[project_render_image_order]])

사용법: reorder_by_brightness.py <이미지디렉터리>
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageStat


def main() -> None:
    d = Path(sys.argv[1])
    files = sorted(d.glob("mood_*.jpg"))
    if not files:
        sys.exit("mood_*.jpg 가 없다")

    stats = []
    for f in files:
        im = Image.open(f).convert("L")
        st = ImageStat.Stat(im)
        stats.append((st.mean[0], st.stddev[0], f))
    stats.sort(key=lambda x: x[0])

    half = len(stats) // 2
    dark, bright = stats[:half], stats[half:]
    order = []
    for i in range(max(len(dark), len(bright))):
        if i < len(bright):
            order.append(bright[i])
        if i < len(dark):
            order.append(dark[i])

    # 2단계 rename (이름 충돌 방지)
    tmp = []
    for i, (mean, sd, f) in enumerate(order, 1):
        t = d / f".stage_{i:03d}.jpg"
        f.rename(t)
        tmp.append((t, i, mean, sd, f.name))
    mapping = []
    for t, i, mean, sd, orig in tmp:
        final = d / f"mood_{i:03d}.jpg"
        t.rename(final)
        mapping.append({"index": i, "file": final.name, "original": orig,
                        "brightness": round(mean, 1), "stddev": round(sd, 1)})

    (d / "image_order.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    # 검증: 밝기 30 미만 컷의 최대 연속
    run = best = 0
    for m in mapping:
        run = run + 1 if m["brightness"] < 30 else 0
        best = max(best, run)
    bs = [m["brightness"] for m in mapping]
    print(f"{len(mapping)}장 재배치 · 밝기 중간값 {sorted(bs)[len(bs)//2]:.1f} "
          f"(최소 {min(bs):.1f} / 최대 {max(bs):.1f})")
    print(f"밝기 30 미만 {sum(1 for b in bs if b < 30)}장, 최대 연속 {best}장 "
          f"({best * 4.5:.1f}초)")


if __name__ == "__main__":
    main()

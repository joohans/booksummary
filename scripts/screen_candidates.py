#!/usr/bin/env python3
"""후보 제안어 스크리닝 — 무료(유튜브 자동완성)만 쓴다.

계량(search.list)은 호출당 100 units 라 전부 재면 쿼터가 날아간다.
먼저 **제안어로 검색 의도를 걸러** 통과분만 `measure_search_supply.py` 로 넘긴다.
→ [[project_selection_criteria]] 「제안어 스크리닝 먼저」 절차

⚠️ **비율로 자르지 말 것 (2026-09-13 실측).** 0.4 로 자르면 원미동 사람들(0.31)도 탈락한다.
   자동 통과한 5건은 수요가 110~370 이었고(「논 이야기」 함정), 「의도 약함」으로 떨어진
   허생전·양반전·이생규장전이 상위였다. **비율은 참고값이고 판정은 제안어를 눈으로 읽어서 한다.**

읽는 법:
  ★ 제안어 13개(자동완성 상한)가 꽉 참      = 수요가 크다는 신호
  ★ 교과서 출판사(미래엔·비상·창비)·중2·내신·수특 = 매년 반복되는 학교 수요 (최상)
  ⛔ 제안어 0개                          = 측정 불가(비속어 제목) 또는 무검색
  ⛔ 동음이의가 상위를 채움                 = 치숙→치수괴사 / 오발탄→소곱창전골 / 붉은 산→붉은 산호초
  ⛔ 각색물(영화·드라마·노래)이 책보다 많음     = 그 검색어를 각색물이 가져간다

사용법:
    .venv/bin/python scripts/screen_candidates.py --file titles.txt
    .venv/bin/python scripts/screen_candidates.py --titles "삼포 가는 길" "오발탄"
"""
import argparse
import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("supply", ROOT / "scripts/measure_search_supply.py")
sup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sup)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--titles", nargs="+")
    ap.add_argument("--file")
    ap.add_argument("--min-ratio", type=float, default=0.4)
    ap.add_argument("--sleep", type=float, default=0.6)
    args = ap.parse_args()

    titles = args.titles or []
    if args.file:
        titles += [l.strip() for l in Path(args.file).read_text(encoding="utf-8").splitlines()
                   if l.strip() and not l.startswith("#")]
    if not titles:
        return ap.error("--titles 또는 --file 필요")

    passed, dropped = [], []
    print(f"{len(titles)}건 스크리닝 (무료 · 자동완성)\n")
    print(f"{'제목':24}{'제안':>4}{'책':>4}{'각색':>5}{'비율':>7}  판정")
    print("-" * 78)
    for t in titles:
        d = sup.demand(t)
        if d["n_sug"] == 0:
            v = "⛔ 제안어 0 (측정불가)"
        elif d.get("n_adapt", 0) > d["n_book"]:
            v = f"⛔ 각색물 우세 ({d['sug_sample'][:2]})"
        elif d["book_ratio"] >= args.min_ratio:
            v = "✅ 계량 대상"
        else:
            v = "⚠️ 의도 약함"
        (passed if v.startswith("✅") else dropped).append(t)
        print(f"{t:24}{d['n_sug']:>4}{d['n_book']:>4}{d.get('n_adapt',0):>5}{d['book_ratio']:>7.2f}  {v}")
        time.sleep(args.sleep)

    print(f"\n통과 {len(passed)} / 탈락 {len(dropped)}")
    if passed:
        print("\n계량 명령:")
        print('  .venv/bin/python scripts/measure_search_supply.py --titles ' +
              " ".join(f'"{t}"' for t in passed))
    return 0


if __name__ == "__main__":
    sys.exit(main())

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

    # 교과서 수요 신호 — 제안어에 이것이 보이면 매년 반복되는 학교 수요다
    SCHOOL = ("미래엔", "비상", "창비", "천재", "지학사", "해냄", "동아",
              "내신", "수특", "수능특강", "중1", "중2", "중3", "고1", "고2", "고3", "세특")

    rows = []
    print(f"{len(titles)}건 스크리닝 (무료 · 자동완성)\n")
    for t in titles:
        d = sup.demand(t)
        school = [k for k in SCHOOL if any(k in s for s in d["sug_sample"])]
        if d["n_sug"] == 0:
            v = "⛔ 제안어 0 (측정불가)"
        elif d.get("n_adapt", 0) > d["n_book"]:
            v = "⛔ 각색물 우세"
        elif school:
            v = f"★ 교과서 신호 ({'·'.join(school[:3])})"
        elif d["n_sug"] >= 10:
            v = "✅ 제안어 상한 — 수요 신호"
        elif d["book_ratio"] >= args.min_ratio:
            v = "✅ 의도 깨끗"
        else:
            v = "⚠️ 판단 필요"
        rows.append((t, d, v))
        # ★ 제안어는 **항상** 찍는다. 비율만 보고 자르면 판정이 뒤집힌다(2026-09-13 실측)
        print(f"■ {t}  (제안 {d['n_sug']} · 책 {d['n_book']} · 각색 {d.get('n_adapt', 0)} · "
              f"비율 {d['book_ratio']:.2f})  {v}")
        if d["sug_sample"]:
            print(f"   {' / '.join(d['sug_sample'])}")
        time.sleep(args.sleep)

    drop = [t for t, _, v in rows if v.startswith("⛔")]
    keep = [t for t, _, v in rows if not v.startswith("⛔")]
    print(f"\n⛔ 명백한 탈락 {len(drop)} / 나머지 {len(keep)}")
    print("⚠️ 「나머지」는 통과가 아니라 **눈으로 볼 대상**이다 — 비율이 낮아도 제안어가 좋으면 살린다")
    if keep:
        print("\n수요 계량(다음 단계):")
        print("  .venv/bin/python scripts/measure_search_demand.py --provider naver --titles " +
              " ".join(f'"{t}"' for t in keep))
    return 0


if __name__ == "__main__":
    sys.exit(main())

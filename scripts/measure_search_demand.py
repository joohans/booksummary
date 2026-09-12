#!/usr/bin/env python3
"""책 제목의 한국어 **검색 수요**를 계량한다. (공급 측은 `measure_search_supply.py`)

왜 필요한가 (2026-09-08):
  기존 `measure_search_supply.py` 는 **공급**(경쟁 영상 조회수)만 잰다. 그래서 경쟁이
  낮은 이유가 "공급이 적어서"인지 "아무도 안 찾아서"인지 가르지 못했다.
  검증 결과 경쟁 중간값은 실제 성과와 무상관이었다(두 표본에서 ρ≈0).
  「파이프 이야기」는 경쟁 0 = '경쟁낮음' 판정을 받고도 조회 꼴찌(11회)였다.
  → 수요 축을 따로 재서 그 둘을 가른다.

제공자 두 가지:

  **naver** (권장, 키 필요) — 검색광고 키워드도구. **월간 절대 검색수**를 준다.
    앵커 정규화가 필요 없고 하위 구간(월 수십 회)까지 해상도가 나온다.
    `.env` 에 NAVER_AD_API_KEY / NAVER_AD_SECRET_KEY / NAVER_AD_CUSTOMER_ID 필요.
    발급: https://searchad.naver.com → 도구 > API 사용 관리 (무료)

  **trends** (키 불필요, 기본) — Google Trends. **상대값(0~100)** 이라 공통 앵커로
    정규화한다. 두 가지 한계가 실측으로 확인됐다(2026-09-08):
      1) 앵커보다 훨씬 작은 키워드는 **0 으로 반올림**된다. 「노인과 바다」를 앵커로 쓰자
         20편 중 9편이 0 이 됐고 그 안에 조회 11회와 297회가 섞여 구분되지 않았다
      2) **20~30건이면 429** 로 IP 가 몇 시간 막힌다. 요청 간 45초를 둬도 마찬가지다
    → 소량 확인용으로는 쓸 만하지만, 후보 수십 건 계량에는 naver 를 쓸 것

사용:
    .venv/bin/python scripts/measure_search_demand.py --titles "만세전" "수난이대"
    .venv/bin/python scripts/measure_search_demand.py --file books.txt --provider naver
    .venv/bin/python scripts/measure_search_demand.py --validate   # 성숙 표본으로 지표 검증
"""
import argparse
import json
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── 앵커 ────────────────────────────────────────────────────────────────────
# Trends 는 요청 내 최대값을 100 으로 스케일하므로, 앵커가 대상보다 훨씬 크면
# 대상이 0 으로 반올림돼 버린다. 2026-09-08 실측: 「노인과 바다」를 앵커로 쓰자
# 20편 중 9편이 0 이 됐고 그 안에 조회 11회와 297회가 섞여 구분이 되지 않았다.
# → 우리가 다루는 구간(무명 근대 단편)에 맞는 **작은 앵커**를 기본으로 쓴다.
ANCHOR = "물고기는 존재하지 않는다"
# 큰 앵커 기준으로 환산하고 싶을 때 곱하는 값 (노인과 바다 = 1.0 스케일)
ANCHOR_TO_BIG = 0.091
TIMEFRAME = "today 12-m"
GEO = "KR"
SLEEP = 45         # 요청 간 대기. 8초로 하면 20건쯤에서 429 가 난다(9/08 실측)
RETRY = 3
RETRY_SLEEP = 90

# 지표 검증용 — 경과 152~218일의 성숙 표본 20편과 실제 조회수.
# 공개일이 다르면 조회수를 비교할 수 없어 경과일이 비슷한 것만 골랐다.
VALIDATION = [
    ("특이점이 온다", 1438), ("종의 기원", 501), ("인간 실격", 302), ("도파민네이션", 297),
    ("괴테는 모든 것을 말했다", 196), ("살인자의 기억법", 148), ("쇼펜하우어의 아포리즘", 123),
    ("까르마조프가의 형제들", 123), ("노인과 바다", 101), ("프로젝트 헤일메리", 81),
    ("세상에 마음 주지 마라", 71), ("도둑맞은 집중력", 70), ("미드나잇 라이브러리", 67),
    ("이처럼 사소한 것들", 52), ("물고기는 존재하지 않는다", 34), ("세계의 단편", 31),
    ("To Kill a Mockingbird", 29), ("북 오브 러브", 27), ("세이노의 가르침", 17),
    ("파이프 이야기", 11),
]


def fetch(titles: list[str]) -> dict[str, float]:
    """앵커와 **1:1로만** 비교해 앵커=1.0 기준의 수요를 돌려준다.

    ⛔ 한 요청에 4~5개를 몰아넣으면 안 된다(2026-09-08 실측). Trends 는 요청 내 최대값을
    100 으로 스케일하므로, 배치에 수요가 큰 키워드가 하나 있으면 **앵커가 1~2 로 뭉개져**
    같은 배치의 나머지가 전부 과대·과소 평가된다. 실제로 앵커 원값이 배치마다
    1.5~45.7(±97%)로 흔들렸고, 「도파민네이션」(실제 297회)이 수요 0 으로 나왔다.
    요청 수는 늘지만 1:1 이 유일하게 스케일이 일관된다.
    """
    from pytrends.request import TrendReq

    targets = [t for t in titles if t != ANCHOR]
    out: dict[str, float] = {ANCHOR: 1.0}

    for i, t in enumerate(targets, 1):
        df = None
        for attempt in range(RETRY):
            try:
                # 매 요청마다 새 세션을 만든다 — 세션을 재사용하면 429 가 빨리 온다
                py = TrendReq(hl="ko", tz=540)
                py.build_payload([ANCHOR, t], timeframe=TIMEFRAME, geo=GEO)
                df = py.interest_over_time()
                break
            except Exception as e:
                if attempt == RETRY - 1:
                    print(f"   [{i}/{len(targets)}] {t:24} ❌ {str(e)[:60]}", file=sys.stderr)
                else:
                    time.sleep(RETRY_SLEEP)
        if df is None:
            time.sleep(SLEEP)
            continue
        if df.empty or ANCHOR not in df.columns:
            print(f"   [{i}/{len(targets)}] {t:24} 데이터 없음 → 0")
            out[t] = 0.0
            time.sleep(SLEEP)
            continue
        a = float(df[ANCHOR].mean())
        v = float(df[t].mean()) if t in df.columns else 0.0
        out[t] = round(v / a, 3) if a > 0 else 0.0
        # 앵커가 뭉개졌다 = 대상이 앵커보다 훨씬 크다. 값은 유효하지만 정밀도가 낮다
        flag = "  ⚠️앵커뭉개짐(대상이 훨씬 큼)" if a < 5 else ""
        print(f"   [{i}/{len(targets)}] {t:24} {out[t]:>8.3f}  (앵커 {a:.1f}){flag}")
        time.sleep(SLEEP)
    return out


def fetch_naver(titles: list[str]) -> dict[str, float]:
    """네이버 검색광고 키워드도구로 **월간 절대 검색수**(PC+모바일)를 받는다.

    Trends 와 달리 앵커가 필요 없고 하위 구간 해상도가 나온다.
    키워드도구는 공백을 제거하고 대문자로 정규화한 형태를 키로 돌려주므로 그에 맞춰 대조한다.
    """
    import base64
    import hashlib
    import hmac
    import os
    import urllib.parse
    import urllib.request

    try:
        from dotenv import load_dotenv
        load_dotenv(str(ROOT / ".env"))
    except ImportError:
        pass

    key = os.getenv("NAVER_AD_API_KEY")
    secret = os.getenv("NAVER_AD_SECRET_KEY")
    customer = os.getenv("NAVER_AD_CUSTOMER_ID")
    if not (key and secret and customer):
        print("❌ 네이버 검색광고 API 키가 없다. `.env` 에 아래 세 개를 넣을 것:\n"
              "   NAVER_AD_API_KEY / NAVER_AD_SECRET_KEY / NAVER_AD_CUSTOMER_ID\n"
              "   발급: https://searchad.naver.com → 도구 > API 사용 관리 (무료)",
              file=sys.stderr)
        return {}

    BASE, PATH = "https://api.naver.com", "/keywordstool"

    def signed_headers() -> dict[str, str]:
        ts = str(int(time.time() * 1000))
        msg = f"{ts}.GET.{PATH}"
        sig = base64.b64encode(
            hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest()
        ).decode()
        return {"X-Timestamp": ts, "X-API-KEY": key,
                "X-Customer": str(customer), "X-Signature": sig}

    def norm(s: str) -> str:
        return s.replace(" ", "").upper()

    out: dict[str, float] = {}
    # 키워드도구는 요청당 힌트 키워드 5개까지 받는다
    for i in range(0, len(titles), 5):
        chunk = titles[i : i + 5]
        q = urllib.parse.urlencode({"hintKeywords": ",".join(norm(t) for t in chunk),
                                    "showDetail": "1"})
        req = urllib.request.Request(f"{BASE}{PATH}?{q}", headers=signed_headers())
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                rows = json.load(r).get("keywordList", [])
        except Exception as e:
            print(f"   ⚠️ 실패 {chunk}: {type(e).__name__} {str(e)[:80]}", file=sys.stderr)
            continue
        by = {row["relKeyword"]: row for row in rows}
        for t in chunk:
            row = by.get(norm(t))
            if not row:
                out[t] = 0.0
                print(f"   {t:24} 결과 없음 → 0")
                continue

            def cnt(v) -> float:
                # 검색수가 10 미만이면 "< 10" 문자열로 온다
                if isinstance(v, str):
                    return 5.0 if "<" in v else float(v or 0)
                return float(v or 0)

            total = cnt(row.get("monthlyPcQcCnt")) + cnt(row.get("monthlyMobileQcCnt"))
            out[t] = total
            print(f"   {t:24} {total:>9,.0f} 회/월")
        time.sleep(0.4)
    return out


def spearman(xs: list[float], ys: list[float]) -> float:
    n = len(xs)

    def ranks(vals, rev=False):
        order = sorted(range(n), key=lambda i: vals[i], reverse=rev)
        r = [0] * n
        for pos, i in enumerate(order, 1):
            r[i] = pos
        return r

    d2 = sum((a - b) ** 2 for a, b in zip(ranks(xs, rev=True), ranks(ys, rev=True)))
    return 1 - 6 * d2 / (n * (n * n - 1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--titles", nargs="+")
    ap.add_argument("--file")
    ap.add_argument("--provider", choices=["trends", "naver"], default="trends",
                    help="naver 권장(월간 절대 검색수, 키 필요) / trends 기본(상대값, 키 불필요)")
    ap.add_argument("--validate", action="store_true",
                    help="성숙 표본 20편으로 이 지표가 성과를 가르는지 검증")
    args = ap.parse_args()

    if args.validate:
        titles = [t for t, _ in VALIDATION]
    elif args.file:
        titles = [l.strip() for l in Path(args.file).read_text().splitlines() if l.strip()]
    elif args.titles:
        titles = args.titles
    else:
        print("--titles / --file / --validate 중 하나 필요", file=sys.stderr)
        return 1

    if args.provider == "naver":
        print(f"{len(titles)}건 측정 (네이버 검색광고, 월간 절대 검색수)\n")
        demand = fetch_naver(titles)
        unit = "회/월"
    else:
        print(f"{len(titles)}건 측정 (Google Trends, {TIMEFRAME}, geo={GEO}, 앵커=「{ANCHOR}」)")
        print(f"⏱ 요청 간 {SLEEP}초 대기 — {len(titles)}건이면 약 {len(titles)*SLEEP//60}분. "
              f"20~30건을 넘기면 429 로 IP 가 막힌다\n")
        demand = fetch(titles)
        unit = f"앵커({ANCHOR})=1"

    if not demand:
        return 1

    out = ROOT / f"data/search_demand_{args.provider}.json"
    # ⚠️ 덮어쓰지 말고 누적한다 — 2026-09-12 에 한 건만 재던 실행이
    #    기존 13건을 통째로 날린 적이 있다(커밋 직전 발견). 같은 제목은 최신값으로 갱신.
    merged = {}
    if out.exists():
        try:
            merged = json.loads(out.read_text())
        except json.JSONDecodeError:
            merged = {}
    merged.update(demand)
    out.write_text(json.dumps(merged, ensure_ascii=False, indent=1))
    print(f"\n저장: {out.relative_to(ROOT)} (누적 {len(merged)}건)")

    if not args.validate:
        print(f"\n{'제목':30}{unit:>16}")
        for t in titles:
            v = demand.get(t)
            print(f"{t[:28]:30}{'—' if v is None else f'{v:>16,.3f}'}")
        return 0

    # ── 검증 ───────────────────────────────────────────────────────────────
    actual = dict(VALIDATION)
    pairs = [(t, demand[t], actual[t]) for t in actual if t in demand]
    if len(pairs) < 5:
        print("측정된 항목이 너무 적어 검증 불가", file=sys.stderr)
        return 1

    rho = spearman([p[1] for p in pairs], [p[2] for p in pairs])
    print(f"\n■ 수요 지표 vs 실제 조회수  n={len(pairs)}")
    print(f"  Spearman ρ = {rho:+.3f}   (경쟁 지표는 같은 표본에서 −0.171 이었다)\n")
    print(f"{'책':26}{'수요':>8}{'조회':>7}")
    for t, d, v in sorted(pairs, key=lambda p: -p[1]):
        print(f"{t[:24]:26}{d:>8.3f}{v:>7}")

    zero = [t for t, d, _ in pairs if d < 0.05]
    if zero:
        print(f"\n수요 거의 0 ({len(zero)}건): {', '.join(zero)}")
        print(f"  → 그 편들의 실제 조회수: {[actual[t] for t in zero]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""책 제목별 '한국어 유튜브 공급'을 계량한다.

배경 (2026-08-24 Analytics 실측 — data/analytics_20260824.md):
  우리 조회수의 70%는 검색이고, 이기는 영상은 전부 **정확한 책 제목 검색**으로 이긴다.
    히치하이커 1,958회 중 검색 1,721회, 그 중 "은하수를 여행하는 히치하이커를
    위한 안내서" 한 검색어가 1,180회.
  즉 편당 성과 ≈ (그 책 제목의 한국어 검색 수요) × (우리가 상위에 걸리는지).
  기존 find_candidates_aladin.py 는 알라딘 판매순위(수요 대리지표)만 보고
  **공급(기존 한국어 영상)을 안 본다.** 이 스크립트가 그 공급을 잰다.

계량하는 것 (경쟁 영상 = 우리 채널 제외, 제목에 해당 책 제목이 들어간 영상):
  n_comp   경쟁 영상 수 (검색 상위 N개 중)
  v_max    경쟁 영상 최고 조회수  → 그 책에 실제 수요가 있다는 증거
  v_med    경쟁 영상 조회수 중간값 → 상위권에 걸리기 위해 넘어야 하는 선
  n_long   4분 이상 영상 수 (쇼츠 제외한 실질 경쟁)

해석 (2026-08-24 실측 10편으로 검증 — 자세한 근거는 아래 '판정 기준' 주석):
  v_med < 5,000    상위 진입 가능. 우리 최고 성과(히치하이커)가 2,644 였다
  v_med 4만 이상   전부 잔돈이었다(100~500회). 유명한 책일수록 여기 해당한다
  제안어           **사람이 읽는다.** 각색물·동명이인이 검색어를 가져가는지 보는 용도.
                   비율로 자동 판정하려는 시도는 실패했다(변형마다 결과가 뒤집힘)

쿼터: search.list 는 호출당 100 units (일일 10,000). 기본 25건 = 2,500 units.
업로드 1건이 1,600 units 이므로 업로드 예정일에는 --limit 을 줄일 것.

사용:
  .venv/bin/python scripts/measure_search_supply.py --titles "동물농장" "모비딕"
  .venv/bin/python scripts/measure_search_supply.py --file data/candidates.txt --limit 20
  .venv/bin/python scripts/measure_search_supply.py --validate   # 기존 업로드분으로 지표 검증
"""
import argparse
import json
import os
import re
import statistics
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 지표 검증용: 이미 올린 책 → 최근 90일 실제 조회수 (2026-08-24 Analytics)
# 상위권과 하위권을 섞어 넣어야 지표가 둘을 가르는지 볼 수 있다.
VALIDATION = [
    ("은하수를 여행하는 히치하이커를 위한 안내서", "더글러스 애덤스", 1958),
    ("모비딕", "허먼 멜빌", 516),
    ("나는 고양이로소이다", "나쓰메 소세키", 471),
    ("특이점이 온다", "커즈와일", 315),
    ("갈매기", "체호프", 208),
    ("종의 기원", "정유정", 191),
    ("오이디푸스 왕", "소포클레스", 143),
    ("톰 소여의 모험", "마크 트웨인", 121),
    ("빅 히스토리", "데이비드 크리스천", 106),
    ("순교자", "김은국", 118),
]

# ── 판정 기준 ──────────────────────────────────────────────────────────────
# 2026-08-24: '의도 비율'을 게이트로 자동화하려 여러 변형을 시도했으나 **전부 불안정했다.**
# 각색어(영화·OST·뮤지컬)를 음수로 세면 우리 1위(히치하이커, 1,958회)가 탈락하고,
# 양수로 세면 「픽션들」이 "픽션드라마"에 걸려 통과한다. 제안어가 4~14개뿐이라
# 비율의 분산이 너무 크다. n=10 에 과적합하는 것이므로 **합성 점수를 만들지 않는다.**
#
# 변형과 무관하게 방향이 일관된 것은 **경쟁 강도 하나**다:
#   히치하이커 2,644 → 1,958회 (우리 최고 성과)
#   모비딕 39,140 / 순교자 56,963 / 갈매기 587,931 → 전부 100~500회
#   1984 89,963 / 죄와 벌 98,243 / 동물농장 344,595 → 저조 예상 (10월 공개로 검증)
# 의도(모호성)는 **제안어를 사람이 눈으로 읽으면 즉시 판별된다** —
#   「동물농장 강아지·토리·미미」=SBS TV / 「갈매기살 맛집」=음식 / 「죄와 벌 SG워너비」=노래.
# 그래서 자동 판정은 경쟁만 하고, 의도는 제안어를 출력해 사람이 본다.
GATE_COMPETITION = 5000


def verdict(d: dict) -> str:
    if d.get("error"):
        return "측정실패"
    if d["v_med"] >= GATE_COMPETITION * 8:
        return "경쟁압도"
    if d["v_med"] >= GATE_COMPETITION:
        return "경쟁높음"
    if d["n_sug"] < 3:
        return "수요희박"
    return "경쟁낮음"


def norm(s: str) -> str:
    return re.sub(r"[\s·,.:;!?'\"\-—…()\[\]]", "", s.lower())


# ── 수요·의도 축: 유튜브 자동완성 ───────────────────────────────────────────
# 유튜브 API에는 검색량이 없다. 자동완성은 절대량을 주지 않지만
# **검색 의도**를 알려준다 — 그게 우리가 실제로 필요한 것이다.
#   「동물농장」 제안어: 동요·강아지·고양이·토리·미미·t1  → SBS TV 동물농장 수요
#   「갈매기」  제안어: 갈매기살·갈매기의 꿈·갈매기 소리  → 체호프와 무관
#   「히치하이커」제안어: 영화·42·책·ost·줄거리          → 작품 수요
# 즉 제목이 같아도 그 검색어를 치는 사람이 책을 찾는지가 갈린다. (2026-08-24)
SUGGEST = "https://suggestqueries.google.com/complete/search?client=youtube&ds=yt&hl=ko&q="

# 책을 찾는 사람이 붙이는 수식어. **토큰 단위로 맞춘다** —
# 부분 문자열로 두면 「픽션들」이 "픽션드라마"의 '드라마'에 걸려 통과한다 (2026-08-24 실측)
BOOK_INTENT = {
    "줄거리", "요약", "해석", "해설", "독후감", "감상문", "서평", "후기", "리뷰",
    "결말", "등장인물", "인물", "주제", "명언", "명대사", "책", "소설", "원작",
    "번역", "번역본", "완역", "오디오북", "낭독", "pdf", "epub", "작가", "저자",
    "비평", "분석", "배경", "의미", "상징", "문학",
}
# 각색물·동명이인 — 그 검색어를 **가져가는** 경쟁 개체다. 책 의도로 세면 안 된다.
#   브람스를 좋아하세요→드라마 OST / 드라큘라→뮤지컬 김준수 / 자기만의 방→웹드라마
#   나르치스와 골드문트→뮤지컬 / 폭풍의 언덕→심규선(노래) / 백년의 고독→넷플릭스·소주
ADAPTATION = {
    "영화", "드라마", "뮤지컬", "연극", "ost", "넷플릭스", "웹툰", "애니",
    "예고편", "몰아보기", "플리", "노래", "노래방", "커튼콜", "넘버",
}


def tokens(s: str) -> list:
    return re.split(r"[\s·,./]+", s.lower())


def suggest(q: str) -> list:
    """유튜브 자동완성 제안어. 응답은 EUC-KR JSONP."""
    try:
        raw = urllib.request.urlopen(SUGGEST + urllib.parse.quote(q), timeout=12).read()
    except Exception as e:
        # 조용한 0 은 "수요 없음"과 구별되지 않아 판정을 오염시킨다
        print(f"  ⚠ 자동완성 실패({q}): {type(e).__name__} {str(e)[:60]}", file=sys.stderr)
        return []
    m = re.search(r"window\.google\.ac\.h\((.*)\)", raw.decode("euc-kr", errors="replace"), re.DOTALL)
    if not m:
        return []
    try:
        return [x[0] for x in json.loads(m.group(1))[1]]
    except Exception:
        return []


def demand(title: str, author: str = "") -> dict:
    """제안어로 검색 의도를 잰다."""
    sugs = suggest(title)
    if not sugs:
        return {"n_sug": 0, "n_book": 0, "book_ratio": 0.0, "sug_sample": []}
    body = [s for s in sugs if norm(s) != norm(title)]  # 제목 자체는 제외
    n_book = n_adapt = 0
    for s in body:
        tk = set(tokens(s))
        if tk & ADAPTATION:
            n_adapt += 1
        elif tk & BOOK_INTENT or (author and norm(author) in norm(s)):
            n_book += 1
    return {
        "n_sug": len(body),
        "n_book": n_book,
        "n_adapt": n_adapt,
        "book_ratio": round(n_book / len(body), 2) if body else 0.0,
        "sug_sample": body[:8],
    }


def parse_duration(iso: str) -> int:
    """ISO8601 duration → 초."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def build_clients():
    from dotenv import load_dotenv
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    load_dotenv(str(ROOT / ".env"))
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("YOUTUBE_CLIENT_ID"),
        client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/youtube.readonly"],
    )
    creds.refresh(Request())
    yt = build("youtube", "v3", credentials=creds)
    mine = yt.channels().list(part="id", mine=True).execute()["items"][0]["id"]
    return yt, mine


def measure(yt, mine: str, title: str, depth: int = 25) -> dict:
    """한 책 제목의 경쟁 공급을 잰다."""
    try:
        r = yt.search().list(
            part="snippet", q=title, type="video", maxResults=depth,
            regionCode="KR", relevanceLanguage="ko", order="relevance",
        ).execute()
    except Exception as e:
        return {"title": title, "error": str(e)[:90]}

    key = norm(title)
    hits = [it for it in r.get("items", [])
            if it["snippet"]["channelId"] != mine
            and key in norm(it["snippet"]["title"])]
    if not hits:
        return {"title": title, "n_comp": 0, "v_max": 0, "v_med": 0, "n_long": 0,
                "n_raw": len(r.get("items", []))}

    ids = [h["id"]["videoId"] for h in hits]
    stats = []
    for i in range(0, len(ids), 50):
        resp = yt.videos().list(part="statistics,contentDetails",
                                id=",".join(ids[i:i + 50])).execute()
        for v in resp["items"]:
            stats.append((int(v["statistics"].get("viewCount", 0)),
                          parse_duration(v["contentDetails"].get("duration", ""))))
    views = [s[0] for s in stats] or [0]
    return {
        "title": title,
        "n_comp": len(stats),
        "v_max": max(views),
        "v_med": int(statistics.median(views)),
        "n_long": sum(1 for _, d in stats if d >= 240),
        "n_raw": len(r.get("items", [])),
    }


def show(rows, actual=None):
    print(f"\n{'제목':<30}{'경쟁중간':>9}{'제안':>5}{'책의도':>7}{'비율':>6}{'판정':>11}", end="")
    print(f"{'실제성과':>9}" if actual else "")
    print("-" * (77 if actual else 68))
    for d in rows:
        if d.get("error"):
            print(f"{d['title'][:28]:<30}  오류: {d['error'][:40]}")
            continue
        line = (f"{d['title'][:28]:<30}{d['v_med']:>9,}{d['n_sug']:>5}"
                f"{d['n_book']:>7}{d['book_ratio']:>6.2f}{verdict(d):>11}")
        if actual:
            line += f"{actual.get(d['title'], 0):>9,}"
        print(line)
    print("\n제안어 (검색 의도는 눈으로 판별한다 — 각색물·동명이인이 가져가는지 확인):")
    for d in rows:
        if not d.get("error") and d.get("sug_sample"):
            print(f"  {d['title'][:24]:<26} {', '.join(d['sug_sample'])}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--titles", nargs="+", help="측정할 책 제목")
    ap.add_argument("--file", help="한 줄에 한 제목씩 담긴 파일")
    ap.add_argument("--validate", action="store_true",
                    help="기존 업로드분으로 지표가 성과를 가르는지 검증")
    ap.add_argument("--depth", type=int, default=25, help="검색 상위 몇 개를 볼지")
    ap.add_argument("--limit", type=int, default=25, help="측정할 제목 수 상한(쿼터 보호)")
    args = ap.parse_args()

    if args.validate:
        names = [f"{t}|{a}" for t, a, _ in VALIDATION]
        actual = {t: v for t, _, v in VALIDATION}
    elif args.file:
        names = [l.strip() for l in Path(args.file).read_text().splitlines() if l.strip()]
        actual = None
    elif args.titles:
        names, actual = args.titles, None
    else:
        print("--titles / --file / --validate 중 하나 필요", file=sys.stderr)
        return 1

    names = names[:args.limit]
    print(f"{len(names)}건 측정 (search.list {len(names)}회 ≈ {len(names)*100:,} units)",
          file=sys.stderr)

    yt, mine = build_clients()
    rows = []
    for raw in names:
        t, _, a = raw.partition("|")
        t, a = t.strip(), a.strip()
        d = measure(yt, mine, t, args.depth)
        d.update(demand(t, a))
        rows.append(d)
    show(rows, actual)

    out = ROOT / "data" / "search_supply_latest.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    print(f"\n저장: {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

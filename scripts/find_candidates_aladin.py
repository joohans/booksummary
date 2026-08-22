#!/usr/bin/env python3
"""알라딘 판매 순위로 '아직 다루지 않은 책' 후보를 뽑는다.

배경 (2026-08-22 Analytics 실측):
  채널 조회수는 그 책의 한국어 검색 수요에 비례한다. 그리고 검색 수요는
  최신 베스트셀러가 아니라 **고전**에 몰려 있다.
    고전 13편 중간값 125회 vs 현대 자기계발 12편 중간값 28회 (4.5배)
  따라서 기본 조회 대상은 '고전' 분야(CategoryId 2105)다.
  전체 베스트셀러는 --category 로 따로 볼 수 있으나 성과 상한이 낮다.

중복 체크는 **YouTube API의 실제 영상 제목**을 기준으로 한다.
history.md 를 쓰면 안 된다 — 그 파일에는 '검토만 한 후보 목록'도 적혀 있어서
업로드하지 않은 책이 covered 로 잡힌다 (2026-08-22 실측: 「설득」「죄와 벌」 오탐).
제목 목록은 data/.video_titles_cache.json 에 캐시한다 (--refresh 로 갱신).

사용:
  .venv/bin/python scripts/find_candidates_aladin.py                # 고전 200위
  .venv/bin/python scripts/find_candidates_aladin.py --category 인문학
  .venv/bin/python scripts/find_candidates_aladin.py --limit 40
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "http://www.aladin.co.kr/ttb/api/ItemList.aspx"

CATEGORIES = {
    "고전": 2105, "인문학": 656, "소설": 1, "역사": 74,
    "과학": 987, "사회과학": 798, "에세이": 55889,
    "자기계발": 336, "경제경영": 170, "전체": 0,
}

# 영상으로 만들 수 없는 물건
EXCLUDE_ITEM = re.compile(
    r"만화|라이트노벨|세트|전\s*\d+\s*권|잡지|문제집|수험서|기출|워크북|다이어리|"
    r"캘린더|굿즈|화보|사전|도감|유아|그림책|스티커|컬러링|필사|일력|각본집|무크",
    re.IGNORECASE,
)
# 원전이 아닌 파생물(해설서·재해석)
EXCLUDE_DERIV = re.compile(
    r"어떻게 읽을 것인가|다시 읽는|반대한다|한 번도 안 읽어|한눈에 읽는|"
    r"읽는 법|입문|해설|강의|따라 읽기|쉽게 읽는|처음 읽는",
)
# 제목 앞뒤 장식
STRIP_PREFIX = re.compile(r"^(초판본|완역본|무삭제)\s*")
# 권 번호만 떼되, 공백을 필수로 요구한다.
# (\s* 로 두면 "1984" 같은 숫자 제목이 통째로 지워져 조용히 탈락한다 — 2026-08-22 버그)
STRIP_VOLUME = re.compile(r"\s+\d+$")


def core_title(t: str) -> str:
    t = re.sub(r"&[a-z]+;", " ", t).split(" - ")[0]
    t = re.sub(r"\([^)]*\)", " ", t)
    t = STRIP_PREFIX.sub("", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return STRIP_VOLUME.sub("", t).strip()


def norm(s: str) -> str:
    """비교용 정규화 — 공백·문장부호 제거."""
    return re.sub(r"[\s·,.:;!?'\"\-—…]", "", s.lower())


CACHE = ROOT / "data" / ".video_titles_cache.json"


def channel_titles(refresh: bool) -> list:
    """채널의 실제 영상 제목 (공개·예약·비공개 전부). 진실의 원천."""
    if CACHE.exists() and not refresh:
        return json.loads(CACHE.read_text())

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(str(ROOT / "secrets" / "credentials.json"))
    yt = build("youtube", "v3", credentials=creds)
    up = yt.channels().list(part="contentDetails", mine=True).execute()
    up = up["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    ids, tok = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=up,
                                    maxResults=50, pageToken=tok).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok:
            break

    titles = []
    for i in range(0, len(ids), 50):
        resp = yt.videos().list(part="snippet", id=",".join(ids[i:i + 50])).execute()
        titles += [v["snippet"]["title"] for v in resp["items"]]

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(titles, ensure_ascii=False))
    print(f"  영상 제목 {len(titles)}건 캐시 갱신", file=sys.stderr)
    return titles


def fetch(key: str, cid: int, pages: int):
    out = []
    for start in range(1, pages + 1):
        q = {
            "ttbkey": key, "QueryType": "Bestseller", "MaxResults": 50,
            "start": start, "SearchTarget": "Book",
            "output": "js", "Version": "20131101",
        }
        if cid:
            q["CategoryId"] = cid
        try:
            with urllib.request.urlopen(API + "?" + urllib.parse.urlencode(q), timeout=25) as r:
                d = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"  조회 실패(start={start}): {str(e)[:80]}", file=sys.stderr)
            break
        if d.get("errorMessage"):
            print(f"  API 오류: {d['errorMessage']}", file=sys.stderr)
            break
        items = d.get("item") or []
        if not items:
            break
        out += items
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="고전", choices=list(CATEGORIES))
    ap.add_argument("--pages", type=int, default=4, help="50건 단위 페이지 수 (기본 4 = 200위)")
    ap.add_argument("--limit", type=int, default=40, help="출력할 후보 수")
    ap.add_argument("--refresh", action="store_true", help="영상 제목 캐시 갱신")
    args = ap.parse_args()

    key = next((l.split("=", 1)[1].strip()
                for l in (ROOT / ".env").read_text().splitlines()
                if l.startswith("ALADIN_PARTNER_ID=")), None)
    if not key:
        print("ALADIN_PARTNER_ID 없음", file=sys.stderr)
        return 1

    titles = channel_titles(args.refresh)
    haystack = norm(" || ".join(titles))

    items = fetch(key, CATEGORIES[args.category], args.pages)
    print(f"[{args.category}] 베스트셀러 {len(items)}건 조회", file=sys.stderr)

    covered, cand, seen = [], [], set()
    for it in items:
        raw = it.get("title", "")
        ct = core_title(raw)
        if not ct or len(ct) < 2:
            continue
        if EXCLUDE_ITEM.search(raw) or EXCLUDE_DERIV.search(raw):
            continue
        n = norm(ct)
        if n in seen:
            continue
        seen.add(n)
        row = (it.get("bestRank") or 999, ct,
               it.get("author", "").split("(")[0].split(",")[0].strip())
        # 제목이 기존 카탈로그에 부분 일치해도 커버된 것으로 본다
        (covered if n in haystack else cand).append(row)

    # 후보 중, 이미 커버된 제목을 포함하는 이본(예: '오뒷세이아')도 제외
    cov_norms = [norm(t) for _, t, _ in covered if len(norm(t)) >= 3]
    def is_variant(t):
        n = norm(t)
        return any(cn in n or n in cn for cn in cov_norms)

    variants = [r for r in cand if is_variant(r[1])]
    cand = [r for r in cand if not is_variant(r[1])]

    print(f"\n■ 이미 다룬 책 {len(covered)}건 — 상위권 커버 확인용")
    for r, t, a in sorted(covered)[:10]:
        print(f"   {r:>3}위  {t[:34]:<36}{a[:18]}")

    if variants:
        print(f"\n■ 이본·다른 번역본으로 제외 {len(variants)}건: "
              + ", ".join(t for _, t, _ in sorted(variants)[:8]))

    print(f"\n■ 후보 {len(cand)}건")
    print(f"   {'순위':>4}  {'제목':<34}{'저자'}")
    print("   " + "-" * 66)
    for r, t, a in sorted(cand)[:args.limit]:
        print(f"   {r:>4}  {t[:33]:<34}{a[:24]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

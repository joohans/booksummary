#!/usr/bin/env python3
"""핵심요약 영상 제목에서 거짓 '5분' 표기와 중복·키워드 스터핑 제거.

  전: [핵심 요약] 시간의 역사: 스티븐 호킹 (5분 핵심 요약·AI 심층 분석)
  후: [핵심 요약] 시간의 역사: 스티븐 호킹 (AI 심층 분석)

일당백 제목은 건드리지 않는다 (포맷 고정 규칙).
기본 --dry-run, 실제 반영은 --apply.
snippet 갱신 시 description/tags/categoryId/defaultLanguage 를 그대로 되돌려주고,
localizations 는 기존 키(YouTube 자동 번역 id/en-US 포함)를 보존한 채 ko 제목만 맞춘다.
"""
import argparse
import re
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CREDS = Path(__file__).resolve().parent.parent / "secrets" / "credentials.json"


# 부제에서 걷어낼 토큰.
#  - 거짓 시간 약속: "5분 핵심 요약" / "5-min Summary"  (실제 12~15분)
#  - [핵심 요약] 접두사와 중복되는 문구
#  - title_generator 에서 제거한 장르별 키워드 접미 전량
_DROP_TOKENS = {
    # 시간 약속 / 중복
    "5분 핵심 요약", "5분핵심요약", "핵심 요약", "5-min summary", "5 min summary",
    "5-minute summary", "summary",
    # 한글 장르 접미
    "삶의 지혜", "행복", "고독", "습관", "감정", "성장",
    "핵심 전략", "실전 적용", "핵심 사건", "맥락", "교훈",
    "핵심 개념", "의미", "영향", "시어", "해석", "문장", "사유",
    "인사이트", "줄거리", "핵심 주제", "인물", "정리",
    # 영문 장르 접미
    "wisdom, happiness & solitude", "habits, mindset & growth",
    "key strategies & takeaways", "key events & lessons",
    "key ideas & impact", "imagery, emotion & interpretation",
    "quotes, ideas & insights", "plot, themes & characters",
    "key ideas & takeaways",
}


def clean_title(t: str) -> str:
    """괄호 안 부가 설명에서 거짓 시간 약속·중복·장르 키워드 접미를 제거."""
    def fix_paren(m):
        parts = [p.strip() for p in re.split(r"·", m.group(1)) if p.strip()]
        kept = [p for p in parts if p.lower() not in _DROP_TOKENS]
        return f"({' · '.join(kept)})" if kept else ""

    out = re.sub(r"\(([^()]*)\)", fix_paren, t)
    return re.sub(r"\s{2,}", " ", out).strip()


def _meaningful(old: str, new: str) -> bool:
    """공백·구분자 간격만 달라진 변경이면 False (쿼터 낭비 방지)."""
    norm = lambda s: re.sub(r"[\s·]+", "", s)
    return norm(old) != norm(new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제 반영 (기본: 미리보기)")
    ap.add_argument("--include-public", action="store_true",
                    help="공개 영상도 포함 (기본: 예약된 비공개만)")
    ap.add_argument("--limit", type=int, help="처리 편수 제한 (쿼터 분할용)")
    args = ap.parse_args()

    yt = build("youtube", "v3", credentials=Credentials.from_authorized_user_file(str(CREDS)))
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

    targets = []
    for i in range(0, len(ids), 50):
        resp = yt.videos().list(part="snippet,status,localizations",
                                id=",".join(ids[i:i + 50])).execute()
        for v in resp["items"]:
            t = v["snippet"]["title"]
            priv = v["status"]["privacyStatus"]
            scheduled = priv == "private" and v["status"].get("publishAt")
            if not (scheduled or (args.include_public and priv == "public")):
                continue
            if "일당백" in t or "1DANG100" in t:      # 포맷 고정 — 제외
                continue
            new = clean_title(t)
            if new != t and _meaningful(t, new):
                targets.append((v, t, new))

    if args.limit:
        targets = targets[: args.limit]

    print(f"대상 {len(targets)}편 (예상 쿼터 {len(targets) * 50:,}유닛)\n")
    for v, old, new in targets:
        tag = "예약" if v["status"].get("publishAt") else "공개"
        print(f"[{tag}] {v['id']}")
        print(f"  전({len(old):>2}자) {old}")
        print(f"  후({len(new):>2}자) {new}\n")

    if not args.apply:
        print("[미리보기] 실제 반영은 --apply")
        return 0

    ok = err = 0
    for v, old, new in targets:
        sn = v["snippet"]
        body = {
            "id": v["id"],
            "snippet": {
                "title": new,
                "description": sn.get("description", ""),
                "categoryId": sn.get("categoryId", "27"),
                "tags": sn.get("tags", []),
            },
        }
        if sn.get("defaultLanguage"):
            body["snippet"]["defaultLanguage"] = sn["defaultLanguage"]
        parts = "snippet"

        loc = v.get("localizations") or {}
        if "ko" in loc:
            loc = dict(loc)
            loc["ko"] = dict(loc["ko"], title=new)
            body["localizations"] = loc
            parts = "snippet,localizations"

        try:
            yt.videos().update(part=parts, body=body).execute()
            print(f"✅ {new}")
            ok += 1
        except Exception as e:
            print(f"❌ {v['id']}: {str(e)[:160]}")
            err += 1

    print(f"\n성공 {ok}편 / 실패 {err}편")
    return 0 if err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

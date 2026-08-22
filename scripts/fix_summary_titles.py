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


def clean_title(t: str) -> str:
    """괄호 안의 부가 설명에서 거짓·중복 문구를 제거."""
    def fix_paren(m):
        inner = m.group(1)
        parts = [p.strip() for p in re.split(r"·", inner) if p.strip()]
        drop = re.compile(
            r"^(5\s*분\s*핵심\s*요약|5-?Min(ute)?\s*Summary|핵심\s*주제|인사이트|정리)$",
            re.IGNORECASE,
        )
        kept = [p for p in parts if not drop.match(p)]
        return f"({'·'.join(kept)})" if kept else ""

    out = re.sub(r"\(([^()]*)\)", fix_paren, t)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제 반영 (기본: 미리보기)")
    ap.add_argument("--include-public", action="store_true",
                    help="공개 영상도 포함 (기본: 예약된 비공개만)")
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
            if new != t:
                targets.append((v, t, new))

    print(f"대상 {len(targets)}편\n")
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

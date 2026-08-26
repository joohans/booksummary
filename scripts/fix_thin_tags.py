#!/usr/bin/env python3
"""태그가 비었거나 깨진 편에 큐레이션 태그를 넣는다 (2026-08-25 감사 결과).

배경: 공개 455편 중 15편이 태그 10개 미만이었고, 남은 태그도 단어 샐러드였다
      ('Fast and Slow Book Daniel Kahneman Daniel Kahneman Author Psychology' 가 한 개 태그).
      유입의 70% 이상이 검색이라 태그·제목이 곧 성과다 → data/analytics_20260826.md

주의: videos().update(part='snippet') 은 snippet 전체를 덮어쓴다.
      기존 snippet 을 읽어 tags 만 바꿔 되돌려준다 (제목·설명·카테고리·언어 보존).

사용: .venv/bin/python scripts/fix_thin_tags.py [--apply]
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent

COMMON_KO = ["책요약", "책리뷰", "북튜브", "독서", "책추천"]
COMMON_EN = ["BookSummary", "BookReview", "BookTube", "Reading", "BookRecommendation"]

# 영상 ID → 태그. 한글 편은 한글 태그를 앞에, 영문 편은 영문 태그를 앞에 둔다.
PLAN = {
    # 생각에 관한 생각 (채널 조회 2위 편 포함)
    "EDfOZfYtCbI": ["생각에 관한 생각", "다니엘 카너먼", "카너먼", "시스템1 시스템2", "행동경제학",
                    "전망 이론", "휴리스틱", "인지 편향", "심리학 책", "노벨경제학상",
                    "Thinking Fast and Slow", "Daniel Kahneman"] + COMMON_KO,
    "GNTBUL9ic5k": ["Thinking Fast and Slow", "Daniel Kahneman", "Kahneman", "System 1 System 2",
                    "behavioral economics", "prospect theory", "heuristics", "cognitive bias",
                    "psychology book", "Nobel Prize economics"] + COMMON_EN,
    "ZDMd0kixj3Y": ["Thinking Fast and Slow", "Daniel Kahneman", "Kahneman", "System 1 System 2",
                    "behavioral economics", "prospect theory", "heuristics", "cognitive bias",
                    "psychology book", "book summary"] + COMMON_EN,
    # 괴델, 에셔, 바흐
    "cA-U5OXTugE": ["괴델 에셔 바흐", "괴델", "에셔", "바흐", "더글러스 호프스태터", "호프스태터",
                    "이상한 고리", "자기 참조", "불완전성 정리", "인공지능", "인지과학", "퓰리처상",
                    "Godel Escher Bach", "Douglas Hofstadter"] + COMMON_KO,
    "5Pe8jgivfYM": ["Godel Escher Bach", "Douglas Hofstadter", "Hofstadter", "strange loop",
                    "self reference", "incompleteness theorem", "artificial intelligence",
                    "cognitive science", "Pulitzer Prize"] + COMMON_EN,
    # 안데르센·그림 형제·페로 동화
    "N1JFwwSivQc": ["안데르센", "그림 형제", "페로", "안데르센 동화", "그림 동화", "페로 동화",
                    "동화", "민담", "고전 동화", "샤를 페로", "한스 크리스티안 안데르센",
                    "Andersen", "Grimm Brothers", "Perrault"] + COMMON_KO,
    # 지적 대화를 위한 넓고 얕은 지식
    "E1_YNjcnNKs": ["지적 대화를 위한 넓고 얕은 지식", "지대넓얕", "채사장", "인문학 입문",
                    "교양", "역사 경제 정치", "철학 입문", "인문교양",
                    "Broad and Shallow Knowledge"] + COMMON_KO,
    "AAVpwJnMaqY": ["Broad and Shallow Knowledge", "Chae Sajang", "liberal arts",
                    "humanities introduction", "general knowledge", "philosophy introduction",
                    "history economics politics"] + COMMON_EN,
    # 북 오브 러브 (닐 게이먼)
    "nmOJjNWEKX8": ["북 오브 러브", "닐 게이먼", "게이먼", "판타지 소설", "환상문학",
                    "The Book of Love", "Neil Gaiman"] + COMMON_KO,
    "qcpzNB7gPws": ["The Book of Love", "Neil Gaiman", "Gaiman", "fantasy novel",
                    "fantasy fiction"] + COMMON_EN,
    # 파이프 이야기 (우디 앨런)
    "FhNzjqLD_Dw": ["파이프 이야기", "우디 앨런", "앨런", "단편집", "유머 문학",
                    "The Pipe Stories", "Woody Allen"] + COMMON_KO,
    "VyzciodVpeI": ["The Pipe Stories", "Woody Allen", "Allen", "short stories",
                    "humor literature"] + COMMON_EN,
    # 살인자의 기억법 (김영하) — 영문 편
    "z5m1sakux1c": ["The Killer's Memorandum", "Kim Young-ha", "Youngha Kim", "Korean novel",
                    "Korean literature", "serial killer fiction", "memory loss novel"] + COMMON_EN,
    # THE 2028 GLOBAL INTELLIGENCE CRISIS
    "dR6lVLpQQws": ["2028 글로벌 인텔리전스 위기", "인공지능 위기", "AI 위기", "미래 예측",
                    "기술 전망", "AGI", "인공지능 책",
                    "THE 2028 GLOBAL INTELLIGENCE CRISIS"] + COMMON_KO,
    "mzhoCHi01Xg": ["THE 2028 GLOBAL INTELLIGENCE CRISIS", "global intelligence crisis",
                    "AI crisis", "artificial intelligence", "future forecast", "AGI",
                    "technology outlook"] + COMMON_EN,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제 적용 (없으면 미리보기)")
    args = ap.parse_args()

    load_dotenv(ROOT / ".env")
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("YOUTUBE_CLIENT_ID"),
        client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/youtube.force-ssl"],
    )
    creds.refresh(Request())
    yt = build("youtube", "v3", credentials=creds)

    ids = list(PLAN)
    items = {}
    for i in range(0, len(ids), 50):
        for v in yt.videos().list(part="snippet", id=",".join(ids[i:i + 50])).execute()["items"]:
            items[v["id"]] = v

    ok = fail = 0
    for vid, tags in PLAN.items():
        v = items.get(vid)
        if not v:
            print(f"❌ {vid} 조회 실패")
            fail += 1
            continue
        sn = v["snippet"]
        print(f"\n{vid}  {sn['title'][:58]}")
        print(f"   기존 {len(sn.get('tags', []))}개 → 신규 {len(tags)}개")
        if not args.apply:
            print(f"   {tags}")
            continue

        # snippet 전체를 되돌려준다 — tags 만 교체 (나머지 필드 보존)
        body = {
            "id": vid,
            "snippet": {
                "title": sn["title"],
                "description": sn["description"],
                "categoryId": sn["categoryId"],
                "tags": tags,
            },
        }
        for k in ("defaultLanguage", "defaultAudioLanguage"):
            if sn.get(k):
                body["snippet"][k] = sn[k]
        try:
            r = yt.videos().update(part="snippet", body=body).execute()
            got = len(r["snippet"].get("tags", []))
            # 판정은 update 응답으로 한다 (list 는 낡은 값을 돌려준다)
            print(f"   {'✅' if got == len(tags) else '⚠️'} 반영 {got}개")
            ok += got == len(tags)
        except Exception as e:  # noqa: BLE001
            print(f"   ❌ 실패: {e}")
            fail += 1

    if args.apply:
        print(f"\n성공 {ok} / 실패 {fail} / 총 {len(PLAN)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

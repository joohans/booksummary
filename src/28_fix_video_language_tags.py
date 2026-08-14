#!/usr/bin/env python3
"""
YouTube 영상의 defaultAudioLanguage 정정 및 소실된 태그 복구

배경:
    src/09_upload_from_metadata.py가 업로드 직후 videos.update(part='snippet')를
    호출하면서 snippet에 tags와 defaultAudioLanguage를 포함하지 않았다.
    YouTube API는 지정한 part를 통째로 교체하므로 두 필드가 삭제됐고,
    defaultAudioLanguage는 이후 YouTube의 오디오 자동 감지값(en-US)으로 채워졌다.

동작:
    - defaultAudioLanguage를 defaultLanguage에 맞게 정정 (한국어 영상의 en-US 등)
    - 태그가 비어 있으면 영상 제목에서 책 제목을 추출해 재생성
    - 로컬 output/*.metadata.json에 원본 태그가 있으면 그것을 우선 사용

사용:
    python src/28_fix_video_language_tags.py                 # 미리보기 (기본)
    python src/28_fix_video_language_tags.py --apply         # 실제 적용
    python src/28_fix_video_language_tags.py --apply --limit 50
    python src/28_fix_video_language_tags.py --apply --lang-only
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CREDENTIALS_PATH = PROJECT_ROOT / "secrets" / "credentials.json"
OUTPUT_DIR = PROJECT_ROOT / "output"

# videos.update 1회당 소모되는 API 쿼터 (일일 기본 한도 10,000)
QUOTA_PER_UPDATE = 50
DAILY_QUOTA = 10_000

# 제목에서 책 제목을 뽑아내는 패턴 (채널의 4가지 제목 포맷)
TITLE_PATTERNS = [
    # [일당백] 사랑의 학교 (Cuore · 배경지식...) / [핵심 요약] 원씽 (The ONE Thing · 5분...)
    re.compile(r"^\[(?:일당백|핵심 요약)\]\s*(.+?)\s*[(（]"),
    # [1DANG100] Cuore (Background...) / [Summary] Outlive (5-min...)
    re.compile(r"^\[(?:1DANG100|Summary)\]\s*(.+?)\s*[(（]"),
    # [한국어] 현명한 투자자 책 리뷰 | [Korean] ...
    re.compile(r"^\[한국어\]\s*(.+?)\s*책 리뷰"),
    # [English] The Gene Book Review
    re.compile(r"^\[English\]\s*(.+?)\s*Book Review"),
]

# 책 제목 뒤에 붙는 ": 저자명" 제거용
AUTHOR_SUFFIX = re.compile(r"\s*:\s*[^:]+$")


def load_tag_generator():
    """숫자로 시작하는 모듈명 때문에 importlib으로 로드."""
    spec = importlib.util.spec_from_file_location(
        "episode_metadata", PROJECT_ROOT / "src" / "20_create_episode_metadata.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate_episode_tags


def extract_book_title(video_title: str) -> Optional[str]:
    """영상 제목에서 책 제목을 추출한다."""
    for pattern in TITLE_PATTERNS:
        match = pattern.match(video_title)
        if match:
            title = match.group(1).strip()
            # "이기적 유전자: 리처드 도킨스" -> "이기적 유전자"
            title = AUTHOR_SUFFIX.sub("", title).strip()
            return title or None
    return None


def load_local_tags() -> Dict[str, List[str]]:
    """로컬 metadata.json에서 제목 -> 태그 매핑을 만든다."""
    tags_by_title: Dict[str, List[str]] = {}
    for path in OUTPUT_DIR.glob("*.metadata.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        title = data.get("title")
        tags = data.get("tags")
        if title and tags:
            tags_by_title[title.strip()] = tags
    return tags_by_title


def get_youtube_client():
    if not CREDENTIALS_PATH.exists():
        raise SystemExit(f"인증 파일이 없습니다: {CREDENTIALS_PATH}")
    creds = Credentials.from_authorized_user_file(str(CREDENTIALS_PATH))
    return build("youtube", "v3", credentials=creds)


def fetch_all_videos(youtube) -> List[Dict]:
    """채널의 모든 업로드 영상 snippet을 가져온다."""
    channel = youtube.channels().list(part="contentDetails", mine=True).execute()
    uploads_id = channel["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    video_ids: List[str] = []
    page_token = None
    while True:
        response = (
            youtube.playlistItems()
            .list(part="contentDetails", playlistId=uploads_id, maxResults=50, pageToken=page_token)
            .execute()
        )
        video_ids += [item["contentDetails"]["videoId"] for item in response["items"]]
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    # playlistItems에 중복이 섞여 있어 순서를 지키며 중복 제거
    video_ids = list(dict.fromkeys(video_ids))

    videos: List[Dict] = []
    for i in range(0, len(video_ids), 50):
        response = youtube.videos().list(part="snippet", id=",".join(video_ids[i : i + 50])).execute()
        videos += response["items"]
    return videos


def plan_fix(
    video: Dict,
    local_tags: Dict[str, List[str]],
    generate_tags,
    lang_only: bool,
) -> Optional[Tuple[Dict, List[str]]]:
    """
    이 영상에 필요한 수정을 계산한다.

    Returns:
        (수정된 snippet, 수정 사유 목록) 또는 수정 불필요 시 None
    """
    snippet = video["snippet"]
    title = snippet["title"]
    default_lang = snippet.get("defaultLanguage")
    if not default_lang:
        return None  # 기준 언어가 없으면 판단 불가 — 건드리지 않는다

    base_lang = default_lang.split("-")[0]
    reasons: List[str] = []
    new_snippet = {
        "title": title,
        "description": snippet.get("description", ""),
        "categoryId": snippet.get("categoryId", "22"),
        "defaultLanguage": default_lang,
        "defaultAudioLanguage": snippet.get("defaultAudioLanguage"),
        "tags": snippet.get("tags", []),
    }

    # 1) 오디오 언어가 기준 언어와 다르면 정정
    audio_lang = snippet.get("defaultAudioLanguage")
    if not audio_lang or not audio_lang.startswith(base_lang):
        new_snippet["defaultAudioLanguage"] = default_lang
        reasons.append(f"audio {audio_lang or 'None'} -> {default_lang}")

    # 2) 태그가 비었으면 복구
    if not lang_only and not snippet.get("tags"):
        restored = local_tags.get(title.strip())
        source = "local"
        if not restored:
            book_title = extract_book_title(title)
            if book_title:
                try:
                    restored = generate_tags(book_title, base_lang)
                    source = f"regen({book_title})"
                except Exception as exc:  # 태그 생성 실패는 건너뛴다
                    print(f"      ⚠️ 태그 재생성 실패 [{title[:30]}]: {exc}")
                    restored = None
        if restored:
            new_snippet["tags"] = restored
            reasons.append(f"tags 0 -> {len(restored)} ({source})")

    return (new_snippet, reasons) if reasons else None


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube 영상 언어/태그 일괄 정정")
    parser.add_argument("--apply", action="store_true", help="실제 적용 (기본은 미리보기)")
    parser.add_argument("--limit", type=int, help="수정할 최대 영상 수 (쿼터 조절용)")
    parser.add_argument("--lang-only", action="store_true", help="언어만 정정하고 태그는 건드리지 않음")
    args = parser.parse_args()

    youtube = get_youtube_client()
    generate_tags = load_tag_generator()
    local_tags = load_local_tags()

    print("📺 채널 영상 조회 중...")
    videos = fetch_all_videos(youtube)
    print(f"   총 {len(videos)}개\n")

    targets = []
    for video in videos:
        plan = plan_fix(video, local_tags, generate_tags, args.lang_only)
        if plan:
            targets.append((video, *plan))

    if args.limit:
        targets = targets[: args.limit]

    if not targets:
        print("✅ 수정할 영상이 없습니다.")
        return

    quota = len(targets) * QUOTA_PER_UPDATE
    print(f"🔧 수정 대상: {len(targets)}개 (예상 쿼터 {quota:,} / 일일 {DAILY_QUOTA:,})")
    if quota > DAILY_QUOTA:
        print(f"   ⚠️ 일일 쿼터를 초과합니다. --limit {DAILY_QUOTA // QUOTA_PER_UPDATE} 이하로 나눠 실행하세요.")
    print()

    for video, _, reasons in targets[:15]:
        print(f"   {video['id']}  {video['snippet']['title'][:45]}")
        for reason in reasons:
            print(f"      · {reason}")
    if len(targets) > 15:
        print(f"   ... 외 {len(targets) - 15}개")
    print()

    if not args.apply:
        print("ℹ️ 미리보기 모드입니다. 실제 적용하려면 --apply 를 붙이세요.")
        return

    succeeded = failed = 0
    for index, (video, new_snippet, _) in enumerate(targets, start=1):
        try:
            youtube.videos().update(
                part="snippet", body={"id": video["id"], "snippet": new_snippet}
            ).execute()
            succeeded += 1
            print(f"   [{index}/{len(targets)}] ✅ {video['snippet']['title'][:45]}")
        except HttpError as exc:
            failed += 1
            print(f"   [{index}/{len(targets)}] ❌ {video['id']}: {exc}")
            if exc.resp.status == 403 and "quota" in str(exc).lower():
                print("   ⛔ 쿼터 소진으로 중단합니다. 내일 이어서 실행하세요.")
                break

    print(f"\n✅ 완료: {succeeded}개 수정, {failed}개 실패")


if __name__ == "__main__":
    main()

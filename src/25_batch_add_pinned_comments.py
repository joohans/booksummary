#!/usr/bin/env python3
"""
기존 YouTube 영상에 제휴 링크가 포함된 고정 댓글 일괄 추가 스크립트

채널의 모든 영상에 챕터 타임스탬프와 제휴 링크가 포함된 고정 댓글을 추가합니다.
안전장치로 --dry-run이 기본이며, --apply 플래그를 명시해야 실제로 추가됩니다.
"""

import os
import sys
import time
import argparse
import re
import json
import requests
from pathlib import Path
from typing import Any, Optional, Dict, List
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

GOOGLE_API_AVAILABLE = True

from src.utils.pinned_comment import generate_pinned_comment
from src.utils.link_validator import audit_and_clean_comment

load_dotenv()

# YouTube API 스코프 (댓글 작성 및 고정 권한 필요)
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

# 제휴 링크 마커 (고정 댓글에 이미 있는지 확인용)
AFFILIATE_MARKERS = [
    "📖 이 책 구매하기:",
    "📖 Get this book:"
]


class PinnedCommentAdder:
    """YouTube 영상에 제휴 링크가 포함된 고정 댓글을 일괄 추가하는 클래스"""

    # 상태 파일 경로
    STATE_FILE = "data/processed_videos.json"

    def __init__(self, dry_run: bool = True, delay: float = 1.0,
                 update_existing: bool = False, verify_books: bool = False,
                 validate_links: bool = False, fix_invalid_links: bool = False,
                 recreate: bool = False, resume: bool = False):
        """
        Args:
            dry_run: True면 미리보기만, False면 실제 추가
            delay: API 호출 간 대기 시간 (초)
            update_existing: True면 기존 제휴 댓글도 업데이트
            verify_books: True면 Google Books API로 책 제목 검증
            validate_links: True면 새 댓글 추가 전 링크 유효성 검사 (무효 링크 제외)
            fix_invalid_links: True면 기존 댓글에서 유효하지 않은 링크 찾아 제거/업데이트
            recreate: True면 기존 채널 소유자 댓글을 삭제 후 새 댓글로 재등록
            resume: True면 이미 처리한 영상 건너뜀 (상태 파일 사용)
        """
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("google-api-python-client가 필요합니다.")

        self.dry_run = dry_run
        self.delay = delay
        self.update_existing = update_existing
        self.verify_books = verify_books
        self.validate_links = validate_links
        self.fix_invalid_links = fix_invalid_links
        self.recreate = recreate
        self.resume = resume
        self.google_books_api_key = os.getenv("GOOGLE_BOOKS_API_KEY", "")
        self.youtube: Any = None
        self.channel_id = os.getenv("YOUTUBE_CHANNEL_ID")
        self.processed_video_ids = set()
        self.quota_exhausted = False

        if not self.channel_id:
            raise ValueError("YOUTUBE_CHANNEL_ID가 설정되지 않았습니다.")

        # 상태 파일 항상 로드 (이미 처리된 영상 추적)
        self._load_state()

        self._authenticate()

    def _load_state(self):
        """이미 처리한 영상 ID 목록을 상태 파일에서 로드"""
        state_file = Path(self.STATE_FILE)
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_video_ids = set(data.get('processed_video_ids', []))
                    print(f"📋 상태 파일 로드: {len(self.processed_video_ids)}개 이미 처리된 영상")
            except Exception as e:
                print(f"⚠️ 상태 파일 로드 실패: {e}")
        else:
            print("📋 상태 파일 없음. 새로 시작합니다.")
            self.processed_video_ids = set()

    def _save_state(self):
        """현재 처리한 영상 ID 목록을 상태 파일에 저장"""
        state_file = Path(self.STATE_FILE)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'processed_video_ids': list(self.processed_video_ids),
                    'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 상태 파일 저장 실패: {e}")

    def _authenticate(self):
        """OAuth2 인증"""
        client_id = os.getenv("YOUTUBE_CLIENT_ID")
        client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

        if not all([client_id, client_secret, refresh_token]):
            raise ValueError("YouTube API 자격증명이 설정되지 않았습니다.")

        try:
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES
            )

            credentials.refresh(Request())
            self.youtube = build('youtube', 'v3', credentials=credentials)
            print("✅ YouTube API 인증 성공")
        except Exception as e:
            print(f"❌ 인증 실패: {e}")
            raise

    def get_channel_videos(self, max_results: Optional[int] = None) -> List[Dict]:
        """
        채널의 모든 영상 목록 가져오기

        Args:
            max_results: 최대 영상 개수 (None이면 전체)

        Returns:
            영상 정보 목록 [{"video_id": "...", "title": "..."}, ...]
        """
        print(f"\n📋 채널 영상 목록 가져오는 중... (채널 ID: {self.channel_id})")

        videos = []

        try:
            # 1. 채널의 uploads 재생목록 ID 가져오기
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=self.channel_id
            ).execute()

            if not channel_response.get('items'):
                print("❌ 채널을 찾을 수 없습니다.")
                return videos

            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            print(f"   📂 Uploads 재생목록 ID: {uploads_playlist_id}")

            # 2. 재생목록의 모든 영상 가져오기
            next_page_token = None
            page = 1

            while True:
                playlist_response = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=50,  # 페이지당 최대 50개
                    pageToken=next_page_token
                ).execute()

                items = playlist_response.get('items', [])
                print(f"   📄 Page {page}: {len(items)}개 영상")

                for item in items:
                    video_id = item['snippet']['resourceId']['videoId']
                    title = item['snippet']['title']
                    videos.append({
                        'video_id': video_id,
                        'title': title
                    })

                    if max_results and len(videos) >= max_results:
                        break

                if max_results and len(videos) >= max_results:
                    break

                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break

                page += 1
                time.sleep(self.delay)  # API 호출 간 대기

            print(f"✅ 총 {len(videos)}개 영상 발견")
            return videos

        except HttpError as e:
            print(f"❌ API 오류: {e}")
            return videos

    def get_pinned_comment(self, video_id: str) -> Optional[Dict]:
        """
        영상의 고정 댓글 가져오기

        Args:
            video_id: YouTube 영상 ID

        Returns:
            고정 댓글 정보 (없으면 None)
        """
        try:
            response = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,
                order='relevance'
            ).execute()

            for item in response.get('items', []):
                snippet = item['snippet']
                top_comment = snippet['topLevelComment']['snippet']

                # 채널 소유자의 댓글인지 확인
                if top_comment.get('authorChannelId', {}).get('value') == self.channel_id:
                    # textOriginal: 원본 텍스트 (HTML 엔티티 없음, 채널 소유자만 접근 가능)
                    # textDisplay: YouTube가 HTML로 변환한 형태 (&amp; 등 포함) - 폴백용
                    text = top_comment.get('textOriginal') or top_comment.get('textDisplay', '')
                    return {
                        'comment_id': item['id'],
                        'text': text
                    }

            return None

        except HttpError as e:
            if e.resp.status == 403:
                # 댓글이 비활성화된 영상
                return None
            print(f"   ⚠️ 댓글 조회 오류: {e}")
            return None

    def has_affiliate_links(self, comment_text: str) -> bool:
        """
        댓글에 이미 제휴 링크가 있는지 확인

        Args:
            comment_text: 댓글 텍스트

        Returns:
            제휴 링크가 있으면 True
        """
        for marker in AFFILIATE_MARKERS:
            if marker in comment_text:
                return True
        return False

    def fix_comment_invalid_links(self, video_id: str, video_title: str) -> str:
        """
        기존 댓글에서 유효하지 않은 구매 링크를 찾아 제거하고 댓글을 업데이트합니다.

        Returns:
            'fixed' | 'no_comment' | 'no_affiliate' | 'all_valid' | 'error'
        """
        existing = self.get_pinned_comment(video_id)
        if not existing:
            print("   ℹ️  채널 소유자 댓글 없음. (건너뜀)")
            return "no_comment"

        comment_text = existing["text"]
        if not self.has_affiliate_links(comment_text):
            print("   ℹ️  제휴 링크 없는 댓글. (건너뜀)")
            return "no_affiliate"

        print("   🔍 구매 링크 유효성 검사 중...")
        cleaned, validation, removed = audit_and_clean_comment(
            comment_text, delay=0.5, verbose=True
        )

        if not removed:
            print("   ✅ 모든 링크 유효. (수정 불필요)")
            return "all_valid"

        print(f"   🗑  무효 링크 {len(removed)}개 제거됨:")
        for url in removed:
            print(f"      - {url[:80]}")

        if self.dry_run:
            print("   🔍 [DRY RUN] 댓글 업데이트 미리보기 (실제 변경 안 함)")
            print("   📝 업데이트 후 댓글 미리보기:")
            print("   " + cleaned.replace("\n", "\n   "))
            return "fixed"

        success = self.update_comment(existing["comment_id"], cleaned)
        return "fixed" if success else "error"

    def extract_book_info_from_title(self, title: str) -> Optional[Dict]:
        """
        제목에서 책 정보 추출

        Args:
            title: YouTube 영상 제목

        Returns:
            {"book_title": "...", "author": "...", "language": "ko/en"}
            또는 None
        """
        # 패턴 1: [핵심 요약] 책제목: 저자 (영문제목 · ...) — summary+video 한글
        match = re.search(r'\[핵심 요약\]\s*([^(\[|·]+?)(?:\s*[\(·\[])', title)
        if match:
            extracted = match.group(1).strip()
            # "책제목: 저자명" 형식에서 `:` 이후 저자명 제거
            book_title = extracted.split(':')[0].strip()
            language = "ko"
            return {"book_title": book_title, "author": "", "language": language}

        # 패턴 2: [Summary] Book Title: Author (... · ...) — summary+video 영문
        match = re.search(r'\[Summary\]\s*([^(\[|·]+?)(?:\s*[\(·\[])', title)
        if match:
            extracted = match.group(1).strip()
            # "Book Title: Author Name" 형식에서 `:` 이후 저자명 제거
            book_title = extracted.split(':')[0].strip()
            language = "en"
            return {"book_title": book_title, "author": "", "language": language}

        # 패턴 3: [한국어] 책제목 책 리뷰 저자 — 일당백 한글
        match = re.search(r'\[한국어\]\s*([^|]+?)책\s*리뷰\s*([^|]*?)(?:\s*\|)', title)
        if not match:
            match = re.search(r'\[한국어\]\s*([^|]+?)책\s*리뷰\s*(.*)', title)
        if match:
            book_title = match.group(1).strip()
            author = match.group(2).strip() if (match.lastindex or 0) >= 2 else ""
            language = "ko"
            return {"book_title": book_title, "author": author, "language": language}

        # 패턴 4: [English] Book Title Book Review Author — 일당백 영문
        match = re.search(r'\[English\]\s*([^|]+?)Book\s*Review\s*([^|]*?)(?:\s*\|)', title)
        if not match:
            match = re.search(r'\[English\]\s*([^|]+?)Book\s*Review\s*(.*)', title)
        if match:
            book_title = match.group(1).strip()
            author = match.group(2).strip() if (match.lastindex or 0) >= 2 else ""
            language = "en"
            return {"book_title": book_title, "author": author, "language": language}

        # 패턴 5: [1DANG100] Book Title: Author (...) — 일당백 영문
        match = re.search(r'\[1DANG100\]\s*([^:]+):\s*([^(\[|]+)', title)
        if match:
            book_title = match.group(1).strip()
            author = match.group(2).strip()
            language = "en"
            return {"book_title": book_title, "author": author, "language": language}

        # 패턴 6: [일당백] 책제목: 저자 (...) — 일당백 한글
        match = re.search(r'\[일당백\]\s*([^:]+):\s*([^(\[|]+)', title)
        if match:
            book_title = match.group(1).strip()
            author = match.group(2).strip()
            language = "ko"
            return {"book_title": book_title, "author": author, "language": language}

        # 패턴 7: [일당백] 책제목 (영문제목 · ...) — 저자 없이 콜론이 안 붙는 형식
        # 「왜 칸트인가」·「사랑의 학교」처럼 부제만 있는 편이 여기 걸린다 (2026-08-25 추가)
        match = re.search(r'\[일당백\]\s*([^(\[|:·]+?)\s*[\(·]', title)
        if match:
            return {"book_title": match.group(1).strip(), "author": "", "language": "ko"}

        # 패턴 8: [1DANG100] Book Title (... · ...) — 위의 영문판
        match = re.search(r'\[1DANG100\]\s*([^(\[|:·]+?)\s*[\(·]', title)
        if match:
            return {"book_title": match.group(1).strip(), "author": "", "language": "en"}

        # 패턴 9: 범용 폴백 — 위 패턴에 안 걸리는 구 제목 포맷을 모두 받는다 (2026-08-25 추가)
        # 「[Summary] Ikigai Book Review」·「[핵심요약] 원칙: 레이 달리오」(공백 없는 태그)
        # 「[한국어] 프로테스탄티즘의 윤리와 자본주의 정신 | [Korean] ...」 같은 것들이 여기 걸린다.
        # 순서: 앞머리 대괄호 태그 제거 → 첫 `|` 또는 `(` 앞까지 → 상투어 앞까지 → `:` 앞(저자 분리)
        # 대괄호 태그는 있으면 떼고, 없어도 진행한다. 태그 없는 구 영문 제목이 있다
        # ("Complete Guide to Don Quixote | From Author & Background to Full Story",
        #  "The Prince: A Necessary Evil for Awakened Citizens") — 2026-08-26 실측 15편
        head = re.sub(r'^\s*\[[^\]]+\]\s*', '', title)
        head = re.split(r'[|(]', head)[0]
        head = re.sub(r'^\s*Complete\s+Guide\s+to\s+', '', head, flags=re.I)
        head = re.split(
            r'책\s*리뷰|Book\s*Review|핵심\s*정리|핵심\s*요약|Complete\s+Guide',
            head, flags=re.I,
        )[0]
        head = head.split(':')[0].replace('_', ' ')
        head = re.sub(r'\s+', ' ', head).strip(' ·-—')
        if len(head) >= 2:
            lang = "ko" if re.search(r'[가-힣]', head) else "en"
            return {"book_title": head, "author": "", "language": lang}

        return None

    def verify_book_title(self, title: str, language: str = "en") -> bool:
        """
        Google Books API로 책 제목이 존재하는지 검증

        Args:
            title: 책 제목
            language: 검색 언어 ('ko' 또는 'en')

        Returns:
            책이 존재하면 True, 없으면 False
        """
        if not self.google_books_api_key:
            return True  # API 키 없으면 검증 건너뜀

        try:
            params = {
                "q": f"intitle:{title}",
                "key": self.google_books_api_key,
                "maxResults": 1,
            }
            if language == "ko":
                params["langRestrict"] = "ko"

            response = requests.get(
                "https://www.googleapis.com/books/v1/volumes",
                params=params,
                timeout=5
            )
            data = response.json()
            total = data.get("totalItems", 0)

            if total > 0:
                found_title = data["items"][0]["volumeInfo"].get("title", "")
                print(f"   📖 Google Books 검증: '{found_title}' 발견 (총 {total}건)")
                return True
            else:
                print(f"   ⚠️ Google Books에서 '{title}' 검색 결과 없음")
                return False

        except Exception as e:
            print(f"   ⚠️ Google Books 검증 실패 (무시): {e}")
            return True  # 검증 실패는 무시하고 진행

    def delete_comment(self, comment_thread_id: str) -> bool:
        """
        채널 소유자 댓글 삭제

        Args:
            comment_thread_id: 댓글 스레드 ID

        Returns:
            성공 여부
        """
        if self.dry_run:
            print("   🔍 [DRY RUN] 댓글 삭제 미리보기.")
            return True

        try:
            # 스레드 ID에서 topLevelComment ID 추출
            thread_response = self.youtube.commentThreads().list(
                part='snippet',
                id=comment_thread_id
            ).execute()

            if not thread_response.get('items'):
                print(f"   ❌ 댓글 스레드를 찾을 수 없습니다.")
                return False

            top_comment_id = thread_response['items'][0]['snippet']['topLevelComment']['id']
            self.youtube.comments().delete(id=top_comment_id).execute()
            print(f"   🗑  댓글 삭제 완료")
            return True

        except HttpError as e:
            print(f"   ❌ 댓글 삭제 실패: {e}")
            return False

    def update_comment(self, comment_id: str, comment_text: str) -> bool:
        """
        기존 댓글 업데이트

        Args:
            comment_id: 업데이트할 댓글 스레드 ID
            comment_text: 새 댓글 텍스트

        Returns:
            성공 여부
        """
        if self.dry_run:
            print("   🔍 [DRY RUN] 댓글 업데이트 미리보기.")
            return True

        try:
            # commentThreads ID에서 topLevelComment ID 추출
            thread_response = self.youtube.commentThreads().list(
                part='snippet',
                id=comment_id
            ).execute()

            if not thread_response.get('items'):
                print(f"   ❌ 댓글 스레드 {comment_id}를 찾을 수 없습니다.")
                return False

            top_comment_id = thread_response['items'][0]['snippet']['topLevelComment']['id']

            self.youtube.comments().update(
                part='snippet',
                body={
                    'id': top_comment_id,
                    'snippet': {
                        'textOriginal': comment_text
                    }
                }
            ).execute()

            print(f"   ✅ 댓글 업데이트 완료")
            return True

        except HttpError as e:
            print(f"   ❌ 댓글 업데이트 실패: {e}")
            return False

    def add_pinned_comment(self, video_id: str, comment_text: str) -> bool:
        """
        영상에 고정 댓글 추가

        Args:
            video_id: YouTube 영상 ID
            comment_text: 댓글 텍스트

        Returns:
            성공 여부
        """
        if self.dry_run:
            print("   🔍 [DRY RUN] 실제로 댓글을 추가하지 않습니다.")
            return True

        try:
            # 댓글 추가
            comment_response = self.youtube.commentThreads().insert(
                part='snippet',
                body={
                    'snippet': {
                        'videoId': video_id,
                        'topLevelComment': {
                            'snippet': {
                                'textOriginal': comment_text
                            }
                        }
                    }
                }
            ).execute()

            comment_id = comment_response['id']

            # 댓글 고정 (setModerationStatus API 사용)
            # 참고: 채널 소유자의 댓글만 고정 가능
            # YouTube Studio에서 수동으로 고정해야 함 (API로는 불가능)

            print(f"   ✅ 댓글 추가 완료 (YouTube Studio에서 수동 고정 필요)")
            print(f"   📝 댓글 ID: {comment_id}")
            return True

        except HttpError as e:
            print(f"   ❌ 댓글 추가 실패: {e}")
            if "quotaExceeded" in str(e):
                self.quota_exhausted = True
            return False

    def process_videos(self, video_ids: Optional[List[str]] = None, limit: Optional[int] = None):
        """
        영상들을 처리하여 고정 댓글 추가

        Args:
            video_ids: 처리할 영상 ID 목록 (None이면 전체 채널)
            limit: 최대 처리 개수
        """
        if video_ids:
            # 특정 영상만 처리 — 제목이 있어야 책 정보를 추출할 수 있으므로 API로 조회한다
            videos = []
            for i in range(0, len(video_ids), 50):
                chunk = video_ids[i:i + 50]
                try:
                    items = self.youtube.videos().list(
                        part="snippet", id=",".join(chunk)
                    ).execute().get("items", [])
                    found = {it["id"]: it["snippet"]["title"] for it in items}
                except Exception as e:
                    print(f"⚠️ 제목 조회 실패 ({e}) — ID만으로 진행합니다")
                    found = {}
                videos += [{"video_id": vid, "title": found.get(vid, "Unknown")} for vid in chunk]
        else:
            # 채널 전체 영상 가져오기
            videos = self.get_channel_videos(max_results=limit)

        if not videos:
            print("처리할 영상이 없습니다.")
            return

        # 비공개·예약 영상은 댓글 API 가 403 을 준다. 미리 걸러낸다.
        # (2026-08-25: 예약된 일당백 5편이 매번 403 을 맞고 있었다 — 공개 후 자동으로 대상이 된다)
        try:
            all_ids = [v["video_id"] for v in videos]
            private = {}
            for i in range(0, len(all_ids), 50):
                for it in self.youtube.videos().list(
                    part="status", id=",".join(all_ids[i:i + 50])
                ).execute().get("items", []):
                    if it["status"]["privacyStatus"] != "public":
                        private[it["id"]] = it["status"].get("publishAt", "")[:10] or "비공개"
            if private:
                print(f"⏸ 비공개·예약 {len(private)}개 제외 (공개 후 처리):")
                for vid, when in list(private.items())[:10]:
                    print(f"   - {vid} ({when})")
                videos = [v for v in videos if v["video_id"] not in private]
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ 공개 상태 확인 실패 ({e}) — 전체 대상으로 진행합니다")

        mode_label = "🔍 DRY RUN (미리보기)" if self.dry_run else "✏️ APPLY (실제 추가)"
        if self.recreate:
            mode_label += " + 🔄 기존 댓글 삭제 후 재등록"
        if self.fix_invalid_links:
            mode_label += " + 🔗 무효 링크 제거"
        if self.validate_links:
            mode_label += " + ✅ 링크 유효성 검사"

        print(f"\n{'='*60}")
        print(f"처리 모드: {mode_label}")
        print(f"처리 대상: {len(videos)}개 영상")
        print(f"{'='*60}\n")

        added_count = 0
        skipped_count = 0
        error_count = 0
        fixed_count = 0

        for idx, video in enumerate(videos, 1):
            video_id = video['video_id']
            video_title = video['title']

            # 상태 파일은 기본적으로 기록용이다. 건너뛸지는 실제 댓글 유무로 판단한다.
            # 낡은 "처리됨" 항목 때문에 댓글 없는 영상이 조용히 빠지는 일이 반복됐다
            # (비공개 403 실패분·드라이런 오염분). get_pinned_comment 가 1 unit 이라
            # 상태 파일로 아끼는 쿼터보다 놓치는 비용이 크다. 옛 동작은 --resume 으로.
            if self.resume and not self.recreate and video_id in self.processed_video_ids:
                print(f"   ⏭️ 이미 처리된 영상 (건너뜀)")
                skipped_count += 1
                continue

            print(f"\n[{idx}/{len(videos)}] 🎬 {video_title}")
            print(f"   📹 Video ID: {video_id}")

            try:
                # ── fix_invalid_links 모드: 기존 댓글 링크 유효성 검사 및 제거 ──
                if self.fix_invalid_links:
                    result = self.fix_comment_invalid_links(video_id, video_title)
                    if result == "fixed":
                        fixed_count += 1
                    elif result == "error":
                        error_count += 1
                    else:
                        skipped_count += 1
                    time.sleep(self.delay)
                    continue

                # ── 일반 모드: 신규 댓글 추가 ──

                # 1. 기존 채널 소유자 댓글 확인
                existing_comment = self.get_pinned_comment(video_id)
                should_update = False

                if existing_comment:
                    if self.recreate:
                        # recreate 모드: 기존 댓글 삭제 후 새로 등록
                        print("   🗑  기존 댓글 삭제 후 재등록 모드")
                        if not self.delete_comment(existing_comment['comment_id']):
                            error_count += 1
                            time.sleep(self.delay)
                            continue
                        # 삭제 후 existing_comment를 None으로 처리하여 신규 추가로 진행
                        existing_comment = None
                    elif self.has_affiliate_links(existing_comment['text']):
                        if self.update_existing:
                            print("   🔄 제휴 링크 있는 댓글 발견 - 업데이트 모드로 진행")
                            should_update = True
                        else:
                            print("   ✅ 이미 제휴 링크가 있는 댓글이 있습니다. (건너뜀)")
                            skipped_count += 1
                            continue
                    else:
                        print("   ⚠️ 기존 댓글이 있지만 제휴 링크가 없습니다.")

                # 2. 책 정보 추출
                book_info = self.extract_book_info_from_title(video_title)
                if not book_info:
                    print("   ⚠️ 제목에서 책 정보를 추출할 수 없습니다. (건너뜀)")
                    skipped_count += 1
                    continue

                print(f"   📚 책 정보: {book_info}")

                # 3. Google Books 검증 (선택사항)
                if self.verify_books:
                    verify_title = book_info['book_title']
                    verify_lang = book_info['language']
                    self.verify_book_title(verify_title, verify_lang)
                    # 검증 실패해도 계속 진행 (경고만 출력)

                # 4. 고정 댓글 생성 (validate_links=True면 유효한 링크만 포함)
                comment_text = generate_pinned_comment(
                    book_title=book_info['book_title'],
                    timestamps=None,  # 타임스탬프는 영상마다 다르므로 생략
                    language=book_info['language'],
                    author=None,  # 작가명 제외 - 검색 정확도 향상
                    validate_links=self.validate_links,
                )

                if not comment_text:
                    print("   ⚠️ 고정 댓글 생성 실패. (건너뜀)")
                    skipped_count += 1
                    continue

                print(f"   📝 댓글 길이: {len(comment_text)}자")

                # 5. 댓글 추가 또는 업데이트
                if should_update and existing_comment:
                    if self.update_comment(existing_comment['comment_id'], comment_text):
                        added_count += 1
                        self.processed_video_ids.add(video_id)
                    else:
                        error_count += 1
                elif self.add_pinned_comment(video_id, comment_text):
                    added_count += 1
                    self.processed_video_ids.add(video_id)
                else:
                    error_count += 1

                # 쿼터가 떨어졌으면 나머지를 두드리지 않고 멈춘다 (2026-08-25: 121회 헛시도)
                if self.quota_exhausted:
                    print("\n⛔ 쿼터 소진 — 중단합니다. 리셋(KST 16:00) 후 같은 명령으로 이어집니다.")
                    break

                # API 호출 간 대기
                time.sleep(self.delay)

            except HttpError as e:
                print(f"   ❌ API 오류: {e}")
                error_count += 1
                if "quotaExceeded" in str(e):
                    print("\n⛔ 쿼터 소진 — 남은 영상을 건너뛰고 중단합니다.")
                    print("   쿼터 리셋은 KST 16:00. 이후 같은 명령을 다시 실행하면 이어집니다.")
                    break
                time.sleep(self.delay)
            except Exception as e:
                print(f"   ❌ 예외 발생: {e}")
                error_count += 1
                time.sleep(self.delay)

        # 최종 결과
        print(f"\n{'='*60}")
        print(f"✅ 처리 완료:")
        if self.fix_invalid_links:
            print(f"   - 링크 수정: {fixed_count}개")
        else:
            print(f"   - 추가: {added_count}개")
        print(f"   - 건너뜀: {skipped_count}개")
        print(f"   - 오류: {error_count}개")
        print(f"{'='*60}")

        # 상태 파일 저장 (새로 처리된 영상 추가)
        # DRY RUN 에서는 저장하지 않는다. 미리보기가 "처리됨"으로 기록되면 뒤이은 --apply 가
        # 전부 건너뛴다 — 2026-08-25 실측으로 71편이 게시 없이 스킵됐다.
        if self.dry_run:
            print(f"\n📋 DRY RUN — 상태 파일 저장 안 함 (대상 {len(self.processed_video_ids)}개 미리보기)")
        else:
            self._save_state()
            print(f"\n📋 상태 저장 완료: 총 {len(self.processed_video_ids)}개 처리된 영상")

        if not self.dry_run and added_count > 0:
            print(f"\n⚠️ 중요: YouTube Studio에서 댓글을 수동으로 고정해야 합니다!")
            print(f"   https://studio.youtube.com/")


def main():
    parser = argparse.ArgumentParser(
        description="기존 YouTube 영상에 제휴 링크가 포함된 고정 댓글 일괄 추가",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 미리보기 (기본)
  python src/25_batch_add_pinned_comments.py --dry-run

  # 실제 적용 (50개 제한)
  python src/25_batch_add_pinned_comments.py --apply --limit 50

  # 특정 영상만 처리
  python src/25_batch_add_pinned_comments.py --video-id VIDEO_ID --apply

  # API 호출 간격 조절 (초)
  python src/25_batch_add_pinned_comments.py --apply --delay 2.0

  # 기존 댓글도 새 형식으로 업데이트 (작가명 제거된 링크로)
  python src/25_batch_add_pinned_comments.py --apply --update-existing --delay 2.0

  # Google Books API로 책 제목 검증하며 처리
  python src/25_batch_add_pinned_comments.py --apply --verify-books --delay 2.0

  # 새 댓글 추가 시 링크 유효성 검사 (무효 링크 제외)
  python src/25_batch_add_pinned_comments.py --apply --validate-links

  # 기존 댓글의 무효 링크 탐지 및 제거 (미리보기)
  python src/25_batch_add_pinned_comments.py --fix-invalid-links

  # 기존 댓글의 무효 링크 실제 제거 적용
  python src/25_batch_add_pinned_comments.py --fix-invalid-links --apply

주의사항:
  - YouTube API 일일 쿼터: commentThreads.insert 1건 = 50 units (일 10,000 units 제한 → 약 200건/일)
  - --apply 플래그 없이는 미리보기만 수행됩니다.
  - 이미 제휴 링크가 있는 댓글은 건너뜁니다 (--update-existing 없으면).
  - --update-existing: 기존 제휴 댓글을 새 형식으로 교체합니다.
  - 댓글 추가 후 YouTube Studio에서 수동으로 고정해야 합니다!
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='미리보기만 수행 (실제 추가 안 함, 기본값)'
    )

    parser.add_argument(
        '--apply',
        action='store_true',
        help='실제로 댓글 추가 (이 플래그가 있어야 추가됨)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='처리할 최대 영상 개수'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='API 호출 간 대기 시간 (초, 기본값: 1.0)'
    )

    parser.add_argument(
        '--video-id',
        action='append',
        help='처리할 특정 영상 ID (여러 개 지정 가능)'
    )

    parser.add_argument(
        '--update-existing',
        action='store_true',
        help='이미 제휴 링크가 있는 댓글도 새 형식으로 업데이트'
    )

    parser.add_argument(
        '--verify-books',
        action='store_true',
        help='Google Books API로 책 제목 존재 여부 검증 (GOOGLE_BOOKS_API_KEY 필요)'
    )

    parser.add_argument(
        '--validate-links',
        action='store_true',
        help='새 댓글 추가 시 구매 링크 유효성 HTTP 검사 후 무효 링크 제외'
    )

    parser.add_argument(
        '--fix-invalid-links',
        action='store_true',
        help='기존 댓글에서 유효하지 않은 구매 링크를 찾아 제거 (--apply 없으면 DRY RUN)'
    )

    parser.add_argument(
        '--recreate',
        action='store_true',
        help='기존 채널 소유자 댓글을 삭제하고 새 댓글로 재등록 (--apply 없으면 DRY RUN)'
    )

    parser.add_argument(
        '--resume',
        action='store_true',
        help='이미 처리한 영상 건너뜀 (상태 파일 사용)'
    )

    args = parser.parse_args()

    # --apply 플래그가 있으면 dry_run=False
    dry_run = not args.apply

    if not dry_run:
        if args.fix_invalid_links:
            mode_str = "무효 링크 제거"
        elif args.update_existing:
            mode_str = "업데이트"
        else:
            mode_str = "추가"
        print(f"⚠️ 실제 {mode_str} 모드입니다. 5초 후 시작합니다...")
        time.sleep(5)

    try:
        adder = PinnedCommentAdder(
            dry_run=dry_run,
            delay=args.delay,
            update_existing=args.update_existing,
            verify_books=args.verify_books,
            validate_links=args.validate_links,
            fix_invalid_links=args.fix_invalid_links,
            recreate=args.recreate,
            resume=args.resume,
        )
        adder.process_videos(video_ids=args.video_id, limit=args.limit)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

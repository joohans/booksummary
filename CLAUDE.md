# BookSummary 프로젝트 가이드

이 프로젝트는 책 요약 및 리뷰 영상을 자동으로 생성하는 파이프라인입니다. YouTube에 업로드할 일당백 스타일 영상과 핵심요약 영상을 제작합니다.

## 🔍 세션 시작 시 필수 확인 (최최우선)

**모든 작업 요청에 앞서, 반드시 `history.md` 상단의 체크리스트를 먼저 읽어야 합니다.**

```bash
# 세션 시작 시 항상 실행
# Read history.md 상단 "⚡ 다음 작업 세션 체크리스트" 섹션 확인
```

### 확인 목적
1. **코드 개선 요청 시** — 이미 완료된 개선인지 중복 작업 방지
2. **채널 현황 파악** — 구독자 수, 총 영상 수, 분석 리포트 위치
3. **우선순위 확인** — 다음 액션 아이템 순서 파악

### 규칙
- `history.md` 체크리스트 확인 전까지 코드 수정 절대 금지
- 이미 완료된 항목을 재작업 요청받으면 "이미 완료됨"을 먼저 알리고 현재 상태 설명
- 체크리스트의 "다음 우선 실행 액션"을 기준으로 작업 순서 제안

## 🎬 사용자 워크플로우 (최우선)

### 일반적인 작업 흐름
사용자는 다음과 같은 패턴으로 작업을 요청합니다:

1. **사전 준비**: `input/` 폴더에 필요한 파일들을 준비합니다
2. **영상 제작 요청**: "summary+video 스타일로 영상 만들어줘" 또는 "일당백 스타일로 영상 만들어줘"
3. **언어**: 한글과 영문 영상 모두 생성을 기대합니다
4. **필요한 정보**: 추가로 필요한 정보가 있으면 질문합니다

### 사용자가 영상 제작을 요청할 때 물어봐야 할 것들

**사용자가 "summary+video 영상 만들어줘" 또는 "일당백 영상 만들어줘" 요청 시:**

1. **영상 스타일 확인** (명확하지 않은 경우)
   - "summary+video 스타일" 또는 "일당백 스타일" 중 어떤 스타일인지 확인
   - summary+video: 5분 요약 + NotebookLM 리뷰 영상 (단일 영상)
   - 일당백: Part 1 + Part 2 등 여러 파트 연결 (에피소드 영상)

2. **책 정보 확인**
   - 책 제목 (필수)
   - 저자 이름 (선택사항, 있으면 좋음)

3. **TTS 옵션 선택** (summary+video 스타일인 경우만)
   - TTS 제공자: OpenAI / Google Cloud / Replicate
   - 음성 선택: 제공자별 음성 목록 제시

4. **언어 확인**
   - 한글 영상 생성 여부 (기본: Yes)
   - 영문 영상 생성 여부 (기본: Yes)
   - 보통 둘 다 생성하지만 명시적으로 확인

5. **추가 옵션 확인** (필요 시)
   - 요약 길이 (기본: 5분)
   - Summary 음량 조절 (기본: 1.2배)
   - 자막 추가 여부 (기본: 자막 없음)

### Input 폴더 확인 (작업 시작 시 필수)

**중요: 모든 영상 제작 작업은 반드시 `input/` 폴더 확인부터 시작해야 합니다!**

1. **Input 폴더 확인**
   ```bash
   ls -la input/
   ```
   - 사용자가 준비한 파일들이 있는지 확인
   - 파일명 패턴: `{prefix}_타입_{언어}.{확장자}`
   - 예: `man_audio_kr.m4a`, `man_summary_kr.md`, `man_thumbnail_kr.png`, `man_video_kr.mp4`

2. **필수 파일 체크리스트**
   - `{prefix}_audio_kr.m4a` / `{prefix}_audio_en.m4a` - NotebookLM 리뷰 오디오 (필수)
   - `{prefix}_summary_kr.md` / `{prefix}_summary_en.md` - 요약 텍스트 (선택, 없으면 AI 생성)
   - `{prefix}_thumbnail_kr.png` / `{prefix}_thumbnail_en.png` - 썸네일 원본 (선택)
   - `{prefix}_video_kr.mp4` / `{prefix}_video_en.mp4` - NotebookLM 비디오 (선택)

3. **표준 워크플로우 실행 순서**
   ```bash
   # 1단계: Input 폴더에서 파일 준비 및 표준 네이밍으로 이동
   python scripts/prepare_files_from_downloads.py \
     --book-title "책 제목" \
     --author "저자 이름" \
     --prefix "파일명접두사"

   # 2단계: 이미지 다운로드 (필수 100개, 저자/주제 관련)
   # - 기본: AI 검증 포함 (130개 다운로드 → 관련성 점수 상위 100개 유지)
   # - --skip-validation: AI 검증 없이 빠르게 다운로드만 수행
   python src/02_get_images.py \
     --title "책 제목" \
     --author "저자 이름" \
     --num-mood 100 \
     --skip-cover
   # AI 검증 없이 빠르게: --skip-validation 추가

   # 3단계: 다중 엔진 TTS 오디오 생성 (선택사항, 요약 MD가 있는 경우)
   python src/09_text_to_speech_multi.py \
     --provider openai \
     --text-file "assets/summaries/{책제목}_summary_ko.md" \
     --output "assets/audio/{책제목}_longform_ko.mp3" \
     --voice nova \
     --language ko

   # 4단계: 영상 제작 (한글)
   # - 구조: Summary(5분, 750단어+, Hook/Body/Bridge) + NotebookLM + Review
   python src/10_create_video_with_summary.py \
     --book-title "책 제목" \
     --author "저자 이름" \
     --language ko \
     --summary-duration 5.0 \
     --summary-audio-volume 1.2

   # 5단계: 영상 제작 (영문)
   python src/10_create_video_with_summary.py \
     --book-title "책 제목" \
     --author "저자 이름" \
     --language en \
     --summary-duration 5.0 \
     --summary-audio-volume 1.2

   # 6단계: 메타데이터 생성
   python src/08_create_and_preview_videos.py \
     --book-title "책 제목" \
     --metadata-only

   # 7단계: YouTube 업로드 (비공개)
   python src/09_upload_from_metadata.py \
     --privacy private \
     --auto
   ```

4. **번역 매핑 확인 및 추가**
   - 새로운 책의 경우 `src/utils/translations.py`에 매핑 추가 필요
   - 책 제목 매핑: `translate_book_title()` 함수의 `title_map`
   - 작가 이름 매핑: `translate_author_name()` 함수의 `author_map`
   - 예시:
     ```python
     "죽음의 수용소에서": "Man's Search for Meaning",
     "빅터 프랭클": "Viktor Frankl",
     ```

5. **파일 이동 후 위치 확인**
   - 오디오: `assets/audio/{책제목}_review_{언어}.{확장자}`
   - 요약: `assets/summaries/{책제목}_summary_{언어}.md`
   - 썸네일: `output/{책제목}_thumbnail_{언어}.jpg` (PNG→JPG 자동 변환)
   - 비디오: `assets/video/{책제목}_notebooklm_{언어}.{확장자}`
   - 이미지: `assets/images/{책제목}/mood_*.jpg` (100개)
   - 책 정보: `assets/images/{책제목}/book_info.json`
   - 책 커버: `assets/images/{책제목}/cover.jpg`

6. **보안 및 인증 정보 확인**
   - 모든 자격 증명 파일은 `secrets/` 폴더에 위치해야 합니다.
   - `secrets/client_secret.json`: YouTube API 클라이언트 보안 비밀
   - `secrets/credentials.json`: YouTube API 인증 토큰 (`youtube.upload` + `youtube.force-ssl` 스코프 포함)
   - `secrets/google-cloud-tts-key.json`: Google Cloud TTS 서비스 계정 키
   - OAuth 스코프 재발급이 필요한 경우: `python scripts/reauth_youtube.py` 실행

## 📦 제휴 링크 및 고정 댓글 관리

### 제휴 링크 자동 삽입
업로드 시 description에 Amazon/알라딘/Yes24 제휴 링크가 자동으로 포함됩니다.

1. **환경 변수 설정** (`.env` 파일)
   - `AMAZON_ASSOCIATE_TAG`: Amazon Associates 태그 (예: `joohans-20`)
   - `ALADIN_PARTNER_ID`: 알라딘 파트너스 ID (선택)
   - `YES24_PARTNER_ID`: Yes24 제휴 ID (선택)
   - 하나라도 설정되어 있으면 업로드 시 자동 삽입

2. **기존 영상 일괄 업데이트** (`src/24_batch_update_affiliate_links.py`)
   ```bash
   # 미리보기 (기본값, 실제 변경 없음)
   python src/24_batch_update_affiliate_links.py

   # 실제 업데이트 (처음 설정하거나 링크 변경 시)
   python src/24_batch_update_affiliate_links.py --apply

   # 이미 링크가 있는 영상도 강제 업데이트
   python src/24_batch_update_affiliate_links.py --apply --force
   ```

### 일괄 고정 댓글 추가/업데이트
채널의 모든 영상에 챕터 타임스탬프 + 제휴 링크가 포함된 고정 댓글을 관리합니다.

1. **실행 명령어** (`src/25_batch_add_pinned_comments.py`)
   ```bash
   # 미리보기 (기본값, 실제 변경 없음)
   python src/25_batch_add_pinned_comments.py

   # 실제 추가 (새 영상에만)
   python src/25_batch_add_pinned_comments.py --apply

   # 기존 댓글도 업데이트
   python src/25_batch_add_pinned_comments.py --apply --update-existing
   ```

2. **주의사항**
   - 실제 "고정" 처리는 YouTube UI에서 수동으로 해야 함 (API 미지원)
   - `youtube.force-ssl` 스코프가 필요 (댓글 작성 권한)
   - `--dry-run`이 기본값이므로 반드시 `--apply` 명시 필요

## 🎬 영상 제작 및 업로드 워크플로우

### YouTube URL 자막 다운로드
**중요: 사용자가 YouTube URL을 제공하고 "스크립트를 만들어달라" 또는 "스크립트 생성" 등을 요청하면 `fetch_separate_scripts.py`를 실행해야 합니다.**

1. **YouTube URL 자막 다운로드 규칙**
   - 사용자가 YouTube URL을 제공하고 스크립트/자막 다운로드를 요청할 때
   - `scripts/fetch_separate_scripts.py` 스크립트를 실행
   - Part 1, Part 2 등의 영상에서 자막을 가져와서 각각 별도의 텍스트 파일로 저장

2. **실행 명령어**
   ```bash
   .venv/bin/python scripts/fetch_separate_scripts.py \
     --urls "URL1" "URL2" ...

   # 여러 URL이 제공된 경우
   .venv/bin/python scripts/fetch_separate_scripts.py \
     --urls "https://www.youtube.com/watch?v=VIDEO_ID_1" "https://www.youtube.com/watch?v=VIDEO_ID_2" \
     --title "책 제목"
   ```

3. **출력 파일 위치**
   - `data/source/{비디오ID 또는 책제목}_part1_author.txt` (Part 1: 작가와 배경)
   - `data/source/{비디오ID 또는 책제목}_part2_novel.txt` (Part 2: 소설 줄거리)
   - 추가 Part가 있으면 `part3_*.txt`, `part4_*.txt` 등으로 저장

4. **주의사항**
   - 책 제목이 제공되지 않으면 비디오 ID를 사용하여 파일명 생성
   - IP 차단을 우회하기 위해 쿠키 파일(`scripts/cookies.txt`) 자동 사용
   - 자막이 없는 영상의 경우 오류 메시지 표시

### 일당백 스타일 영상 제작
**중요: 사용자가 "일당백 스타일" 또는 "일당백스타일"이라고 요청하면 `create_full_episode.py`를 실행해야 합니다.**

1. **일당백 스타일 영상 제작 규칙**
   - 사용자가 "일당백 스타일로 영상 만들어줘", "일당백스타일 영상" 등으로 요청할 때
   - `src/create_full_episode.py` 스크립트를 실행
   - Part 1, Part 2 등의 비디오와 인포그래픽을 연결하여 전체 에피소드 영상 생성

2. **실행 명령어**
   ```bash
   python src/create_full_episode.py \
     --title "책 제목" \
     --language ko
   ```

3. **필수 파일 위치**
   - `assets/notebooklm/{책제목}/{언어}/part1_video_{언어}.mp4`
   - `assets/notebooklm/{책제목}/{언어}/part1_info_{언어}.png`
   - `assets/notebooklm/{책제목}/{언어}/part2_video_{언어}.mp4`
   - `assets/notebooklm/{책제목}/{언어}/part2_info_{언어}.png`

4. **주의사항**
   - 일당백 스타일은 비디오 연결 방식이므로 Summary 생성이나 TTS는 필요 없음
   - 단순히 Part 1 영상 → Part 1 인포그래픽 → Part 2 영상 → Part 2 인포그래픽 순서로 연결

### 일당백 영상 제목 포맷 규칙 (고정)
**중요: 일당백 스타일 영상의 제목 포맷은 명시적 요청이 없으면 절대 변경하지 않습니다.**

1. **제목 포맷 규칙 (고정)**
   - **한글 영상**: `[일당백] {한글제목}: {한글작가명} ({부제목})`
   - **영문 영상**: `[1DANG100] {영문제목}: {영문작가명} ({부제목})`
   - 각 언어 영상은 해당 언어로만 제목 구성 (한글 영상에 영문 혼입 금지, 영문 영상에 한글 혼입 금지)
   - 부제목은 있으면만 추가, 100자 제한 초과 시 자동 축약
   - 제목은 `src/20_create_episode_metadata.py`의 `generate_episode_title()` 함수에서 생성

2. **제목 포맷 변경 금지**
   - 사용자가 명시적으로 "제목 포맷 변경", "제목 형식 바꿔줘" 등으로 요청하지 않는 한 절대 변경하지 않음
   - 제목이 너무 길어서 YouTube 100자 제한에 걸리는 경우에만 자동으로 축약
   - 제목 포맷 변경이 필요한 경우 반드시 사용자에게 확인 후 진행

3. **예시**
   - 한글: `[일당백] 노르웨이의 숲: 무라카미 하루키`
   - 영문: `[1DANG100] Norwegian Wood: Haruki Murakami`

### YouTube 업로드 승인 절차
**중요: 영상 생성 후 YouTube 업로드는 반드시 사용자의 명시적 허락을 받아야 합니다.**

1. **영상 생성 워크플로우**
   - 영상 생성 요청 시: 영상 제작까지만 진행
   - 메타데이터 생성까지 완료
   - **YouTube 업로드는 자동으로 진행하지 않음**

2. **YouTube 업로드 절차**
   - 영상 생성 완료 후 사용자에게 업로드 여부 확인
   - 사용자가 명시적으로 "업로드해줘", "업로드 진행해줘" 등으로 요청할 때만 업로드 실행
   - 업로드 전 업로드할 영상 목록과 설정(공개/비공개 등)을 사용자에게 확인

3. **업로드 명령어 예시**
   ```bash
   # 업로드는 사용자 명시적 요청 시에만 실행
   python src/09_upload_from_metadata.py --privacy private --auto
   ```

4. **주의사항**
   - "영상 만들어줘" 요청만으로는 업로드하지 않음
   - "영상 만들고 업로드해줘" 같은 명시적 요청이 있어야 업로드 진행
   - 업로드 전 항상 사용자에게 최종 확인 요청

### 썸네일 프롬프트 자동 생성 (영상 제작 완료 후 필수)
**중요: 영상 제작이 완료되면 반드시 Gems용 썸네일 프롬프트를 자동으로 출력합니다.**

1. **자동 출력 규칙**
   - 영상 제작(한글/영문) 완료 후, 사용자에게 묻지 않고 **자동으로** 썸네일 프롬프트를 출력합니다.
   - 템플릿 파일을 읽어 플레이스홀더를 채운 완성된 프롬프트를 출력합니다.
   - 템플릿 위치: `templates/thumbnails/`

2. **스타일별 템플릿**
   - Summary+Video 한글: `templates/thumbnails/summary_video_ko.md`
   - Summary+Video 영문: `templates/thumbnails/summary_video_en.md`
   - 일당백 한글: `templates/thumbnails/episode_ko.md`
   - 일당백 영문: `templates/thumbnails/episode_en.md`

3. **플레이스홀더 채우기 규칙**
   - `{author_name}`: 저자 이름 (한글 또는 영문, 영상 언어에 맞게)
   - `{hook_sentence}`: 책 핵심 메시지를 **궁금증 유발 문장**으로 직접 생성 (책 제목 그대로 X)
   - `{illustration_subject}`: 저자 또는 책 주인공 묘사 (수채화 일러스트 소재로 적합하게)
   - `{thematic_background}`: 책의 핵심 상징물이나 배경
   - `{character_description}`: (일당백용) 인물 묘사
   - `{world_background}`: (일당백용) 세계관 배경

4. **출력 형식 예시**
   영상 제작 완료 후 다음처럼 출력합니다:
   ```
   ---
   📸 Gems 썸네일 프롬프트 (한글용)
   [완성된 프롬프트 내용]

   📸 Gems 썸네일 프롬프트 (영문용)
   [완성된 프롬프트 내용]
   ---
   ```

5. **주의사항**
   - `{hook_sentence}`는 Claude가 책 내용을 바탕으로 직접 창작합니다 (단순 번역이나 제목 그대로 X)
   - 한글/영문 영상 모두 제작한 경우 두 프롬프트 모두 출력합니다

### 업로드 전 썸네일 생성 (필수)
**중요: YouTube 업로드 전에 반드시 썸네일을 생성·확인합니다.**

1. **자동 동작**
   - `src/09_upload_from_metadata.py` 실행 시, 썸네일이 없으면 **업로드 직전**에 `input/` 폴더에서 자동 생성합니다.
   - 한글(ko): `input/` 내 `*thumbnail*kr*`, `*thumbnail*ko*`, `*gold*kr*` 등 → `output/{영상파일명}_thumbnail_ko.jpg`
   - 영문(en): `input/` 내 `*thumbnail*en*`, `*gold*en*` 등 → `output/{영상파일명}_thumbnail_en.jpg`

2. **수동으로 썸네일만 먼저 만들고 싶을 때**
   - `input/`에 `gold_thumbnail_kr.png`, `gold_thumbnail_en.png` 또는 `thumbnail_kr.png`, `thumbnail_en.png` 등을 두고
   - 업로드 스크립트를 실행하면 됩니다. (스크립트가 업로드 전에 위 규칙으로 JPG를 생성합니다.)

3. **주의사항**
   - 사용자가 "업로드해줘"라고 할 때, **썸네일 생성이 선행되지 않았다면** 업로드 스크립트 하나만 실행해도 됩니다. 스크립트가 `input/` 기반 썸네일 자동 생성을 수행합니다.
   - 일당백·핵심요약 모두 동일: `output/`에 `{영상 stem}_thumbnail_ko.jpg` / `_en.jpg` 가 없으면 `input/` 에서 생성 후 업로드합니다.

## 🎤 TTS (Text-to-Speech) 설정

### 영상 제작 시 TTS 옵션 선택
**중요: 사용자가 Summary+Video 영상 제작을 요청할 때, 반드시 TTS 옵션을 물어봐야 합니다.**

1. **TTS 제공자 선택**
   - 사용자에게 어떤 TTS 제공자를 사용할지 물어봅니다
   - 선택지:
     - **OpenAI TTS** (기본값): 빠르고 자연스러운 음성, 한국어 지원 우수
     - **Google Cloud TTS Neural2** (권장): 한국어 발음 가장 우수, 한국어 특화
     - **Replicate xtts-v2**: 오픈소스 기반, 다양한 언어 지원

2. **음성 선택**
   - TTS 제공자에 따라 사용 가능한 음성이 다릅니다
   - 사용자에게 음성을 선택하도록 물어봅니다

3. **제공자별 사용 가능한 음성**

   **OpenAI TTS**:
   - 한국어 권장: `nova` (여성, 자연스러움), `alloy` (중성), `echo` (남성)
   - 영어 권장: `alloy` (중성), `nova` (여성), `echo` (남성), `fable` (영국식 남성)
   - 기타: `onyx` (남성), `shimmer` (여성)

   **Google Cloud TTS Neural2**:
   - 한국어: `ko-KR-Neural2-A` (여성, 기본), `ko-KR-Neural2-B` (남성), `ko-KR-Neural2-C` (여성), `ko-KR-Neural2-D` (남성)
   - 영어: `en-US-Neural2-A` ~ `en-US-Neural2-J` (다양한 음성, 기본: C)

   **Replicate xtts-v2**:
   - 언어 코드만 지정 (ko, en)

4. **실행 명령어 예시**

   ```bash
   # OpenAI TTS (nova 음성, 기본값)
   python src/10_create_video_with_summary.py \
     --book-title "책 제목" \
     --author "저자 이름" \
     --language ko \
     --tts-provider openai \
     --tts-voice nova

   # Google Cloud TTS (Neural2-B 남성 음성)
   python src/10_create_video_with_summary.py \
     --book-title "책 제목" \
     --author "저자 이름" \
     --language ko \
     --tts-provider google \
     --tts-voice ko-KR-Neural2-B

   # OpenAI TTS (echo 남성 음성)
   python src/10_create_video_with_summary.py \
     --book-title "책 제목" \
     --author "저자 이름" \
     --language en \
     --tts-provider openai \
     --tts-voice echo
   ```

5. **기본값 동작**
   - `--tts-provider` 미지정 시: `openai` (기본값)
   - `--tts-voice` 미지정 시: 제공자별 기본 음성 사용
     - OpenAI: 한국어 `nova`, 영어 `alloy`
     - Google: 한국어 `ko-KR-Neural2-A`, 영어 `en-US-Neural2-C`

6. **TTS 옵션 질문 프로세스**
   - 사용자가 "summary+video 영상 만들어줘" 요청 시:
     1. 먼저 TTS 제공자를 물어봅니다 (OpenAI / Google Cloud / Replicate)
     2. 선택한 제공자의 음성 목록을 보여주고 선택하도록 합니다
     3. 선택된 옵션으로 영상 제작 명령어를 실행합니다
   - **주의**: 일당백 스타일은 TTS 옵션이 필요 없습니다 (NotebookLM 오디오 사용)

## 📝 Summary 파일 작성 규칙

### Summary 파일 메타데이터 주석 처리
**중요: Summary 파일 생성 시 메타데이터는 반드시 HTML 주석으로 처리해야 합니다.**

1. **메타데이터 주석 처리 규칙**
   - 책 제목, 저자 이름, 설명 라인 등은 HTML 주석(`<!-- -->`)으로 감싸야 함
   - TTS 생성 시 자동으로 필터링되어 음성으로 변환되지 않음
   - 예시:
     ```markdown
     <!-- 📘 노인과 바다 -->
     <!-- 어니스트 헤밍웨이 -->
     <!-- TTS 기준 약 5분 서머리 스크립트 (Korean) -->

     [HOOK – 도입]

     사람은 언제 패배하는가?
     ...
     ```

2. **적용 범위**
   - `src/08_generate_summary.py`의 `save_summary()` 메서드에서 자동으로 주석 처리
   - 수동으로 작성하는 경우에도 동일한 규칙 적용

## Git 커밋 전 필수 작업

### 커밋 전 반드시 수행할 작업
**중요: Git 커밋 전에 반드시 다음 파일들을 업데이트하고 커밋/푸시해야 합니다:**

1. **README.md 파일 업데이트 및 커밋/푸시 (필수)**
   - **항상 현행화 유지**: 코드 변경 시 즉시 README.md도 함께 업데이트
   - 새로운 기능 추가 시 문서화
   - 사용법 변경 시 업데이트
   - 주요 개선사항 반영
   - 파일 구조 변경 시 "프로젝트 구조" 섹션 업데이트
   - 파일 네이밍 규칙 변경 시 "사용 방법" 섹션 업데이트
   - 환경 변수 추가 시 "환경 변수 설정" 섹션 업데이트
   - API 우선순위 변경 시 "주요 기능" 섹션 업데이트
   - 영상 구조 변경 시 "프로젝트 개요"와 "워크플로우" 섹션 업데이트
   - **변경사항이 있으면 반드시 커밋/푸시**

2. **TODO.md 파일 업데이트 및 커밋/푸시 (필수)**
   - **항상 현행화 유지**: 작업 완료 시 즉시 TODO.md도 함께 업데이트
   - 완료된 작업 체크 표시
   - 새로운 작업 항목 추가
   - 진행 중인 작업 상태 업데이트
   - **변경사항이 있으면 반드시 커밋/푸시**

3. **history.md 파일 업데이트**
   - **반드시 정확한 날짜로 새 섹션 추가** (예: `## 2026-02-09`)
   - 날짜는 `date +"%Y-%m-%d"` 명령어로 확인하여 정확하게 기록
   - 주요 변경사항 기록
   - 완료된 작업 요약
   - 생성된 파일 및 크기 정보

4. **ildangbaek_books.csv 업데이트** (유튜브 업로드 시)
   - 유튜브 채널에 업로드된 책 정보 업데이트
   - `python src/13_update_csv_from_youtube.py` 실행하여 최신 업로드 정보 반영
   - `status` 필드를 `uploaded`로 업데이트
   - `youtube_uploaded` 필드에 업로드 날짜 기록
   - 업로드된 책의 `video_created` 필드도 함께 업데이트 (없는 경우)

5. **GitHub CI 테스트 확인 (필수)**
   ```bash
   pytest
   ```
   - 모든 테스트가 통과하는지 반드시 확인
   - 새로운 기능 추가나 코드 수정 시 영향도가 있는 테스트가 있는지 점검
   - 테스트 실패 시 커밋 금지 및 수정 우선

**커밋 전 체크리스트:**
- [ ] README.md 업데이트 완료 및 커밋/푸시
- [ ] TODO.md 업데이트 완료 및 커밋/푸시
- [ ] history.md 파일 업데이트 완료 (정확한 날짜 확인: `date +"%Y-%m-%d"`)
- [ ] **CI 테스트(`pytest`) 실행 및 통과 확인 (필수)**
- [ ] ildangbaek_books.csv 업데이트 완료 (유튜브 업로드 정보 반영, 해당 시)
- [ ] 변경사항 확인 (git status)
- [ ] 커밋 메시지 작성
- [ ] **사용자에게 최종 확인 요청** (커밋/푸시 실행 전)
- [ ] 사용자 승인 후 커밋 실행
- [ ] 사용자 승인 후 푸시 실행

## 환경 정보

- **실행 머신**: Linux (세션은 Linux 머신에서만 실행)
- **Python**: 3.12.3, 가상환경 `.venv` 사용
- **Python 실행**: `.venv/bin/python` — 이 머신에는 `python` 명령이 없으므로 반드시 명시할 것
- **playwright 예외**: playwright는 시스템 python에만 설치돼 있어 NotebookLM 자동화 스크립트는 `python3`로 실행
- **프로젝트 루트**: `~/dev/jsong1230-github/booksummary`
- **영상 렌더링**: 로컬 금지, GPU 서버(192.168.0.150 / .151)에서 실행

## 주요 의존성

- `youtube-transcript-api`: YouTube 자막 추출
- `requests`: HTTP 요청
- `moviepy`: 영상 편집
- `Pillow`: 이미지 처리
- `openai`: OpenAI API (GPT, TTS)
- `anthropic`: Claude API
- `google-cloud-texttospeech`: Google Cloud TTS

## 프로젝트 구조 참고

```
booksummary/
├── input/              # 사용자가 준비한 파일들 (오디오, 썸네일, 비디오 등)
├── data/source/        # YouTube 자막 텍스트 파일
├── assets/
│   ├── audio/          # TTS 생성 오디오
│   ├── images/         # 책 커버 및 무드 이미지
│   ├── summaries/      # 책 요약 텍스트
│   └── video/          # NotebookLM 비디오
├── output/             # 최종 생성 영상 및 썸네일
├── scripts/            # 유틸리티 스크립트
├── src/                # 메인 소스 코드
└── secrets/            # API 키 및 인증 파일 (절대 커밋 금지)
```

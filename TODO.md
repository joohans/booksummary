# BookReview-AutoMaker 프로젝트 TODO

## 🚧 진행 중인 작업

### 선정 기준 실험 (2026-08-24 시작)

조회수의 70%가 검색이고 편당 성과는 "책 제목 검색 수요 × 검색 상위 진입"으로 결정된다
(→ `data/analytics_20260824.md`). 기준을 바꿔 제작 중.

- [x] Analytics 실측 및 8/22 진단 수정 (병목은 리텐션이 아니라 발행 공백 + 선정)
- [x] `scripts/measure_search_supply.py` 작성 (경쟁 강도 계량 + 제안어 출력)
- [x] 예약 큐 13편 한 칸씩 뒤로 밀어 실험 편 슬롯 확보
- [x] **생명이란 무엇인가** (경쟁 1,608) — 8/27 예약, `ntig_j4dKHo`
- [x] **화씨 451** (경쟁 1,423) — 8/31 예약, `uz4SWTTK73Q`
- [x] **부분과 전체** (경쟁 1,962) — 9/03 예약, `kxckIkN0_Cc`
- [ ] **결과 비교** — 경쟁 낮음 3편(8/27·8/31·9/03) vs 경쟁 높음 3연작.
      ⚠️ **30일이 아니라 60~90일로 연기**(8/30). 공개 시점 트래픽이 없어 30일로는 갈리지 않는다

### 새 선정 기준(검색 수요 × 공급)으로 제작한 편 — 2026-08-30 재개

발굴 공식: **한국 근현대문학 + 교과서 수록 + 고유명사 제목**. 후보 풀은 `data/candidates.md`.

- [x] **만세전** (염상섭, 경쟁 2,632) — 9/07 예약, `YhBewX4kj-g`
- [x] **우상의 눈물** (전상국, 1,408) — 9/10 예약, `dqc8CnTIEbc`
- [x] **수난이대** (하근찬, **747 = 최저 경쟁**) — 9/14 예약, `hsItetT2Ntk`
- [x] **유자소전** (이문구, 950) — 9/17 예약, `23WgiKeuLsQ`. 교과서 수록 단편 30건을 새로 계량해 선정
- [ ] 다음 편 착수 — **만무방**(김유정, 499 = 최저) · 레디메이드 인생(채만식, 1,119) ·
      기억 속의 들꽃(윤흥길, 1,496) 순. 전부 2회 측정 일치·중복 0건
      ⛔ 미리 쌓지 않는다(기본은 대기) — 공개 반응 보고 판단

### 제작 파이프라인 보강

- [x] **렌더 전 이미지 밝기 검사** (2026-09-01) — `scripts/check_image_brightness.py`.
      평균밝기 9.8인 사진 1장이 「수난이대」 64~67초를 검게 만들어 1시간 28분을 재렌더했다.
      **렌더 전에 반드시 실행**한다(README 2단계에 추가)
- [ ] **Flux 프롬프트 베이스 템플릿화** — `full frame` 명시 / 복장 명시 /
      생성 후 서명·글자 육안 확인. 매번 손으로 쓰지 않도록 스크립트에 고정
      - ★ **소재 블랙리스트가 핵심**(2026-09-01 확인): 표지판·비석·간판·액자·족자·실내 벽면·상점가.
        `no text/no signage/no signboard/no framed calligraphy` 를 다 넣어도 못 막는다.
        60장 중 15장을 글자로 폐기했다. 자연·정물·인물 소재만 안전하다
- [ ] **이미지 소요량 자동 계산** — 요약 길이 ÷ 4.5초로 필요 장수를 먼저 뽑고 생성하기.
      TTS 음성이 랜덤이라 같은 원고도 5:12~6:24로 흔들리고, 그만큼 필요 장수가 달라진다
- [ ] **스톡 다운로드는 `--keywords` 필수** — 한글 저자명으로는 검색 결과가 0이라
      같은 파일 10장만 덮어써진다. 영문 정밀 키워드 20개를 항상 넘길 것

- [x] **매일 반응 점검 루틴** (2026-08-25) — `scripts/daily_pulse.py`, cron 09:05,
      `data/daily_pulse_latest.md`. 댓글 점검(08:57)과 짝을 이룬다
- [x] **고정 댓글 전 편 게시 완료** (2026-08-26) — 총 **173편**. 공개 455편 중 누락 0편 검증
- [x] **따라잡기 자동화** — `run-pin-catchup.sh` + cron 16:10. 예약 편은 공개되면 자동 처리
- [x] **태그 수리 15편** (2026-08-26) — `scripts/fix_thin_tags.py`. 채널 조회 2위 편이 태그 3개였음
- [x] ⛔ **백카탈로그 되살리기는 성립하지 않음** (2026-08-26 검증) — 조회 0회 편 10권 중 9권이
      경쟁 압도 또는 무수요. 제목·태그로 되살아나지 않는다 → `data/analytics_20260826.md`
- [ ] **고정은 수동** — API 미지원(discovery 문서로 확인). 자동화는 Playwright 로만 가능하나
      실익 미검증이라 **상위 5편만 수동 고정해 효과 측정**하기로 결정(2026-08-25).
      기준선 `data/pin_experiment_baseline.json` (현재 전 편 좋아요 0·답글 0)

> ⛔ **2026-08-25 결정: 신규 제작 일시 중단.** 기준이 아직 검증 전인데 미리 쌓으면
> 틀렸을 때 틀린 편이 무더기로 남는다. 예약 큐도 10/16까지 16편 차 있다.
> **첫 실험 편(8/27) 공개 성과를 보고 방향을 미세조정한 뒤 재개**한다.
> 그동안 할 일은 성과 관측 · 후보 발굴 · 기존 편 손질(고정 댓글 등).

### 다음 제작 후보 → **`data/candidates.md` 가 단일 출처**

2026-08-26 기준 누적 55건 계량, **통과 10건**. 1순위는 **「만세전」(염상섭, 경쟁 2,632)** —
제안어에 **천재교육·미래엔**(교과서 출판사)이 있어 학교 수업 수요가 매년 반복된다.
우리 기존 승자(관부연락선·김은국 순교자)와 같은 한국 근대문학 축이다.

- 2~6순위: 니코마코스 윤리학 872 · 원미동 사람들 2,099 · 이중나선 752 ·
  공정하다는 착각 3,527 · 소유냐 존재냐 3,443
- 탈락 사유는 대부분 **다른 것이 검색어를 가져가는 경우**. 새 사례: 안티프래질 = 르세라핌 노래,
  변신 = 완구(또봇·변신필통), 광기의 역사 = 게임 리버스 1999, 주기율표 = 화학 수업(311,946)

## 📋 다음 작업 (우선순위별)

### 🔴 높은 우선순위 (YouTube 구독자 성장 전략 Phase 1)

- [x] 태그 스터핑 수정 (src/08_create_and_preview_videos.py) - 15개 제한, 무관 기관 태그 제거
- [x] 제목 공식 개선 - 훅 카피 + 파이프 포맷 (generate_hook_title 추가)
- [x] Description 첫 줄 개선 - AI 언급 제거, 책별 훅 문장 배치
- [x] Shorts 메타데이터 제목 개선 - 고정 문구 → 장르별 맞춤 훅 (src/26_generate_shorts.py)
- [x] **OAuth 재인증** 완료 - `scripts/reauth_youtube.py` 실행, Analytics+Readonly 스코프 추가 및 .env 자동 갱신
- [x] **분석 기준선 확보** 완료 - `data/analytics_baseline_20260222.md` 생성 (구독자 172명, 총 영상 254개, Top 10 확인)
- [ ] **Shorts 일괄 생성** - 다음 영상 제작 시 assets 준비 후 `python src/26_generate_shorts.py` 실행 (우선: 생각에 관한 생각 EDfOZfYtCbI)
- [ ] **업로드 시간 변경** - 자정(00시) → 오후 7시(19시 KST)로 변경 검토 (한국 황금 시간대)
- [ ] **저참여율 영상 재최적화** - 특이점이 온다(1.03%), 나는 고양이로소이다(1.32%) 제목·썸네일 업데이트
- [ ] **기존 댓글 전수 응답** - 254개 영상 미응답 댓글 답글 달기 (수동, YouTube Studio)

### 🟡 중간 우선순위

- [x] **영상 언어·태그 일괄 정정 완료** (2026-08-14, 330개 전량) - 태그 소실 96개 복구, 오디오 언어 289개 정정
- [x] **태그 "미반영" 경고 원인 규명 및 수정** (2026-08-17, `src/09_upload_from_metadata.py`)
  - [x] 원인: `videos().list`의 업로드 직후 읽기 전파 지연 → 정상 반영을 실패로 오탐하던 것
  - [x] `_ensure_tags_applied()` 검증 기준을 `videos().update` 응답으로 변경
  - [x] 공백→언더스코어 변환 제거 (YouTube는 공백 복합 태그 정상 허용)
  - [x] 개별 태그 30자 상한 완화 (31자 태그 정상 수락 실측), 500자 합계에 따옴표 2자 반영
- [x] 제휴 링크 일괄 업데이트 (246개 영상 완료)
- [x] 일괄 고정 댓글 추가 기능 (246개+ 영상)
- [x] 프로젝트 문서화 (.moai/project/ 생성)
- [x] CI/CD 파이프라인 구축 (선택사항)

### 🟢 낮은 우선순위

_현재 낮은 우선순위 작업이 없습니다_

## 🐛 알려진 이슈

- [ ] **`data/uploaded_books.csv`에 2026-01-04 이전 업로드가 누락** (2026-08-21 발견)
  - CSV 359행 vs history.md 업로드 URL 543건 — 초기 업로드분이 CSV에 없음
  - 이 때문에 「오이디푸스 왕」을 미업로드로 오판해 중복 제작(일당백 기존 → summary+video)
  - 손자병법·군주론·국가도 같은 이유로 "미업로드"로 잘못 분류됨
  - **임시 대응**: 중복 체크 시 `uploaded_books.csv` + `history.md` 양쪽을 한글·영문으로 각각 grep
  - **근본 대응(미착수)**: history.md에서 초기 업로드분을 파싱해 CSV 백필, 또는
    `13_update_csv_from_youtube.py`를 채널 전체 재스캔 모드로 실행

- [ ] **`data/ildangbaek_books.csv`의 `status=uploaded`가 실제 업로드를 뜻하지 않음** (2026-08-22 발견)
  - 1984·죄와 벌·동물농장 세 건 모두 `uploaded`에 날짜까지 있었으나 한글판은 존재하지 않았음
  - ⚠️ **자동 판별 불가** (2026-08-24 실측). `video_created`가 빈 채 `youtube_uploaded`만 있는
    패턴을 오류 표식으로 쓰려 했으나, 그 97건 중 **74건은 실제 업로드분**이었다
    (노인과 바다·햄릿·위대한 개츠비 등) — 단순 기록 누락일 뿐이다.
    제목 부분문자열 매칭도 표기 차이로 오탐한다(「오이디푸스왕」↔「오이디푸스 왕」)
  - **대응**: 중복 판정은 YouTube API 제목만 사용 (`data/.video_titles_cache.json`),
    책 단위로 사람이 확인

- [ ] **`02_get_images.py`의 후보 풀이 목표치와 같으면 저품질이 전부 살아남음** (2026-08-22)
  - AI 검증은 상위 N개만 남기는 방식이라, 130개 받아 100개를 남기면 저점수(≤4점)가 39개까지 섞임
  - **대응**: `--skip-validation`으로 풀을 2배(210개)로 받은 뒤 `validate_images_with_ai(target_count=100)`를 별도 호출 → 저점수 0개 달성
  - 개선안: 다운로드 배수(현재 1.3배)를 2배로 올리거나, 저점수 비율이 높으면 자동 추가 수집

- [ ] **`02_get_images.py`가 한글 제목/저자만으로는 이미지를 거의 못 받음** (2026-08-21)
  - 「오이디푸스 왕」/「소포클레스」로 10개, 「오디세이아」로 35개만 수집됨 (목표 100개)
  - **대응**: `--keywords`로 영문 정밀 키워드 20개를 직접 지정하면 100개 확보 가능
  - 개선안: 한글 키워드 결과가 목표치 미달이면 영문 키워드로 자동 폴백

- [x] **`25_batch_add_pinned_comments.py` 제목 파싱 해결** (2026-08-26)
  - 패턴 7·8(저자 콜론 없는 일당백) + 패턴 9(범용 폴백: 대괄호 태그 선택·`Complete Guide to` 접두어)
  - 상태 파일 스킵을 기본에서 제거(`--resume` 으로만) — 낡은 "처리됨"이 67편을 숨기고 있었다
  - dry-run 이 상태 파일을 오염시키던 버그도 수정. 전 편 파싱 성공 (실패 0건)

## 🔮 향후 계획

### Phase 8: 품질 개선 및 최적화

- [x] 무드 이미지 품질 개선 (책 내용 관련성 향상)
  - [x] generic 키워드 18개 제거 (책과 무관한 범용 검색어 오염 방지)
  - [x] AI 프롬프트 강화 (책 고유 장면/배경 중심 키워드 생성)
  - [x] Summary 텍스트 2000자 → 4000자 확장
  - [x] AI 키워드 충분 시 basic 키워드 병합 생략
  - [x] AI 모델 업데이트 (claude-sonnet-4-6, gpt-4o)
  - [x] `validate_images_with_ai()` 추가 (GPT-4o Vision으로 관련성 검증, 상위 100개 선별)
  - [x] 기본 다운로드 목표 130개로 상향 (검증 후 100개 유지)
  - [x] `--skip-validation` CLI 플래그 추가
- [x] 영상 품질 향상 (해상도, 비트레이트 최적화)
- [x] 처리 속도 최적화 (병렬 처리, 캐싱)
- [x] 에러 핸들링 개선 (재시도 로직, 상세한 에러 메시지)
- [x] 로깅 시스템 개선 (구조화된 로그, 로그 레벨 관리)
  - [x] 로깅 유틸리티 모듈 생성 (`src/utils/logger.py`)
  - [x] 로그 레벨 관리 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - [x] 파일 로그와 콘솔 로그 분리
  - [x] 로그 파일 로테이션 (크기 기반, 최대 10MB, 5개 백업)
  - [x] 환경 변수로 로그 레벨 설정 가능 (`LOG_LEVEL`)
  - [x] 컬러 콘솔 출력 및 이모지 지원
  - [ ] 주요 스크립트에 로깅 시스템 적용 (점진적 업데이트)

### Phase 9: 분석 및 모니터링

- [x] YouTube Analytics API 연동
  - [x] YouTube Analytics API v2 연동 모듈 생성 (`src/15_youtube_analytics.py`)
  - [x] 채널 및 영상 메트릭 수집 기능 구현
  - [x] 조회수, 좋아요, 댓글, 시청 시간 등 메트릭 수집
  - [x] 메트릭 데이터를 JSON/CSV 형식으로 저장
  - [x] 주간/월간 리포트 자동 생성 (Markdown 형식)
- [x] 성능 대시보드 구축
  - [x] HTML 기반 대시보드 생성 (`src/16_dashboard.py`)
  - [x] 채널 통계 카드 (총 영상 수, 조회수, 좋아요, 댓글 수 등)
  - [x] 조회수 상위 10개 영상 테이블
  - [x] 조회수 분포 차트 (Chart.js 사용)
  - [x] 최근 업로드 영상 목록
  - [x] Analytics 코드 점검 및 개선 (스코프 문제 처리)

### Phase 10: 콘텐츠 다양화

- [ ] 다양한 영상 스타일 템플릿 추가
- [x] 배경 음악 자동 추가 기능
  - [x] 일당백 스타일 영상에 배경음악 자동 탐지 및 다운로드 기능 추가
  - [x] Pixabay Music에서 자동 다운로드 기능 통합
  - [x] 인포그래픽 클립에 배경음악 자동 적용
- [x] 챕터 마커 자동 생성
  - [x] YouTube 챕터 마커 자동 생성 기능 구현
  - [x] 메타데이터의 timestamp를 YouTube 챕터 형식으로 변환
  - [x] description 맨 앞에 챕터 마커 자동 추가
- [x] 영상 시각화 개선 (Summary+Video 파이프라인)
  - [x] 동적 자막(Kinetic Typography): 키워드 추출 + Whisper 타이밍, 팝 효과
  - [x] 파형(Waveform) 시각화: 오디오 스펙트럼 하단 시각화(실시간 스크롤)
  - [x] Pexels API 푸티지: 키워드 기반 관련 영상 검색·다운로드 (`PEXELS_API_KEY` 사용)
- [x] 제목 전략 개선: AI 언급 대신 가치·인간적 호기심 강조 (`src/utils/title_generator.py`)
- [x] 제목 부제(괄호) SEO 키워드 자동 생성 (장르 기반 템플릿)
- [x] 제목 100자 제한 강화: 부제 우선 축소 후 절단
- [x] 고정 댓글 활용: 챕터 타임스탬프 + 참여 유도 질문 자동 생성, 업로드 시 댓글 등록 (`src/utils/pinned_comment.py`, 수동 고정은 YouTube UI에서)
- [x] 제휴 링크 자동 삽입 기능 (`src/utils/affiliate_links.py`)
  - [x] Amazon Associates 제휴 링크 자동 생성
  - [x] 한글/영문 영상 description에 제휴 섹션 자동 삽입
  - [x] 기존 영상 일괄 업데이트 스크립트 (`src/24_batch_update_affiliate_links.py`)
  - [x] 멱등성 보장 및 안전 장치 (`--dry-run`, `--apply`)
  - [x] 작가명 검색어 제외로 검색 정확도 향상
- [x] 일괄 고정 댓글 기능 (`src/25_batch_add_pinned_comments.py`)
  - [x] Google Books API로 책 존재 여부 검증
  - [x] 기존 댓글 업데이트 지원
  - [x] 246개+ 영상에 제휴 링크 고정 댓글 추가 완료
- [ ] 다국어 지원 확대 (일본어, 중국어 등)

### Phase 11: 시청자 유입 및 채널 성장 개선 (완료: 2026-02)

**Phase A: Quick Wins (기존 코드 최적화)**
- [x] 장르 기반 동적 해시태그 자동 생성 (`src/utils/title_generator.py`)
  - [x] `generate_hashtags()` 함수 추가 (8개 장르: 철학, 심리, 비즈니스, 역사, 과학, 시, 에세이, 소설)
  - [x] summary_video / full_episode 콘텐츠 타입 구분
  - [x] 한글/영문 장르별 해시태그 세트 (4-5개)
- [x] Summary+Video description 해시태그 동적 변환 (`src/08_create_and_preview_videos.py`)
  - [x] KO/EN description 3곳 모두 정적 해시태그 → `generate_hashtags()` 호출로 대체
- [x] Episode description 해시태그 동적 변환 (`src/20_create_episode_metadata.py`)
  - [x] KO/EN description 정적 해시태그 → `generate_hashtags()` 호출로 대체
- [x] Summary 기본 길이 5분 → 6분으로 상향 (`src/10_create_video_with_summary.py`)
  - [x] `--summary-duration` 기본값 5.0 → 6.0 (총 영상 8-10분, 미드롤 광고 활성화)
  - [x] 단어 수 목표 동적 레이블 (750→900단어 자동 반영) (`src/08_generate_summary.py`)
- [x] Ken Burns 효과 기본 활성화 (`src/03_make_video.py`)
  - [x] `create_image_sequence()` `use_ken_burns=True` 기본값
  - [x] zoom_in/zoom_out 교대 + left/right/None 패닝 순환
  - [x] 실패 시 정적 이미지 자동 폴백

**Phase B: 신규 기능 개발**
- [x] YouTube Shorts 자동 생성 (`src/26_generate_shorts.py`)
  - [x] 9:16 세로 포맷 (1080x1920), 최대 59초
  - [x] Short 1: HOOK 섹션 기반 (첫 30초), Short 2: 핵심 인용구, Short 3: 한 줄 요약
  - [x] TTS 오디오 + 무드 이미지 슬라이드쇼 + 텍스트 오버레이
  - [x] Shorts 전용 메타데이터 JSON 생성 (`#Shorts` 해시태그 포함)
- [x] 플레이리스트 자동 관리 (`src/27_manage_playlists.py`)
  - [x] 7개 장르별 플레이리스트 자동 생성/업데이트
  - [x] 채널 전체 영상 장르 자동 분류 및 배치
  - [x] `--apply` 플래그로 dry_run 기본 (안전 우선)
  - [x] 단일 영상 플레이리스트 추가 (`--video-id`)
- [x] 고정 댓글 CTA 강화 (`src/utils/pinned_comment.py`)
  - [x] "다음에 어떤 책을 리뷰할까요?" 댓글 추천 CTA 추가
  - [x] 좋아요/구독/알림 설정 CTA 추가

**Phase C: 커뮤니티 자동화**
- [x] 커뮤니티 탭 자동 포스팅 (`src/28_community_posts.py`)
  - [x] 인용구 포스트: Summary 파일에서 명문장 자동 추출
  - [x] 투표 포스트: 다음 리뷰 책 추천 투표 (최대 5개 후보)
  - [x] 업데이트 포스트: 채널 근황 메시지
  - [x] 주간 자동 스케줄링 (월: 인용구, 수: 투표, 금: 업데이트)
  - [x] `--apply` 플래그로 dry_run 기본

---

## ✅ 완료된 Phase

### Phase 1: 자료 수집 자동화 (완료: 2025-11)

- [x] 책 제목 입력 (단일/일괄 처리 지원)
- [x] URL 탐색 (위키백과, 온라인 서점, 뉴스 리뷰 타겟)
- [x] 텍스트 파일 출력 (NotebookLM용)
- [x] 표지 이미지 다운로드 ([Google Books API](src/01_download_cover_image.py))
- [x] 무드 이미지 다운로드 ([Pexels/Unsplash API](src/02_download_mood_images.py), 5~10장)
- [x] 가상환경 설정 및 패키지 설치
- [x] 실행 스크립트 작성

### Phase 2: NotebookLM 오디오 생성 (완료: 2025-11)

- [x] NotebookLM 사용법 문서화 (README.md에 통합)

### Phase 3: 이미지 자산 확보 (완료: 2025-11)

- [x] 표지 이미지: Google Books API로 고화질 표지 다운로드
- [x] 무드 이미지: 키워드 기반으로 5~10장 다운로드
- [x] 저장: `assets/images/{책제목}/` 폴더에 정리

### Phase 4: 영상 합성 및 편집 (완료: 2025-11)

- [x] 오디오 로드: `assets/audio/`의 오디오 파일 로드
- [x] 이미지 시퀀스: 오디오 길이에 맞춰 이미지 배분
- [x] Ken Burns 효과: 줌인/패닝 효과 구현
- [x] 전환 효과: 이미지 간 페이드 효과
- [x] Summary audio와 Review audio 자동 연결
- [x] 자막 (옵션): OpenAI Whisper로 자막 추출 및 오버레이
- [x] 렌더링: 1080p, 30fps MP4 출력

### Phase 5: 메타데이터 및 썸네일 (완료: 2025-11)

- [x] en/kr 언어별 메타데이터 자동 생성 (title, description, tags)
- [x] 메타데이터 JSON 파일 저장
- [x] 썸네일 자동 생성 (한글/영문 버전)
- [x] 썸네일 업로드 기능

### Phase 6: 완전 자동화 파이프라인 (완료: 2025-11)

- [x] Summary/Review 오디오 자동 탐지
- [x] en/kr 언어별 영상 자동 생성 (summary 포함)
- [x] en/kr 언어별 메타데이터 자동 생성 및 저장
- [x] en/kr 언어별 썸네일 자동 생성
- [x] 통합 파이프라인 스크립트 ([13_complete_pipeline.py](src/13_complete_pipeline.py))
- [x] 실행 스크립트 ([run_complete_pipeline.sh](run_complete_pipeline.sh))

### Phase 7: YouTube 업로드 (완료: 2025-11)

- [x] 메타데이터 기반 자동 업로드
- [x] 썸네일 자동 업로드
- [x] 업로드 로그 관리 (JSON, CSV, TXT)
- [x] CSV 파일 자동 업데이트

### Phase 8: 파이프라인 표준화 및 이미지 다양성 개선 (완료: 2025-12)

- [x] 언어 접미사 표준화 (`ko` -> `kr`) 및 영문 표준 제목 기반 디렉토리 통합
- [x] 이미지 다양성 향상 (AI 키워드 파싱 버그 수정, Fallback 리스트 확장)
- [x] CI 테스트 안정화 (`pytest.ini` 설정) 및 `.cursorrules` 검증 프로세스 추가
- [x] 유튜브 업로드 프로세스 표준화 대응 및 썸네일 용량 최적화 (`.jpg` 변환)

### 프로젝트 관리 (완료: 2025-11)

- [x] 프로젝트 문서화 ([README](README.md), [TODO](TODO.md), [HISTORY](history.md), [RULES](.cursorrules))
- [x] Git 자동 커밋/푸시 설정
- [x] 커밋 전 필수 작업 규칙 추가 ([.cursorrules](.cursorrules))
- [x] TODO.md에서 history 성 데이터 제거
  - "최근 완료 작업 (최근 2주)" 섹션 전체 제거
  - TODO.md는 현재 작업과 향후 계획만 관리하도록 정리
- [x] 코드 리팩토링 및 파일 정리
  - src/09_text_to_speech.py 삭제 및 src/09_text_to_speech_multi.py로 통합
  - 민감한 인증 정보들을 secrets/ 폴더로 이동 및 관리
  - 불필요한 테스트 스크립트 삭제

---

## 📚 참고 문서

- [README.md](README.md) - 프로젝트 개요 및 사용법
- [HISTORY.md](history.md) - 상세 작업 이력
- [.cursorrules](.cursorrules) - 프로젝트 규칙 및 가이드라인
- [docs/URL_COLLECTION_PROMPT.md](docs/URL_COLLECTION_PROMPT.md) - URL 수집 프롬프트

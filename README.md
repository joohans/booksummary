# BookReview-AutoMaker

NotebookLM 기반 책 리뷰 영상 자동 생성기

## 프로젝트 개요

이 프로젝트는 NotebookLM을 활용하여 책 리뷰 영상을 자동으로 생성하는 파이프라인입니다.
사용자가 NotebookLM에서 생성한 비디오 파일(선택사항)과 요약 텍스트를 업로드하면, AI가 자동으로 요약 오디오를 생성하고 이미지를 합성하여 유튜브 영상을 제작합니다.

**생성되는 영상 구조:**

- Summary (요약 오디오 + 이미지 슬라이드쇼; 동적 자막·파형 시각화·관련 푸티지 선택 적용)
- 2초 silence (검은 화면)
- NotebookLM Video (선택사항, 있으면 자동 포함)

## 전체 워크플로우 (6단계)

1. **NotebookLM 비디오 준비** (선택사항):
   - NotebookLM 비디오를 `assets/video/{책제목}_notebooklm_{언어}.{확장자}` 형식으로 저장
   - 비디오가 없어도 Summary만으로 영상 생성 가능
2. **관련 이미지 확보**: 책 제목과 관련된 고품질 무드 이미지를 **100개** 자동으로 수집합니다. (`assets/images/{책제목}/` 폴더)
3. **Summary 오디오 생성**: 5분 분량의 책 요약(한글/영문)을 생성하고 TTS로 MP3 변환합니다. 생성된 Summary 오디오는 `assets/audio/{책제목}_summary_{언어}.mp3` 형식으로 저장됩니다.
4. **영상 합성**: Summary 오디오 + 2초 silence + NotebookLM Video (선택사항) 순서로 영상을 생성합니다. Summary 자막은 옵션(`--subtitles`)이며 기본은 비활성화입니다. 생성된 영상은 `output/{표준제목}_{kr/en}.mp4` 형식으로 저장됩니다.
5. **배포 준비**: 썸네일과 메타데이터를 생성합니다. 썸네일은 자동으로 찾아서 메타데이터에 포함됩니다.
6. **유튜브 업로드**: 메타데이터 파일을 기반으로 유튜브에 자동 업로드합니다.

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd booksummary
```

### 2. 가상환경 설정

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 API 키를 설정하세요.

**필수 API 키:**

- `GOOGLE_BOOKS_API_KEY`: 책 표지 이미지 다운로드용
- `PEXELS_API_KEY`: 무드 이미지 다운로드용 (1순위), 영상 푸티지 검색용 (선택, 시각화 개선 시)
- `PIXABAY_API_KEY`: 무드 이미지 다운로드용 (2순위, 선택사항)
- `UNSPLASH_ACCESS_KEY`: 무드 이미지 다운로드용 (3순위, 선택사항)
- `OPENAI_API_KEY`: Summary 생성 및 TTS용
- `CLAUDE_API_KEY`: Summary 생성용 (선택사항)
- `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`: YouTube 업로드용
- `YOUTUBE_CHANNEL_ID`: 업로드할 채널 ID (선택사항, 기본값: book summary 채널)
- `GOOGLE_APPLICATION_CREDENTIALS`: Google Cloud TTS 사용 시 (선택사항, `secrets/google-cloud-tts-key.json` 파일 경로)
- `REPLICATE_API_TOKEN`: Replicate TTS 사용 시 (선택사항)
- `ELEVENLABS_API_KEY`: ElevenLabs TTS 사용 시 (선택사항)
- `OPENROUTER_API_KEY`: ElevenLabs를 OpenRouter를 통해 사용 시 (선택사항)
- `LOG_LEVEL`: 로그 레벨 설정 (선택사항, 기본값: INFO, 가능한 값: DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `AMAZON_ASSOCIATE_TAG`: Amazon Associates 제휴 링크용 (선택사항, 예: `joohans-20`)
- `ALADIN_PARTNER_ID`: 알라딘 파트너스 제휴 링크용 (선택사항)
- `YES24_PARTNER_ID`: Yes24 제휴 링크용 (선택사항)

## 어떤 책을 만들지 정하는 법 (선정 기준)

채널 조회수의 **70%가 검색**에서 오고, 성과가 좋은 영상은 전부 **정확한 책 제목 검색**으로
유입된다 (2026-08-24 Analytics 실측 → `data/analytics_20260824.md`).
따라서 편당 성과는 사실상 **"그 책 제목의 한국어 검색 수요 × 우리가 검색 상위에 걸리는지"**로
결정된다. 판매순위가 높아도 경쟁이 세거나 검색어를 다른 콘텐츠가 가져가면 값이 남지 않는다.

```bash
# 1) 후보 발굴 — 알라딘 판매순위 기준, 이미 다룬 책은 자동 제외
.venv/bin/python scripts/find_candidates_aladin.py --category 고전 --limit 40

# 2) 후보의 '공급'(경쟁)과 '의도'를 계량
.venv/bin/python scripts/measure_search_supply.py --titles "화씨 451|브래드버리" "부분과 전체|하이젠베르크"
.venv/bin/python scripts/measure_search_supply.py --file candidates.txt --limit 20
.venv/bin/python scripts/measure_search_supply.py --validate   # 기존 업로드분으로 지표 점검

# 3) 후보의 '수요'를 계량 (2026-09-08 추가 — 공급만 재던 문제 보완)
.venv/bin/python scripts/measure_search_demand.py --provider naver --file candidates.txt
.venv/bin/python scripts/measure_search_demand.py --titles "만세전" "수난이대"   # trends(키 불필요)
.venv/bin/python scripts/measure_search_demand.py --validate   # 성숙 표본으로 지표 검증
```

### 수요 축 (`measure_search_demand.py`)

공급(경쟁)만으로는 **"공급이 적어서 경쟁이 낮은 것"과 "아무도 안 찾아서 경쟁이 낮은 것"** 을
가르지 못합니다. 실제로 「파이프 이야기」는 경쟁 0으로 '경쟁낮음' 판정을 받고도 조회 꼴찌(11회)였습니다.

같은 성숙 표본(n=20)에서 두 지표를 비교한 결과입니다.

| 지표 | Spearman ρ |
|---|---:|
| 경쟁 중간값 (공급) | **−0.171** |
| 검색 수요 (Google Trends) | **+0.391** |

**제공자 두 가지 (naver 키는 2026-09-09 연결 완료):**

| | 키 | 값 | 한계 |
|---|---|---|---|
| `--provider naver` (권장) | `.env` 3개 | **월간 절대 검색수** (최소 10회까지 해상도) | — |
| `--provider trends` | 불필요 | 앵커 대비 상대값 | 아래 두 가지 |

**판정 규칙: 수요 ≥ 300회/월 AND 경쟁 < 5,000. 그 안에서 수요/경쟁 비율로 순위.**

> ⛔ **비율만으로 순위를 매기면 안 됩니다.** 경쟁 0인 책이 비율 최상위로 올라가는데
> 실제로는 무검색입니다. 성숙 표본(n=20)에서 지표별 상관은 이렇습니다.
>
> | 지표 | Spearman ρ |
> |---|---:|
> | 경쟁 단독 | −0.135 |
> | **수요 단독** | **+0.338** |
> | 수요 ÷ 경쟁 | −0.047 |
>
> 수요 단독이 가장 낫지만 **n=20에서 통계적으로 유의하지는 않습니다(p≈0.15).**
> 방향이 맞다는 것이지 확증은 아닙니다 — 12월 판독 때 다시 검증해야 합니다.
>
> 수요 축이 실제로 걸러낸 사례: 「논 이야기」(경쟁 1,037로 통과였으나 **수요 140회/월**) ·
> 「타인의 방」(경쟁 1,453 / **수요 140회/월**). 공급만 보면 「파이프 이야기」류
> (경쟁 0인데 조회 11회)를 후보로 올리게 됩니다.

> ⚠️ **Google Trends 의 실측 한계 (2026-09-08)**
> 1. 앵커보다 훨씬 작은 키워드는 **0으로 반올림**됩니다. 「노인과 바다」를 앵커로 쓰자
>    20편 중 9편이 0이 됐고 그 안에 조회 11회와 297회가 섞여 구분되지 않았습니다.
>    → 우리 구간에 맞는 **작은 앵커**(`ANCHOR = "물고기는 존재하지 않는다"`)를 기본값으로 씁니다
> 2. **20~30건이면 429로 IP가 몇 시간 막힙니다.** 요청 간 45초를 둬도 마찬가지입니다.
>    후보 수십 건을 계량하려면 `--provider naver` 가 필요합니다
>
> 네이버 키 발급: https://searchad.naver.com → 도구 > API 사용 관리 (무료).
> `.env` 에 `NAVER_AD_API_KEY` / `NAVER_AD_SECRET_KEY` / `NAVER_AD_CUSTOMER_ID`

판정 기준:

| 지표 | 기준 | 근거 |
|---|---|---|
| 경쟁 조회수 중간값 | 5,000 미만이면 상위 진입 가능 (⚠️ 아래 참조) | 히치하이커 2,644 → 1,958회 / 모비딕 39,140 → 516회 |
| 제안어 | **사람이 눈으로 읽는다** | 「엔트로피」=화장품 브랜드, 「동물농장」=SBS TV, 「갈매기」=갈매기살 |

> 🔴 **2026-09-08 검증: 경쟁 중간값은 성과를 예측하지 못한다.**
> 독립된 두 표본에서 Spearman ρ 가 전부 0 근처였다
> (검증군 n=10 → +0.018 / 성숙 표본 n=20 → −0.171 / 수요희박 제외 n=15 → +0.021).
> 위 표의 "히치하이커 vs 모비딕" 근거는 **이상치 한 편이 만든 착시**였다.
> 반례: 인간 실격(경쟁 169,344 → 조회 302, 3위) / 파이프 이야기(경쟁 0 → 조회 11, 꼴찌).
>
> 원인은 **공급만 재고 수요를 안 재기 때문**이다. 경쟁이 낮은 이유가
> "공급이 적어서"인지 "아무도 안 찾아서"인지 지표가 가르지 못한다.
> → 수요 측 지표(검색량) 도입이 다음 과제. 상세는 `history.md` 2026-09-08.
>
> ⚠️ 단, 이 결과를 "새 선정 기준이 틀렸다"로 읽으면 안 된다. 검증 표본은 전부 옛 기준 편이고,
> 새 기준(한국 근현대문학 + 교과서 수록) 9편은 아직 성숙하지 않았다. **판정은 12월 초.**

> ⚠️ 자동완성 제안어의 '책 의도 비율'을 합성 점수로 만들려는 시도는 실패했다.
> 표본이 작아 변형마다 결과가 뒤집힌다. **경쟁 강도만 자동 판정하고 의도는 사람이 본다.**
>
> ⚠️ `search.list` 는 호출당 100 units(일일 10,000)다. 업로드 1건이 1,600 units 이므로
> 업로드 예정일에는 `--limit` 을 줄인다.

중복 판정은 **YouTube API 의 실제 영상 제목**만 신뢰한다. CSV의 `status=uploaded` 는
실제 업로드를 뜻하지 않는다 (1984·죄와 벌·동물농장 세 건 모두 오기록 실측).

## 빠른 시작 가이드 (처음 시작하는 경우)

> **💡 처음 사용하시나요?** 이 섹션을 먼저 읽어보세요. 전체 프로세스를 단계별로 안내합니다.

### 📋 1단계: 작업 전 준비사항

**input 폴더에 파일 준비하기**

프로젝트 루트의 `input/` 폴더에 다음 파일들을 준비하세요. 파일명은 `{prefix}_타입_{언어}.{확장자}` 형식을 따라야 합니다.

**필수 파일:**
- 없음 (모든 파일이 선택사항이며, Summary는 AI가 자동 생성 가능)

**선택 파일:**
- `{prefix}_summary_en.md` - 영어 요약 텍스트 (없으면 AI가 자동 생성)
- `{prefix}_summary_kr.md` - 한국어 요약 텍스트 (없으면 AI가 자동 생성)
- `{prefix}_thumbnail_en.png` - 영어 썸네일 원본
- `{prefix}_thumbnail_kr.png` - 한국어 썸네일 원본
- `{prefix}_video_en.mp4` - 영어 NotebookLM 비디오 (선택사항, 있으면 영상에 포함)
- `{prefix}_video_kr.mp4` - 한국어 NotebookLM 비디오 (선택사항, 있으면 영상에 포함)

**파일명 예시 (prefix: `lonliness`):**
```
input/
├── lonliness_summary_en.md
├── lonliness_summary_kr.md
├── lonliness_thumbnail_en.png
├── lonliness_thumbnail_kr.png
├── lonliness_video_en.mp4
└── lonliness_video_kr.mp4
```

### 🤖 NotebookLM 완전 자동화 (NEW)

> **💡 원클릭 자동화**: 책 제목과 저자만 입력하면 URL 수집부터 YouTube 업로드까지 완전 자동화!

NotebookLM을 활용한 완전 자동화 파이프라인을 사용하면 수동 작업 없이 영상을 생성할 수 있습니다.

#### 사전 준비 (최초 1회)

```bash
# 1. NotebookLM 로그인 세션 생성
python scripts/notebooklm_automator.py --login
```

브라우저가 열리면 Google 계정으로 로그인하세요. 세션은 `~/.notebooklm_session.json`에 저장됩니다.

#### 기본 사용법

```bash
# 한글+영문 영상 모두 생성 (기본)
python scripts/notebooklm_full_pipeline.py \
  --book-title "어린왕자" \
  --author "앙투안 드 생텍쥐페리"

# 한글만 생성
python scripts/notebooklm_full_pipeline.py \
  --book-title "어린왕자" \
  --author "앙투안 드 생텍쥐페리" \
  --language ko

# 업로드 없이 영상만 생성
python scripts/notebooklm_full_pipeline.py \
  --book-title "어린왕자" \
  --author "앙투안 드 생텍쥐페리" \
  --skip-upload
```

#### 파이프라인 단계

1. **URL 수집** (병렬): 한글/영어 관련 자료 30개 자동 수집
2. **NotebookLM 비디오 생성** (순차): Playwright로 자동 생성 (최대 35분 소요)
3. **이미지 다운로드**: 책 관련 이미지 100개 수집
4. **영상 제작**: Summary + NotebookLM Video 합성
5. **메타데이터 생성**: YouTube 업로드용 메타데이터
6. **YouTube 업로드** (선택): 비공개/공개 설정 가능

#### 고급 옵션

```bash
# 중단된 파이프라인 재개
python scripts/notebooklm_full_pipeline.py \
  --book-title "어린왕자" \
  --resume

# 특정 단계만 재시도
python scripts/notebooklm_full_pipeline.py \
  --book-title "어린왕자" \
  --retry-step notebooklm_ko

# TTS 옵션 지정
python scripts/notebooklm_full_pipeline.py \
  --book-title "어린왕자" \
  --tts-provider google \
  --tts-voice ko-KR-Neural2-B

# 공개 업로드
python scripts/notebooklm_full_pipeline.py \
  --book-title "어린왕자" \
  --privacy public
```

#### 상태 파일

파이프라인 진행 상태는 `.pipeline_state/{책제목}_state.json`에 저장됩니다.
실패 시 `--resume` 옵션으로 중단된 지점부터 재시작할 수 있습니다.

---

### 🚀 2단계: 전체 파이프라인 실행 (기존 방식)

파일을 준비했다면, 다음 명령어로 전체 프로세스를 한 번에 실행합니다:

```bash
python scripts/run_full_pipeline_from_downloads.py \
  --book-title "책 제목" \
  --author "저자 이름" \
  --prefix "파일명접두사" \
  --language both
```

**실제 예시:**
```bash
python scripts/run_full_pipeline_from_downloads.py \
  --book-title "The Loneliness of Sonia and Sunny (소니아와 써니의 고독)" \
  --author "키란 데사이" \
  --prefix "lonliness" \
  --language both
```

**이 명령어가 하는 일:**
1. ✅ input 폴더에서 파일 찾기 및 표준 네이밍으로 이동
2. ✅ 이미지 다운로드 (100개, 기존 이미지가 있으면 건너뜀)
3. ✅ Summary 생성 (파일이 없으면 AI가 자동 생성)
4. ✅ TTS로 Summary 오디오 생성 (**필수**: 실패 시 중단)
5. ✅ 영상 생성 (Summary + NotebookLM Video)
6. ✅ 메타데이터 생성 (timestamp 자동 포함)

### ⚠️ 렌더 전 필수: 이미지 밝기 검사

렌더는 1시간 이상 걸리므로, **렌더를 시작하기 전에** 이미지 풀의 밝기 이상치를 걸러냅니다.
너무 어두운 사진이 한 장 섞이면 영상에서 그 4초가 화면이 꺼진 것처럼 보입니다.

```bash
# 보고만 (기본)
.venv/bin/python scripts/check_image_brightness.py assets/images/{영문제목}

# 이상치를 _rejected/ 로 격리
.venv/bin/python scripts/check_image_brightness.py assets/images/{영문제목} --move
```

- 평균밝기 **30 미만**(검은 화면으로 읽힘) / **245 초과**(흰 화면)를 이상치로 잡습니다
- 동굴·야간처럼 **의도적으로 어두운 컷**(평균 30~60대)은 통과합니다 — 문제는 내용이 안 보이는 한 자릿수입니다
- 실측: 「수난이대」에서 평균밝기 9.8인 사진 1장이 64~67초를 검게 만들어 재렌더했습니다
- 판정은 σ 값이 아니라 **피사체가 읽히는가**로 합니다. σ 11.6이어도 형태가 뚜렷하면 유지하고,
  평균 3.0/σ13처럼 내용이 안 보이는 것만 제거합니다

### ⚠️ 렌더 전 필수: 파일명 규칙과 밝기 교차 배치

렌더러는 **`glob("mood_*.jpg")`** 만 읽고, **파일명 정렬 순서 그대로** 이미지를 순환시킵니다
(셔플하지 않습니다). 여기서 사고가 두 번 났습니다.

1. **Flux 산출물을 `flux_*.jpg` 로 저장하면 통째로 무시됩니다.** 2026-09-08 「B사감과 러브레터」에서
   Flux 38장이 빠진 채 스톡 48장만 2회 반복되어 렌더를 1회 버렸습니다.
   → 추가 이미지는 **반드시 `mood_*.jpg`**
2. **어두운 컷이 연달아 배치되면 검은 화면 구간이 생깁니다.** 「니코마코스 윤리학」에서
   촛불 3장이 붙어 20초가 거의 검게 나왔습니다.
   → 밝기 오름차순 정렬 후 **밝은/어두운 절반을 교차**시켜 `mood_001..NNN` 으로 재명명하면
   어두운 컷 연속이 1장(4.5초)으로 떨어집니다

렌더 시작 직후 로그의 **`무드 이미지 N개`** 와 **`반복 횟수`** 두 줄을 반드시 확인하세요.

**밝기 교차 배치는 스크립트로 합니다** (2026-09-12 추가):

```bash
.venv/bin/python scripts/reorder_by_brightness.py assets/images/<영문제목>
# 82장 재배치 · 밝기 중간값 128.2 (최소 17.2 / 최대 189.9)
# 밝기 30 미만 3장, 최대 연속 1장 (4.5초)
```

밝기 오름차순 → 밝은/어두운 절반 교차 → `mood_001..NNN` 재명명까지 한 번에 하고,
원본 파일명 매핑을 `image_order.json` 에 남깁니다. 출력의 **최대 연속**이 1~2장인지 확인하세요.
이미지를 나중에 빼면 연속이 다시 늘어나므로 **재실행**해야 합니다.

### ⚠️ 검수: 축소 몽타주는 글자를 못 잡습니다

4×5 그리드로 줄이면 인쇄 텍스트가 뭉개져 "낡은 종이"로만 보입니다. 2026-09-08에
**스페인어 백과사전 페이지**가 AI 관련성 검증과 육안 몽타주 검수를 모두 통과해
렌더 후에야 발견됐습니다(5분 6초에 4.5초간 화면 가득).

→ 검수 시트와 별개로 **밝기 상위 컷만 큰 크기로 한 번 더** 보세요.

### ⚠️ NLM 소스: 저자 위키가 작품 위키보다 크면 초점이 작가론으로 쏠립니다

2026-09-12 「당신들의 천국」에서 작품·저자(ko)·저자(en) 3개로 돌렸더니 비디오가
**「거장 이청준의 문학 세계」** 작가론으로 나왔습니다(판소리·서편제·수상 내역이 큰 비중,
정작 작품은 연표 한 줄). ko 저자 위키가 8,000~10,000자로 작품 위키를 압도한 탓입니다.

→ **착수 전에 두 위키의 분량을 비교**하고, 저자 쪽이 크면 **ko 저자를 빼고 작품 소스를 2개로**
   만드세요. 작품 해설은 한국민족문화대백과(`encykorea.aks.ac.kr`)가 좋은 보강 소스입니다.
→ ⚠️ 재실행하면 `SKIP: 이미 존재`로 1차 산출물을 그대로 돌려줍니다.
   `input/{제목}_Part1_video_kr.mp4` 를 먼저 치워야 재생성됩니다.

### ⚠️ 썸네일 스타일은 프롬프트 **앞머리**에 써야 듣습니다

2026-09-13 「운영전」 썸네일이 애니메이션풍으로 나왔고, 9/15에 원인을 추적했습니다.

| 시도 | 결과 |
|---|---|
| 기본 프롬프트 뒤에 `Soft watercolor + fine ink pen style` | 애니메이션풍 |
| 거기에 `NOT anime, NOT manga, NOT digital cartoon` 추가 | **그대로 애니메이션풍** |
| 뒤쪽 서술을 긍정형으로 강화 | 반실사 디지털 페인팅 + 워터마크 「KEAR3」 |
| ★ **스타일을 프롬프트 맨 앞으로 이동** | **선묘 + 담채로 정착** |

- ⛔ **Flux 는 부정어를 무시합니다** — 글자를 `NO text` 로 못 막는 것과 같습니다(`NO watermark` 도 무시돼 워터마크가 생겼습니다)
- ★ `_build_flux_prompt()` 는 이제 **스타일 → 피사체 → 레이아웃** 순으로 조립합니다
- ⛔ `Blue geometric accent lines` 지시도 제거했습니다 — 스타일을 앞으로 옮기자 화면에 **큰 파란 삼각형**으로 그려졌습니다. 기존 편들에선 거의 반영되지 않던 장식이라 잃는 것이 없습니다

### ⚠️ 제목이 실재 지명·역명과 겹치면 수요 지표가 통째로 오염됩니다

2026-09-12 「사평역」(임철우)은 수요 3,670회/월로 후보 상위였지만, 착수 직전 검색어를 쪼개
다시 재니 **「사평역 소설」이 월 55회**였습니다. ko 위키 「사평역」은 **서울 지하철 9호선 역**
문서이고, 3,670의 대부분이 지하철 검색이었습니다. 유튜브 자동완성은 문학으로 보였지만
네이버 절대 검색수는 다른 시장을 세고 있었습니다.

```bash
# 의도를 못박은 키워드를 함께 재서 비율을 본다
.venv/bin/python scripts/measure_search_demand.py --provider naver \
  --titles "사평역" "사평역 소설" "임철우"
```

→ 제목이 **지명·역명·일반명사**이면 착수 전에 반드시 이 교차 측정을 하세요.

### ⛔ 원격 렌더 감시에 `pgrep` 을 쓰지 마세요

`pgrep -f "10_create_video_with_summary"` 는 **그 문자열을 담은 SSH 명령줄 자신**을 매칭합니다.
2026-09-12에 두 번 오판했습니다(끝난 렌더를 진행 중으로, 시작 전 렌더를 실행 중으로).

```bash
# 완료 판정 — 로그의 완료 문자열
ssh GPU 'grep -aq "요약 포함 영상 제작 완료" ~/booksummary_render/render_X.log'
# 실행 여부 — 내 명령줄에 없는 문자열로
ssh GPU 'ps -eo cmd | grep -c "^/home/jsong/render_venv/bin/python"'
```

**시대·지역이 특정된 작품은 무료 스톡으로 채울 수 없습니다.** 2026-09-12 「원미동 사람들」
(1980년대 한국 변두리)에서는 AI 검증을 통과한 80장 중 **38장이 유럽·베트남·중국·제품컷**이라
육안 검수에서 버렸습니다. 1920년대 조선을 다룬 「만세전」도 같았습니다.

→ 처방은 **실사 + Flux 생성 혼합**입니다(원미동 = 실사 42 + Flux 40).
   Flux 배치 생성은 `scripts/gen_flux_wonmidong.py` 를 템플릿으로 복제해 쓰고,
   **저장 파일명은 반드시 `mood_*.jpg`**, 프롬프트는 시대·팔레트를 고정합니다.
   ⛔ 간판·표지판·신문처럼 **글자를 부르는 소재는 장면에서 빼세요** — 부정 프롬프트로는 못 막습니다
   (원미동에서도 가게·표지판을 그린 6장에 깨진 글자가 나와 폐기했습니다).

### 📁 3단계: 결과 확인

생성된 파일들은 `output/` 폴더에 저장됩니다:

- **영상**: `output/{표준제목}_{kr/en}.mp4`
- **메타데이터**: `output/{표준제목}_{kr/en}.metadata.json`
- **썸네일**: `output/{표준제목}_{kr/en}_thumbnail_{ko/en}.jpg`
  - ⚠️ **영상 파일 stem 과 반드시 일치해야 합니다.** 업로드 스크립트가 이 이름만 찾습니다.
    한글 제목으로 저장하면 찾지 못하고 무드 이미지가 대신 올라갑니다 (2026-09-19 실측)

### ⚠️ 썸네일은 반드시 텍스트 합성까지 하세요

**Flux 로 배경만 만들고 끝내면 훅·제목·저자가 없는 반쪽 썸네일이 올라갑니다.**
2026-09-08에 새 선정 기준 8편(만세전~니코마코스)이 전부 이 상태로 공개돼 있는 것을 발견했습니다.
유입의 70%가 검색인 채널에서 클릭을 가르는 것이 썸네일 텍스트입니다.

```bash
# 배경 생성 + 텍스트 합성 일괄 (이 경로를 쓰세요)
FLUX_SERVER_URL=http://192.168.0.150:9010 .venv/bin/python src/utils/thumbnail_generator.py \
  --title-ko "책 제목" --title-en "English Title" \
  --author-ko "저자" --author-en "Author" \
  --hook-ko "궁금증을 유발하는 한 줄" --hook-en "One-line hook" \
  --image-prompt-ko "Painted illustration, ..." --image-prompt-en "Painted illustration, ..."
```

- 이미 배경 이미지가 있으면 `overlay_text()` 만 호출해 텍스트를 얹을 수 있습니다(재생성 불필요)
- ⚠️ **Flux 포트는 매번 `/health` 의 `model`·`loaded` 필드로 확인**하세요.
  2026-09-08 기준 **9010** 이 정상이고, 9002 는 파이프라인이 cpu/cuda 로 쪼개져 500 을 냅니다
- ★ **업로드 후 썸네일을 실제로 받아서 눈으로 보세요.** API 응답에 `maxres` 키가 있어도
  그것은 "커스텀이 있다"는 뜻일 뿐 "제대로 됐다"는 뜻이 아닙니다

### 🗓 예약 슬롯 사이에 새 편 끼워 넣기

근접 슬롯에 새 편을 넣고 그 이후 예약을 전부 뒤로 미는 방식입니다.
날짜 충돌을 피하려 **뒤에서부터** 밉니다.

```bash
# 미리보기
.venv/bin/python scripts/shift_schedule.py --from 2026-10-02 --days 3
# 실제 적용 (새로 넣은 편은 --exclude 로 제외)
.venv/bin/python scripts/shift_schedule.py --from 2026-10-02 --days 3 --exclude <새영상ID> --apply
```

### 📤 4단계: YouTube 업로드 (선택사항)

영상이 준비되었으면 YouTube에 업로드할 수 있습니다:

```bash
python src/09_upload_from_metadata.py --privacy private --auto
```

이 명령어는:
- `output/` 폴더의 모든 `.metadata.json` 파일을 찾아서
- 각각의 영상을 YouTube에 업로드합니다
- 태그 자동 검증 (30자 초과 태그 제거)
- 썸네일 자동 업로드
- 업로드 로그 자동 저장

**특정 영상만 업로드하고 싶다면(추천):**

`--metadata-files` 옵션으로 업로드 대상을 제한할 수 있습니다.

```bash
python src/09_upload_from_metadata.py \
  --privacy private \
  --auto \
  --metadata-files \
  "output/Some_Book_kr.metadata.json" \
  "output/Some_Book_en.metadata.json"
```

### 💡 처음 사용 시 팁

1. **테스트는 하나씩**: 처음에는 `--language both` 대신 `--language ko` 또는 `--language en`으로 하나씩 테스트하는 것을 권장합니다
2. **이미지 다운로드**: 기존 이미지가 100개 이상이면 자동으로 건너뛰어 시간을 절약합니다
3. **Summary 파일**: 미리 준비하면 더 정확한 요약을 얻을 수 있지만, 없어도 AI가 자동으로 생성합니다
4. **NotebookLM 비디오**: 없어도 영상은 생성되지만, 있으면 더 풍부한 콘텐츠가 됩니다
5. **업로드 전 확인**: 업로드하기 전에 생성된 영상과 메타데이터를 확인하는 것을 권장합니다
6. **번역 매핑**: 새로운 책을 추가할 때 한글/영문 제목과 저자 이름 매핑이 필요합니다. `src/utils/translations.py` 파일에 매핑을 추가하세요.

### 🤖 Cursor(에이전트)로 영상 생성 요청하기

이 프로젝트는 Cursor에서 “한글로 요청”하면, 에이전트가 `input/` 확인 → 파일 정리/다운로드/생성/업로드까지 자동으로 실행할 수 있습니다.  
**제목이 어색하게 섞이거나(한글+영문 혼합) 업로드 대상이 엉키는 문제를 줄이려면 아래 정보를 함께 주세요.**

#### 공통으로 꼭 알려주세요 (필수)
- **스타일**: `summary+video` 또는 `일당백(full_episode)`
- **생성 언어**: `ko`, `en`, `both(한글+영문)`
- **책 제목(한글)**: 따옴표 포함 원문 그대로 (부제/괄호 포함 여부도 함께)
- **저자**
  - 단일 저자: 한글 이름
  - 선집/단편집 등 복수 저자: `여러 명`/`Various Authors`처럼 명시 (또는 저자 생략 요청)

#### 영문 제목 품질을 안정적으로 만들고 싶다면 (권장)
- **영문 원제(공식 표기)**: 제목 번역 매핑이 없는 경우 영문 템플릿에 한글이 섞일 수 있어 권장
- **저자 영문 표기(로마자/공식 표기)**: 예) `Arthur Schopenhauer`

> 💡 **원제/저자 영문을 주기 어렵다면**  
> “이 책 제목/저자 번역 매핑을 `src/utils/translations.py`에 추가해줘”라고 함께 요청하면 됩니다.

#### 제목 스타일을 명확히 하고 싶다면 (권장)
아래 중 하나로 지정해 주세요.
- **고정 포맷(권장)**:
  - `summary+video`: `[핵심 요약] 책제목: 작가 (부제목)`
  - `일당백(full_episode)`: `[일당백] 책제목: 작가 (부제목)`
  - 영문(English) 제목은 완전 영어만 허용:
    - `summary+video (en)`: `[Summary] Book Title: Author (Subtitle)`
    - `일당백(full_episode) (en)`: `[1DANG100] Book Title: Author (Subtitle)`
  - 참고: 영문에서는 한국어 혼입을 막기 위해 **영문 부제목만** 자동 반영되며, 저자/원제 매핑이 없으면 에러로 막습니다.
  - 참고: `(부제목)`은 SEO를 위해 자동 생성될 수 있습니다.
    - ko: `(원래 부제목이 있으면 그 부제목 · SEO 키워드)` / `(원래 부제목이 없으면 SEO 키워드)` 형태
      - `summary+video`: `5분 핵심 요약·AI 심층 분석 · (장르/키워드)`
      - `일당백(full_episode)`: `배경지식·인포그래픽·책 분석`
    - en: `(SEO keywords)` 형태 (완전 영어만 허용)
      - `summary+video`: `5-min Summary · AI Deep Dive · (genre keywords)`
      - `일당백(full_episode)`: `Background · Infographics · Analysis`
  - 참고: YouTube 제목은 **항상 100자 이내**여야 합니다.
    - 길이가 초과되면 `(부제목)`을 우선 **오른쪽부터 단계적으로 줄여서** 100자 이내로 맞춥니다.
- **제목 직접 지정(가장 확실)**: “한글 제목=…, 영문 제목=… 으로 고정”

#### 요청 템플릿 (복붙용)

**1) Summary+Video 생성 요청**

```text
[요청] summary+video 스타일 한글/영문 영상 생성
- 책 제목(한글): "..."
- 영문 원제(권장): "..."
- 저자(한글): "..."
- 저자(영문, 권장): "..."
- input prefix(있다면): "..."  (예: abc_summary_kr.md 같은 파일의 abc)
- 제목 스타일: 가치/후킹형 | 고정 포맷 | 직접 지정
- 업로드: 하지 말고 생성만 / 비공개로 업로드 / 일부공개로 업로드 / 공개로 업로드
```

**2) 일당백(full_episode) 생성 요청**

```text
[요청] 일당백(full_episode) 스타일 한글/영문 영상 생성
- 책 제목(한글): "..."
- 영문 원제(권장): "..."
- 저자: 단일/복수 여부(예: 여러 명)
- input 준비: part1/part2 비디오+인포그래픽(ko/en) + thumbnail_kr.png, thumbnail_en.png
- 업로드: 하지 말고 생성만 / 비공개로 업로드 / 일부공개로 업로드 / 공개로 업로드
```

#### 업로드 관련 주의사항 (중요)
- **업로드는 반드시 “업로드해줘(privacy 포함)”처럼 명시적으로 요청할 때만** 진행하는 것을 권장합니다.
- 재업로드가 필요하면 “강제 업로드(재업로드)”라고 요청해 주세요. (`--force` 사용)

## 일당백 에피소드 제작 워크플로우

일당백 채널의 유튜브 영상을 기반으로 NotebookLM에서 영상과 인포그래픽을 생성하여 하나의 긴 에피소드 영상으로 합치는 워크플로우입니다.

### 전체 워크플로우 순서

1. **자막 추출** (가장 먼저 실행)
   - 유튜브 영상 2개(Part 1, Part 2)에서 자막을 추출하여 텍스트 파일로 저장
   - Part 1: 작가와 배경 정보
   - Part 2: 소설 줄거리

2. **NotebookLM에서 수동 작업**
   - 추출한 자막 텍스트를 NotebookLM에 업로드
   - NotebookLM에서 Part 1, Part 2 각각에 대해:
     - 비디오 생성 (`part1_video.mp4`, `part2_video.mp4`)
     - 인포그래픽 생성 (`part1_info.png`, `part2_info.png`)

3. **파일 준비 및 영상 합성**
   - 생성한 4개 파일을 `input/` 폴더에 넣기
   - `run_episode_maker.py` 실행하여 자동으로 파일 정리 및 영상 합성

### 1단계: 자막 추출

유튜브 영상에서 자막을 추출하여 NotebookLM용 텍스트 파일을 생성합니다.

**2개 영상 (Part 1, Part 2):**
```bash
python scripts/fetch_separate_scripts.py \
  --url1 "https://www.youtube.com/watch?v=VIDEO_ID_1" \
  --url2 "https://www.youtube.com/watch?v=VIDEO_ID_2" \
  --title "책제목" \
  --cookies "scripts/cookies.txt"
```

**여러 영상 (3개 이상):**
```bash
python scripts/fetch_separate_scripts.py \
  --urls "https://www.youtube.com/watch?v=VIDEO_ID_1" \
         "https://www.youtube.com/watch?v=VIDEO_ID_2" \
         "https://www.youtube.com/watch?v=VIDEO_ID_3" \
  --title "책제목" \
  --cookies "scripts/cookies.txt"
```

**IP 차단 우회 (자동 폴백):**
- `scripts/cookies.txt` 쿠키 파일이 있으면 자동 사용
- `youtube-transcript-api` 실패 시 `yt-dlp`로 자동 폴백 (쿠키 자동 전달)
- Part 간 3초 딜레이로 rate limiting 자동 적용

**쿠키 파일 준비:**
1. 크롬 확장프로그램 "Get cookies.txt LOCALLY" 설치
2. YouTube에 로그인한 상태에서 쿠키를 `cookies.txt`로 다운로드
3. `scripts/` 폴더에 `cookies.txt` 저장

**생성되는 파일:**
- `data/source/{책제목}_part1_author.txt` - Part 1 자막 (작가와 배경)
- `data/source/{책제목}_part2_novel.txt` - Part 2 자막 (소설 줄거리)
- `data/source/{책제목}_part3.txt` - Part 3 자막 (3개 이상인 경우)

### 2단계: NotebookLM에서 수동 작업

1. **자막 텍스트 업로드**
   - 생성된 `part1_author.txt`와 `part2_novel.txt` 파일을 각각 NotebookLM에 업로드

2. **Part 1 비디오 및 인포그래픽 생성**
   - NotebookLM에서 Part 1 소스로 비디오 생성 → `part1_video.mp4`로 다운로드
   - NotebookLM에서 Part 1 소스로 인포그래픽 생성 → `part1_info.png`로 다운로드

3. **Part 2 비디오 및 인포그래픽 생성**
   - NotebookLM에서 Part 2 소스로 비디오 생성 → `part2_video.mp4`로 다운로드
   - NotebookLM에서 Part 2 소스로 인포그래픽 생성 → `part2_info.png`로 다운로드

### 3단계: 파일 준비 및 영상 합성

생성한 파일들을 `input/` 폴더에 넣고 자동화 스크립트를 실행합니다.

```bash
# 1. input 폴더에 파일 준비 (Part 2개 이상, Part 3개 이상도 자동 지원)
input/
├── part1_video.mp4    # 또는 다른 이름 (자동 인식)
├── part1_info.png     # 또는 다른 이름 (자동 인식)
├── part2_video.mp4    # 또는 다른 이름 (자동 인식)
├── part2_info.png     # 또는 다른 이름 (자동 인식)
├── part3_video.mp4    # Part 3 이상도 자동 지원 (선택사항)
└── part3_info.png     # Part 3 이상도 자동 지원 (선택사항)

# 2. 자동화 스크립트 실행
python run_episode_maker.py
```

**스크립트 실행 과정:**

1. **책 제목 입력**
   ```
   📖 작업할 책 제목(영문)을 입력하세요: The_Old_Man_and_the_Sea
   ```

2. **파일 자동 정리 및 이동**
   - `input/` 폴더에서 모든 파일 자동 검색 및 언어별/파트별 분류
   - 파일명 자동 정규화 (part1/part2/part3... 구분)
   - `assets/notebooklm/{책제목}/` 폴더로 자동 이동
   - 파일명 정규화: `part1_video.mp4`, `part1_info.png` 등

3. **자막 추출 (선택사항)**
   - 새로운 자막 추출이 필요한 경우에만 실행
   - 필요 없으면 'n' 입력하여 건너뛰기

4. **파일 준비 확인**
   - 필수 파일(Part 1 영상/인포그래픽) 존재 여부 자동 확인
   - Part 2 이상도 자동으로 탐지하여 모두 포함

5. **영상 합성 및 메타데이터 생성**
   - `src/create_full_episode.py` 자동 실행
   - **동적 Part 감지**: 실시간으로 존재하는 Part 개수를 파악하여 합성
   - **장르 자동 감지**: 책 제목이나 정보를 바탕으로 "소설", "시", "수필" 등 장르 자동 판별
   - 최종 영상 생성: `output/{책제목}_full_episode_{언어}.mp4`
   - 메타데이터 생성: `output/{책제목}_full_episode_{언어}.metadata.json` (타임스탬프 자동 포함)

**생성되는 영상 구조:**
- Part 1 영상 → Part 1 인포그래픽 → Part 2 영상 → Part 2 인포그래픽 → ... (모든 Part 자동 연결)
- 모든 클립 사이에 **1.5초 Crossfade** 및 페이드 인/아웃 효과 적용
- 인포그래픽에는 배경음악 자동 추가 및 표시 시간 최적화 (기본 30초)
- 자막 가독성 향상: 폰트 크기 증대(70px), 테두리 강조, 반투명 배경 박스 적용

### 파일명 자동 인식

`input/` 폴더에 파일명이 정확하지 않아도 자동으로 인식합니다:
- `mp4` 파일과 `png` 파일만 있으면 자동으로 part1/part2/part3... 구분
- 파일명에 'part1', 'part2', 'part3' 또는 '1', '2', '3'이 포함되어 있으면 자동 매칭
- 예: `video1.mp4`, `info1.png`, `video2.mp4`, `info2.png`, `video3.mp4`, `info3.png` → 자동 인식
- **Part 3개 이상도 자동 지원**: Part 번호를 증가시키면서 자동으로 모든 Part를 찾아서 연결

### 배경음악 자동 처리

- 배경음악 파일이 없으면 자동으로 탐지 및 다운로드:
  1. `input/` 폴더에서 `background*.mp3`, `bgm*.mp3`, `music*.mp3` 등 검색
  2. `assets/music/` 폴더에서 배경음악 파일 검색
  3. 없으면 Pixabay Music에서 책 분위기에 맞는 배경음악 자동 다운로드
- 인포그래픽 클립에만 배경음악 자동 추가 (영상 클립에는 추가하지 않음)
- 배경음악은 인포그래픽 길이에 맞춰 자동 조정 (반복 또는 자르기)

### 전체 예시

```bash
# 1. 자막 추출
python scripts/fetch_separate_scripts.py \
  --url1 "https://www.youtube.com/watch?v=abc123" \
  --url2 "https://www.youtube.com/watch?v=def456" \
  --title "The_Old_Man_and_the_Sea"

# 2. NotebookLM에서 수동으로 비디오와 인포그래픽 생성
# (part1_video.mp4, part1_info.png, part2_video.mp4, part2_info.png)

# 3. input 폴더에 파일 넣기
cp part1_video.mp4 input/
cp part1_info.png input/
cp part2_video.mp4 input/
cp part2_info.png input/

# 4. 자동화 스크립트 실행
python run_episode_maker.py
# → 책 제목 입력: The_Old_Man_and_the_Sea
# → 자막 추출 필요 여부: n (이미 완료했으므로)
# → 자동으로 파일 정리 및 영상 합성 완료
```

## 사용 방법

### 방법 1: input 폴더에서 자동 준비 (권장)

**가장 간편한 방법입니다.** 프로젝트 루트의 `input/` 폴더에 파일을 준비하고 한 번에 처리합니다.

1. **input 폴더에 파일 준비:**
   - `{prefix}_summary_en.md` / `{prefix}_summary_kr.md` - 요약 텍스트 (선택사항)
   - `{prefix}_thumbnail_en.png` / `{prefix}_thumbnail_kr.png` - 썸네일 원본
   - `{prefix}_video_en.mp4` / `{prefix}_video_kr.mp4` - NotebookLM 비디오 (선택사항)

1. **전체 파이프라인 실행:**

```bash
python scripts/run_full_pipeline_from_downloads.py \
  --book-title "책 제목" \
  --author "저자 이름" \
  --prefix "파일명접두사" \
  --language both
```

   예시:

```bash
python scripts/run_full_pipeline_from_downloads.py \
  --book-title "The Loneliness of Sonia and Sunny (소니아와 써니의 고독)" \
  --author "키란 데사이" \
  --prefix "lonliness" \
  --language both
```

1. **파일만 준비하고 싶은 경우:**

```bash
python scripts/prepare_files_from_downloads.py \
  --book-title "책 제목" \
  --author "저자 이름" \
  --prefix "파일명접두사"
```

**NotebookLM 비디오 업데이트:**

input 폴더에 새로운 NotebookLM 비디오 파일을 올리고 기존 비디오를 교체한 후 영상을 재생성할 수 있습니다.

```bash
python scripts/update_notebooklm_video.py \
  --book-title "책 제목" \
  --prefix "파일명접두사" \
  --language ko
```

이 스크립트는:

1. input 폴더에서 새 비디오 파일을 찾습니다 (`{prefix}_video_kr.mp4` 또는 `{prefix}_video_ko.mp4` 또는 `{prefix}_video.kr.mp4` 형식)
2. 기존 비디오 파일을 백업합니다 (`.backup` 확장자)
3. 새 파일로 교체합니다
4. 해당 언어의 영상을 자동으로 재생성합니다

### 방법 2: 수동으로 파일 준비

**비디오 파일 (선택사항):**
NotebookLM에서 생성한 비디오 파일을 `assets/video/` 폴더에 위치시킵니다.

**파일명 규칙 (표준 네이밍):**

- 한글 비디오: `{책제목}_notebooklm_ko.{확장자}` (예: `Sunrise_on_the_Reaping_notebooklm_ko.mp4`)
- 영어 비디오: `{영문제목}_notebooklm_en.{확장자}` (예: `Sunrise_on_the_Reaping_notebooklm_en.mp4`)
- 지원 확장자: `.mp4`, `.mov`, `.avi`, `.mkv`

**Summary 파일 (선택사항):**

요약 텍스트 파일을 `assets/summaries/` 폴더에 위치시킵니다.

- 한글: `{책제목}_summary_ko.md`
- 영어: `{책제목}_summary_en.md`

**Summary 파일 메타데이터 주석 처리:**

Summary 파일 생성 시 메타데이터(책 제목, 저자, 설명 라인)는 자동으로 HTML 주석(`<!-- -->`)으로 처리됩니다. TTS 생성 시 이 메타데이터는 자동으로 필터링되어 음성으로 변환되지 않습니다.

**자동 생성되는 형식:**
```markdown
<!-- 📘 노인과 바다 -->
<!-- 어니스트 헤밍웨이 -->
<!-- TTS 기준 약 5분 서머리 스크립트 (Korean) -->

[HOOK – 도입]
...
```

**영문 형식:**
```markdown
<!-- 📘 The Old Man and the Sea -->
<!-- Ernest Hemingway -->
<!-- TTS 기준 about 5 minutes summary script (English) -->

[HOOK – Introduction]
...
```

**썸네일 파일:**

PNG 파일을 `output/` 폴더에 위치시키고 JPG로 변환합니다.

- 한글: `{표준제목}_kr_thumbnail_ko.jpg` (예: `Aunt_Suni_kr_thumbnail_ko.jpg`)
- 영어: `{표준제목}_en_thumbnail_en.jpg`

**참고:** Summary 오디오는 자동으로 생성되며 `{책제목}_summary_{언어}.mp3` 형식으로 저장됩니다.

### 2. 전체 파이프라인 실행

다음 명령어로 2~6단계 과정을 한 번에 실행할 수 있습니다.

```bash
./run_complete_pipeline.sh "책 제목" "저자 이름"
```

예시:

```bash
./run_complete_pipeline.sh "The Boy is Coming" "Han Kang"
```

### 개별 단계 실행 (고급 사용자용)

**이미지 다운로드:**

```bash
./run_images.sh --title "책 제목" --author "저자 이름"
```

**요약 생성 및 영상 제작:**

```bash
python src/10_create_video_with_summary.py \
  --book-title "책 제목" \
  --author "저자 이름" \
  --language ko \
  --summary-duration 5.0 \
  --summary-audio-volume 1.2
```

**메타데이터만 생성 (영상이 이미 있는 경우):**

```bash
python src/08_create_and_preview_videos.py \
  --book-title "책 제목" \
  --metadata-only
```

메타데이터 생성 시:

- 썸네일 경로를 자동으로 찾아서 포함합니다
- **장르 자동 감지**: 책의 장르(소설, 시, 수필, 논픽션 등)를 자동으로 감지하여 적절한 용어 사용
  - `book_info.json`의 `categories` 필드 또는 책 제목에서 키워드 분석
  - 장르별 용어: 소설→"소설"/"Novel", 시→"시"/"Poetry", 수필→"수필"/"Essay", 기타→"작품"/"Work"
  - 제목, 설명, 타임스탬프, 해시태그 등 모든 메타데이터에 자동 적용
- **YouTube timestamp 자동 생성**: Summary, NotebookLM Video 섹션의 시작 시간을 자동으로 계산하여 Video Chapters에 포함합니다
  - 예: `0:00 - Summary`, `1:27 - NotebookLM Detailed Analysis`

**파일 네이밍 규칙 요약:**

- **Summary 오디오**: `assets/audio/{책제목}_summary_{언어}.mp3` (자동 생성)
- **NotebookLM 비디오**: `assets/video/{책제목}_notebooklm_{언어}.{확장자}` (선택사항)
- **생성된 영상**: `output/{책제목}_review_with_summary_{언어}.mp4`
- **썸네일**: `output/{표준제목}_{kr/en}_thumbnail_{ko/en}.jpg`
  - ⚠️ **영상 파일 stem 과 반드시 일치해야 합니다.** 업로드 스크립트가 이 이름만 찾습니다.
    한글 제목으로 저장하면 찾지 못하고 무드 이미지가 대신 올라갑니다 (2026-09-19 실측)
- **메타데이터**: `output/{책제목}_review_with_summary_{언어}.metadata.json` (timestamp 자동 포함)

**영상 구성:**

- **Summary** (이미지 슬라이드쇼 + 요약 오디오, 음량 1.2배 조정, **자막 자동 추가**)
- **2초 silence** (검은 화면)
- **NotebookLM Video** (선택사항, 있으면 자동 포함)

**YouTube 챕터 마커 자동 생성:**

- 영상 description의 맨 앞에 YouTube 챕터 마커가 자동으로 추가됩니다
- 형식: `0:00 Chapter Title` (YouTube가 자동으로 인식)
- 챕터 구성:
  - `0:00 Summary` (요약 섹션)
  - `{timestamp} NotebookLM Detailed Analysis` (NotebookLM 비디오가 있는 경우)
- 메타데이터 생성 시 timestamp 정보가 있으면 자동으로 챕터 마커가 생성됩니다

**Summary 자막 기능:**

- **언어별 자동 설정**:
  - **영어 (`en`)**: 자막 자동 추가 (기본값)
  - **한글 (`ko`)**: 자막 없음 (기본값)
- **Whisper 단어 단위 타이밍**: 실제 오디오 파일을 Whisper로 분석하여 정확한 단어 단위 타임스탬프 사용
- Summary 텍스트를 문장 단위로 분할하여 오디오 타이밍에 맞춰 자막 표시
- 자막 스타일:
  - 흰색 텍스트, 검은색 테두리 (가독성 향상)
  - 화면 하단 중앙 위치
  - 폰트 크기: 60px
- **수동 제어 옵션**:
  - `--no-subtitles`: 자막 강제 비활성화 (언어 기본값 무시)
  - `--subtitles`: 자막 강제 활성화 (언어 기본값 무시)
  ```bash
  # 영어: 자막 자동 추가 (기본값)
  python src/10_create_video_with_summary.py \
    --book-title "책 제목" \
    --author "저자 이름" \
    --language en
  
  # 한글: 자막 없음 (기본값)
  python src/10_create_video_with_summary.py \
    --book-title "책 제목" \
    --author "저자 이름" \
    --language ko
  
  # 수동 제어: 한글에도 자막 추가
  python src/10_create_video_with_summary.py \
    --book-title "책 제목" \
    --author "저자 이름" \
    --language ko \
    --subtitles
  ```

**Summary 오디오 음량 조정:**

- 기본값: 1.2배 (20% 증가)
- 조정 가능: `--summary-audio-volume 1.5` (50% 증가) 또는 `--summary-audio-volume 1.0` (원본)

**유튜브 업로드:**

```bash
python src/09_upload_from_metadata.py --privacy private --auto
```

**강제 업로드 (재업로드):**
이미 업로드된 영상이라도 강제로 다시 업로드하려면 `--force` 옵션을 사용하세요:
```bash
python src/09_upload_from_metadata.py --privacy private --auto --force
```

**채널 선택:**
- 기본값: book summary 채널 (`UCxOcO_x_yW6sfg_FPUQVqYA`)
- 다른 채널로 업로드: `--channel-id UCxxxxxxxxxxxxxxxxxxxxxxxxxx`
- 또는 환경 변수: `YOUTUBE_CHANNEL_ID=UCxxxxxxxxxxxxxxxxxxxxxxxxxx`

- **OAuth refresh token 생성**:
  - `secrets/client_secret.json` 파일이 필요합니다.
  - `scripts/get_youtube_refresh_token.py` 스크립트를 사용하여 새 refresh token 생성:
    ```bash
    python scripts/get_youtube_refresh_token.py
    ```
  - OAuth 인증 화면에서 원하는 채널을 선택하세요.
  - 생성된 refresh token을 `.env` 파일의 `YOUTUBE_REFRESH_TOKEN`에 설정하세요.

업로드 시:
- **제목 자동 축약**: YouTube 100자 제한을 초과하는 제목을 자동으로 축약 (97자 + "...")
- 태그 자동 검증 (30자 초과 태그 제거)
- Description 길이 검증 (5000자 제한)
- **썸네일 자동 검색 및 업로드**: 한글/영문 제목 양방향 검색 지원
  - 메타데이터의 `book_title`이 영문이면 한글 번역도 자동 검색
  - 한글이면 영문 번역도 자동 검색
  - 다양한 파일명 패턴 지원 (`{책제목}_thumbnail_{언어}.jpg`, `{책제목}_{언어}_thumbnail.jpg` 등)
  - 한글 파일명 직접 검색 및 유사도 매칭 지원
- 업로드 로그 자동 저장 (JSON, CSV, 텍스트)
- CSV 및 History 파일 자동 업데이트

## 프로젝트 구조

```text
├── secrets/            # 민감한 인증 정보 (Git 무시)
│   ├── client_secret.json
│   ├── credentials.json
│   └── google-cloud-tts-key.json
├── docs/               # 문서
│   └── SUMMARY_TEMPLATE.md  # 유튜브 롱폼 영상용 요약 템플릿 (Hook → Summary → Bridge)
├── output/             # 생성된 영상 및 썸네일
├── scripts/            # 유틸리티 스크립트
│   ├── prepare_files_from_downloads.py  # input 폴더에서 파일 준비 및 표준 네이밍
│   ├── run_full_pipeline_from_downloads.py  # input 폴더 기반 전체 파이프라인 실행
│   ├── update_notebooklm_video.py  # NotebookLM 비디오 업데이트 및 영상 재생성
│   ├── convert_downloads_png.py    # input 폴더 PNG를 JPG 썸네일로 변환
│   ├── convert_png_to_jpg.py       # PNG를 JPG로 변환
│   ├── download_pexels_images.py  # Pexels API 이미지 다운로드 테스트
│   ├── generate_summary_audio.py   # Summary 오디오 생성
│   ├── get_youtube_refresh_token.py  # YouTube OAuth2 refresh token 생성
│   └── ...
├── src/                # 소스 코드
│   ├── 08_generate_summary.py      # 요약 텍스트 생성 (Hook → Summary → Bridge 구조)
│   ├── 09_text_to_speech_multi.py  # 다중 엔진 TTS 변환
│   ├── 10_create_video_with_summary.py  # 영상 합성 (요약+리뷰)
│   ├── 24_batch_update_affiliate_links.py  # 기존 영상 제휴 링크 일괄 업데이트
│   ├── 25_batch_add_pinned_comments.py  # 기존 영상 고정 댓글 일괄 추가
│   ├── 28_fix_video_language_tags.py  # 영상 오디오 언어 정정 및 소실 태그 복구
│   └── ...
└── README.md           # 이 파일
```

## 요약 템플릿

유튜브 롱폼 영상용 5분 분량 오프닝 서머리는 다음 구조로 생성됩니다:

- **[HOOK]**: 강력한 첫 문장 (3초 만에 시청자 몰입)
- **[SUMMARY]**: 5분 분량 핵심 요약 (주제, 주요 아이디어, 예시/일화)
- **[BRIDGE]**: NotebookLM 상세 분석으로 자연스럽게 연결

자세한 템플릿 가이드는 `docs/SUMMARY_TEMPLATE.md`를 참고하세요.

## 주요 기능

### 시청자 유입 및 채널 성장 기능 (Phase 11)

- **YouTube Shorts 자동 생성** (`src/26_generate_shorts.py`): 9:16 세로 포맷(1080x1920), 최대 59초
  - Short 1: HOOK 섹션 기반 (~30초), Short 2: 핵심 인용구 (~45초), Short 3: 한 줄 요약 (~20초)
  - `#Shorts` 해시태그 포함 메타데이터 자동 생성
  ```bash
  python src/26_generate_shorts.py --book-title "책 제목" --language ko
  ```
- **플레이리스트 자동 관리** (`src/27_manage_playlists.py`): 7개 장르별 자동 분류 및 배치
  ```bash
  python src/27_manage_playlists.py --apply         # 채널 전체 영상 정리
  python src/27_manage_playlists.py --video-id VIDEO_ID --apply  # 단일 영상 추가
  ```
- **커뮤니티 탭 자동 포스팅** (`src/28_community_posts.py`): 주간 3회 자동화
  - 월요일: 책 인용구 포스트, 수요일: 다음 리뷰 투표, 금요일: 채널 근황
  ```bash
  python src/28_community_posts.py --book-title "책 제목" --apply
  ```
- **장르 기반 동적 해시태그**: 8개 장르(철학, 심리, 비즈니스, 역사, 과학, 시, 에세이, 소설)별 최적 해시태그 자동 생성
- **Ken Burns 효과 기본 활성화**: zoom_in/zoom_out 교대 + 패닝으로 이미지 시퀀스 동적 구성
- **Summary 기본 길이 6분**: 미드롤 광고 활성화 (총 영상 8-10분 목표)

### 영상 시각화·제목·고정 댓글
- **동적 자막(Kinetic Typography)**: 키워드 추출 + Whisper 타이밍, 팝 효과
- **파형(Waveform) 시각화**: 오디오 스펙트럼 하단 시각화 (실시간 스크롤)
- **Pexels 푸티지**: 키워드 기반 관련 영상 검색·다운로드 (`PEXELS_API_KEY` 설정 시)
- **제목 전략**: AI 언급 대신 가치·인간적 호기심 강조 (`src/utils/title_generator.py`)
- **고정 댓글**: 챕터 타임스탬프 + 참여 유도 질문 + 구독/좋아요 CTA 자동 생성 (고정은 YouTube UI에서 수동)

### 제휴 링크 자동 삽입
- **Amazon Associates 제휴 링크**: 영상 description에 자동으로 Amazon 구매 링크 삽입
  - `.env`에 `AMAZON_ASSOCIATE_TAG` 설정 시 자동 활성화 (예: `joohans-20`)
  - 한글 영상: Amazon 링크 포함
  - 영문 영상: Amazon 링크 포함
  - 알라딘(`ALADIN_PARTNER_ID`), Yes24(`YES24_PARTNER_ID`) 제휴도 지원 (선택사항)
  - **개선**: 작가명을 검색어에서 제외하여 검색 정확도 향상 (제목만 사용)
- **기존 영상 일괄 업데이트**: `src/24_batch_update_affiliate_links.py`로 채널의 기존 영상에도 제휴 링크 추가 가능
  ```bash
  # 미리보기
  python src/24_batch_update_affiliate_links.py --dry-run
  # 실제 적용 (50개 제한)
  python src/24_batch_update_affiliate_links.py --apply --limit 50
  ```
- **멱등성 보장**: 이미 제휴 링크가 있는 영상은 건너뜀

### 영상 언어·태그 일괄 정정

업로드 직후 `videos.update(part='snippet')` 호출이 snippet을 통째로 교체하면서 `tags`와
`defaultAudioLanguage`를 누락해, 태그가 삭제되고 오디오 언어가 en-US로 자동 설정되는 문제가 있었습니다.
업로드 스크립트는 수정되었고, 이미 올라간 영상은 아래 스크립트로 정정합니다.

- **정정 대상**: `defaultLanguage`와 어긋난 `defaultAudioLanguage`, 비어 있는 태그
- **태그 복구**: 로컬 `output/*.metadata.json`의 원본을 우선 사용하고, 없으면 영상 제목에서 책 제목을
  추출해 `generate_episode_tags()`로 재생성 (신규 업로드와 동일한 태그 체계)
  ```bash
  # 미리보기 (기본값)
  python src/28_fix_video_language_tags.py
  # 실제 적용 (쿼터 조절용 제한)
  python src/28_fix_video_language_tags.py --apply --limit 150
  # 언어만 정정하고 태그는 건드리지 않음
  python src/28_fix_video_language_tags.py --apply --lang-only
  ```
- **쿼터 주의**: `videos.update`는 1회당 50 유닛으로 일일 한도가 10,000입니다. 200개를 넘기면
  `--limit`으로 나눠 실행해야 하며, 쿼터 소진이 감지되면 스크립트가 자동 중단합니다.

### 일괄 고정 댓글 기능 (제휴 링크 포함)
- **고정 댓글 일괄 추가**: `src/25_batch_add_pinned_comments.py`로 채널의 모든 영상에 고정 댓글 자동 추가
  ```bash
  # 기본 실행 (모든 영상)
  python src/25_batch_add_pinned_comments.py

  # 기존 댓글 확인 및 업데이트
  python src/25_batch_add_pinned_comments.py --update-existing

  # 책 존재 여부 사전 검증 (Google Books API)
  python src/25_batch_add_pinned_comments.py --verify-books
  ```
- **고정 댓글 구성**:
  - 한글 영상: 알라딘 + Amazon 제휴 링크
  - 영문 영상: Amazon 제휴 링크만
  - 챕터 타임스탐프 (자동 감지)
  - 참여 유도 질문
- **주요 기능**:
  - `--update-existing`: 기존 댓글 업데이트 지원 (`update_comment()` 메서드)
  - `--verify-books`: Google Books API로 책 존재 여부 사전 검증 (`verify_book_title()` 메서드)
  - 댓글 비활성화 영상 자동 감지 및 스킵
  - 일괄 작업 결과 요약 출력

### 고해상도 썸네일 생성

- **4K 해상도 (3840x2160)** 지원으로 고품질 썸네일 생성
- 한국어/영어 폰트 자동 감지 및 최적화
- DALL-E 3를 활용한 AI 배경 이미지 생성 옵션

### 다중 TTS 엔진 지원

- **OpenAI TTS** (기본): `nova` 음성 사용, 한글/영어 모두 지원
- **Google Cloud TTS (Neural2)**: 빠른 처리 속도, 작은 파일 크기, 한글 완벽 지원
- **ElevenLabs Multilingual v2**: 감정 표현이 풍부한 음성 (API 키 필요)
- **Replicate xtts-v2**: 영어 전용 (한글 미지원)
- 다양한 음성 옵션 테스트 스크립트 제공 (`scripts/test_tts_providers.py`, `scripts/test_korean_tts.py`)

### 스마트 이미지 키워드 생성

- 책의 summary 파일을 분석하여 주제에 맞는 이미지 키워드 자동 생성
- AI 기반 키워드 추출로 더 정확한 무드 이미지 수집
- 다중 이미지 소스 지원: **Pexels (1순위) → Pixabay (2순위) → Unsplash (3순위)**
- 각 API의 장점을 활용하여 최대 100개의 고품질 무드 이미지 수집
- **기존 이미지 자동 감지**: 이미지가 100개 이상이면 다운로드를 건너뛰어 시간과 API 호출 절약

### 유튜브 채널에서 CSV 자동 업데이트

- 유튜브 채널에 업로드된 책 정보를 자동으로 CSV에 반영
- `python src/13_update_csv_from_youtube.py` 실행
- 비디오 제목과 책 제목 자동 매칭 (별칭 지원)

### 깊이 있는 URL 수집

- 유튜브 롱폼 북튜브를 위한 깊이 있는 자료 수집
- YouTube 영상(30분 이상), PDF, 논문, 학술 사이트 검색
- 특정 YouTube 채널 우선순위 검색 (일당백 최우선)
- `python src/14_collect_deep_urls_for_notebooklm.py --csv` 실행

### 스마트 태그 생성

- 책 정보 기반 자동 태그 생성
- 추천 기관 태그 자동 포함:
  - 세계적 미디어: 뉴욕타임즈, 아마존, 타임지, CNN, 뉴스위크
  - 주요 서점: 교보문고, 알라딘, YES24
  - 유명 대학: 서울대학교, 하버드대학교, 도쿄대학교 등
  - 문학상: 노벨문학상, 퓰리처상, 맨부커상 등
- YouTube 태그 제한(500자)을 고려한 우선순위 기반 선택
- **태그 자동 검증 및 포맷팅**: 
  - 업로드 시 30자 초과 태그 자동 제거 (YouTube 규칙 준수)
  - 태그 내 공백을 언더스코어(`_`)로 자동 변환 (예: "Das Kapital" → "Das_Kapital")

### YouTube 메타데이터 관리

- **가이드**: [YouTube 메타데이터 생성 가이드](docs/YOUTUBE_METADATA_GUIDE.md)를 참조하세요.
- **에피소드 스타일**: `src/20_create_episode_metadata.py`를 통한 동적 파트 감지 및 타임스탬프 생성.
- **글로벌 SEO**: 영문 메타데이터에서 한글 자동 제거 및 최신 트렌드 태그 반영.
- **다국어 메타데이터 지원**:
  - 양쪽 언어(한글/영문)의 제목과 설명을 자동으로 생성하여 `localizations` 필드에 저장
  - YouTube가 시청자의 언어 설정에 따라 해당 언어의 제목과 설명을 자동으로 표시
  - 일당백 스타일과 Summary+Video 형식 모두 지원
- **기존 영상 메타데이터 수정**: `src/17_update_video_metadata.py`로 이미 업로드된 영상의 제목·설명·태그를 업데이트
  ```bash
  # 메타데이터 파일 기반으로 업데이트 (영상 ID 자동 검색)
  python src/17_update_video_metadata.py --metadata-file output/영상.metadata.json

  # 영상 ID 직접 지정 (제목이 변경된 경우 권장)
  python src/17_update_video_metadata.py --metadata-file output/영상.metadata.json --video-id VIDEO_ID
  ```
  - 필요 스코프: `youtube.upload` + `youtube.force-ssl` (`scripts/reauth_youtube.py`로 발급)

### 번역 매핑 시스템

- 한글/영문 책 제목 및 저자 이름 자동 번역 지원
- `src/utils/translations.py` 파일에 매핑 관리
- 새로운 책 추가 시 매핑 필요:
  ```python
  # 책 제목 매핑
  "신경 끄기의 기술": "The Subtle Art of Not Giving a F*ck",
  "신경_끄기의_기술": "The Subtle Art of Not Giving a F*ck",
  
  # 저자 이름 매핑
  "마크 맨슨": "Mark Manson",
  ```
- 양방향 번역 지원 (한글→영문, 영문→한글)
- 매핑이 없으면 메타데이터 생성 시 오류 발생

### YouTube Analytics API 연동

- **채널 및 영상 메트릭 수집**: 조회수, 좋아요, 댓글 수, 시청 시간 등
- **자동 메트릭 수집**: 채널 전체 또는 특정 영상의 메트릭 수집
- **데이터 저장**: JSON 및 CSV 형식으로 메트릭 데이터 저장
- **사용 예시**:
  ```bash
  # 채널 전체 메트릭 수집
  python src/15_youtube_analytics.py --channel
  
  # 모든 영상 메트릭 수집
  python src/15_youtube_analytics.py --videos
  
  # 특정 영상 메트릭 수집
  python src/15_youtube_analytics.py --video-id VIDEO_ID
  
  # 기간 지정
  python src/15_youtube_analytics.py --channel --start-date 2025-01-01 --end-date 2025-01-31
  
  # 주간 리포트 생성
  python src/15_youtube_analytics.py --weekly-report
  
  # 월간 리포트 생성
  python src/15_youtube_analytics.py --monthly-report
  
  # 특정 월 리포트 생성
  python src/15_youtube_analytics.py --monthly-report --year 2025 --month 1
  ```
### Analytics 기반 채널 개선 제안

Analytics 데이터를 분석하여 채널 성과를 평가하고 구체적인 개선 제안을 생성합니다.

```bash
# 기본 분석 (최근 30일)
python src/22_analytics_recommendations.py

# 분석 기간 지정
python src/22_analytics_recommendations.py --days 60

# 최소 조회수 필터
python src/22_analytics_recommendations.py --min-views 500
```

**분석 항목:**
- 채널 전체 성과 분석
- 영상별 성과 분석 (조회수, 좋아요, 댓글, 참여율)
- 저성과/고성과 영상 식별
- 참여율 분석 및 개선 제안
- 업로드 빈도 분석
- 조회수 분포 및 일관성 분석
- 콘텐츠 전략 제안

**생성되는 리포트:**
- `output/analytics_recommendations.md`: 상세 분석 및 우선순위별 개선 제안

**제안 카테고리:**
- 🔴 **높은 우선순위**: 즉시 개선이 필요한 항목 (저성과 영상, 낮은 참여율)
- 🟡 **중간 우선순위**: 전략적 개선 항목 (업로드 빈도, 콘텐츠 전략)
- 🟢 **낮은 우선순위**: 유지 관리 항목

### 최적 업로드 시간대 분석

업로드 로그와 YouTube Analytics 데이터를 결합하여 최적의 업로드 시간대를 분석합니다.

```bash
# 최적 업로드 시간대 분석 실행
python src/18_analyze_optimal_upload_time.py

# 결과는 output/optimal_upload_time_analysis.md에 저장됩니다
```

**분석 항목:**
- 요일별 업로드 성과
- 시간대별 업로드 성과
- 업로드 후 24시간/48시간 조회수 성장률
- 최적 업로드 시간대 추천

### 정기 업로드 일정 수립

최적 업로드 시간대 분석 결과를 기반으로 정기 업로드 일정을 생성합니다.

```bash
# 4주간 주 2회 업로드 일정 생성
python src/19_upload_schedule.py --weeks 4 --uploads-per-week 2

# 다음 업로드 날짜 확인
python src/19_upload_schedule.py --show-next

# 특정 날짜부터 시작
python src/19_upload_schedule.py --weeks 4 --uploads-per-week 2 --start-date 2025-01-15
```

**생성되는 파일:**
- `output/upload_schedule.json`: JSON 형식 일정
- `output/upload_schedule_calendar.md`: 캘린더 형식 일정

- **필수 스코프**: YouTube Analytics API 사용을 위해 OAuth2 인증 시 다음 스코프가 필요합니다:
  - `https://www.googleapis.com/auth/youtube.readonly`
  - `https://www.googleapis.com/auth/yt-analytics.readonly`
- **주의사항**: 기존 refresh token에 새로운 스코프를 추가하려면 `scripts/get_youtube_refresh_token.py`를 다시 실행해야 합니다
- **주간/월간 리포트**: 자동으로 Markdown 형식의 리포트 생성
  - 채널 전체 메트릭 요약
  - 영상별 메트릭 (조회수 상위 10개)
  - 통계 요약 (총 조회수, 좋아요, 댓글 수 등)
- **대시보드 생성**: HTML 기반 대시보드로 메트릭 시각화
  ```bash
  # 대시보드 생성
  python src/16_dashboard.py
  
  # 기간 지정
  python src/16_dashboard.py --start-date 2025-01-01 --end-date 2025-01-31
  
  # 생성 후 브라우저에서 자동 열기
  python src/16_dashboard.py --open
  ```

### 깊이 있는 채널 최적화 도구

**1. Analytics 기반 개선 제안 (`src/22_analytics_recommendations.py`)**

채널 데이터를 분석하여 우선순위별로 구체적인 개선안을 제시합니다.
- 조회수, 참여율(좋아요/댓글), 업로드 빈도 등 종합 분석
- 저성과/고성과 콘텐츠 식별 및 맞춤형 전략 제안
- `output/analytics_recommendations.md` 리포트 생성

**2. 최적 업로드 시간대 분석 (`src/18_analyze_optimal_upload_time.py`)**

과거 업로드 기록과 성과를 결합하여 가장 효과적인 시간대를 찾아냅니다.
- 요일별/시간대별 조회수 성장률 분석
- `output/optimal_upload_time_analysis.md` 리포트 생성

**3. 정기 업로드 일정 수립 (`src/19_upload_schedule.py`)**

분석된 최적 시간대를 기반으로 자동화된 업로드 스케줄을 생성합니다.
- 주당 업로드 횟수 및 기간 설정 가능
- `output/upload_schedule_calendar.md` (캘린더 뷰) 제공
  ```
  - 채널 통계 카드 (총 영상 수, 조회수, 좋아요, 댓글 수 등)
  - 조회수 상위 10개 영상 테이블
  - 조회수 분포 차트 (Chart.js 사용)
  - 최근 업로드 영상 목록

### 구조화된 로깅 시스템

- **로그 레벨 관리**: DEBUG, INFO, WARNING, ERROR, CRITICAL 레벨 지원
- **파일 및 콘솔 로그 분리**: 
  - 일반 로그: `logs/{모듈명}.log`
  - 에러 로그: `logs/{모듈명}_error.log` (ERROR 레벨 이상만 저장)
- **로그 파일 로테이션**: 파일 크기 기반 자동 로테이션 (기본 10MB, 최대 5개 백업)
- **컬러 콘솔 출력**: 터미널에서 로그 레벨별 색상 구분 및 이모지 표시
- **환경 변수 설정**: `LOG_LEVEL` 환경 변수로 로그 레벨 제어
  ```bash
  # DEBUG 레벨로 실행 (상세한 디버깅 정보 포함)
  LOG_LEVEL=DEBUG python src/10_create_video_with_summary.py ...
  
  # WARNING 레벨로 실행 (경고 이상만 표시)
  LOG_LEVEL=WARNING python src/10_create_video_with_summary.py ...
  ```
- **사용 예시**:
  ```python
  from utils.logger import get_logger
  
  logger = get_logger(__name__)
  logger.debug("디버깅 정보")
  logger.info("일반 정보")
  logger.warning("경고 메시지")
  logger.error("오류 메시지")
  logger.critical("심각한 오류")
  ```

## 라이선스

MIT License

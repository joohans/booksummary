# 🔴 진행 중 — 「수난이대」(하근찬) 제작 (2026-08-31 세션 중단 시점)

> **다음 세션은 이 문서부터 읽고 이어받는다.** 렌더 직전 단계에서 끊겼다.

## 완료된 것

| 단계 | 결과 |
|---|---|
| 중복 확인 | 478편 전수 — `수난이대`·`하근찬` 0건 |
| 번역 매핑 | `수난이대 ↔ Two Generations of Suffering`, `하근찬 ↔ Ha Geun-chan` (커밋 전) |
| 요약 원고 | `assets/summaries/Two_Generations_of_Suffering_summary_kr.md` (2,309자) |
| TTS | `assets/audio/Two_Generations_of_Suffering_longform_ko.mp3` — **echo**, **5분 12초** |
| NLM 소스 | `data/notebooklm_urls/수난이대_part1_ko.md` (6개, 404 2개를 강제징용·Pacific War로 교체) |
| **NLM 비디오** | **7분 36초** — `assets/video/Two_Generations_of_Suffering_notebooklm_ko.mp4` (복사 완료) |
| 실사 이미지 | **41장** — `assets/images/Two_Generations_of_Suffering/` (100장 중 59장 제거, `_rejected/`에 보관) |
| Flux 1차 | **30장 생성 완료** (GPU150 `/tmp/gen_01..30.jpg`, 로컬 `/tmp/gengen/`에도 복사됨) |

**예상 최종 길이: 약 12분 48초** (요약 5:12 + NLM 7:36)

## 남은 것 (순서대로)

### 1. Flux 추가 10장 회수 (중단 시점에 GPU150에서 생성 중)
```bash
ssh jsong@192.168.0.150 "ls /tmp/gen_*.jpg | wc -l"   # 40이 되면 완료
mkdir -p /tmp/gengen
for n in $(seq -w 1 40); do scp -q jsong@192.168.0.150:/tmp/gen_$n.jpg /tmp/gengen/ 2>/dev/null; done
```
※ 생성 스크립트는 GPU150 `/tmp/gen_gen2.sh`, 로그 `/tmp/gengen2.log`
※ 추가 10장(31~40)은 일상 컷: 표지판·돌담 노인·땔감·빨래·논둑길·차내 좌석·고무신·굴뚝 연기·고갯마루 표지석·마을 사람들

### 2. Flux 크롭 후 합류 (하단 서명 제거)
```python
from PIL import Image
import glob; from pathlib import Path
d = Path('assets/images/Two_Generations_of_Suffering')
for f in sorted(glob.glob('/tmp/gengen/gen_*.jpg')):
    idx = Path(f).stem.split('_')[1]
    im = Image.open(f).convert('RGB'); w,h = im.size
    im = im.crop((0,0,w,int(h*0.90)))                      # 하단 10% 제거
    im = im.resize((1920,int(1920*im.height/im.width)), Image.LANCZOS)
    im.save(d/f'mood_flux_{idx}_scene.jpg', quality=92)
```
→ 목표 **실사 41 + Flux 40 = 81장**

### 3. GPU150 업로드 + 렌더
```bash
rsync -az src/ jsong@192.168.0.150:~/booksummary_render/src/
rsync -az assets/audio/Two_Generations_of_Suffering_longform_ko.mp3 jsong@192.168.0.150:~/booksummary_render/assets/audio/
rsync -az assets/summaries/Two_Generations_of_Suffering_summary_kr.md jsong@192.168.0.150:~/booksummary_render/assets/summaries/
rsync -az assets/video/Two_Generations_of_Suffering_notebooklm_ko.mp4 jsong@192.168.0.150:~/booksummary_render/assets/video/
rsync -az --delete assets/images/Two_Generations_of_Suffering/ jsong@192.168.0.150:~/booksummary_render/assets/images/Two_Generations_of_Suffering/
```
**렌더 스크립트는 아직 없음** — `render_idol.sh`를 복제해 제목/경로만 바꿀 것:
`--book-title "수난이대" --author "하근찬"`, image-dir·notebooklm-video·output 모두 `Two_Generations_of_Suffering`
```bash
ssh jsong@192.168.0.150 "cd ~/booksummary_render && nohup ./render_suffering.sh > logs_suffering.log 2>&1 &"
```
※ 렌더 전 `pgrep -f 10_create_video` 확인 (조회 명령 자신이 잡히므로 `grep -v bash` 필요)

### 4. 검증 → 메타데이터 → 업로드
- 프레임 검사는 **전환 페이드를 피해 5초 오프셋**으로 샘플링 (10초 단위는 페이드 최저점에 걸려 전부 검게 보인다)
- 메타데이터 손질: 제목 `[핵심 요약] 수난이대: 하근찬 (Two Generations of Suffering · AI 심층 분석)`,
  큐레이션 태그 26개(교과서 축 포함), 훅은 아래 각도로
- 공개일: **다음 빈 슬롯 10/25** 또는 근접 슬롯(이후 예약 한 칸씩 뒤로 — 사용자 확인 필요)
- 썸네일 미생성 — Flux 9010 사용 (포트는 `/health`의 model 필드로 재확인)

## 요약 각도 (훅에 그대로 쓸 것)

**아버지는 팔이 없고 아들은 다리가 없다. 외나무다리를 건너는 방법은 하나뿐이다.**

- 아버지 만도의 팔: **태평양 전쟁 징용**(남태평양 섬 비행장, 동굴에서 다이너마이트 점화 중 공습)
- 아들 진수의 다리: **육이오 수류탄**
- ★ **같은 정거장** — 만도가 징용으로 떠난 그 정거장에서 아들을 기다린다
- **외나무다리가 두 번**: 혼자 건널 때(물에 빠져 잘린 팔을 다 보여야 했던 수치의 기억) / 아들을 업고 건널 때
- 정직함: 아버지는 아들을 껴안지 않는다. 인사도 안 하고 주막으로 가버린다. 받아들이는 데 걸린 시간이 **술 몇 잔**
- **고등어 한 손**이 끝까지 손에 들려 있다 — 말로 못 한 마음
- 결말: 등에 아들, 한 손엔 지팡이 한 손엔 고등어. **용머리재가 가만히 내려다본다**

## ★ Flux 결과가 세 편 중 최고였다

고등어를 든 손 · 앞서 걷는 아버지와 목발로 뒤따르는 아들 · **아들을 업고 외나무다리를 건너는 아버지**
— 서사의 결정적 장면이 그대로 나왔다. 스톡으로는 절대 얻을 수 없는 것들이다.
스톡은 이번에도 절반 이상 폐기(59/100): `1950s Korea rural`이 **쿠바 클래식카 4장**을 끌어왔고,
인도 시장·소달구지 5장, 발리 계단식 논 5장, 유럽 성·알프스가 섞였다.

## 커밋 대기 중인 변경
- `src/utils/translations.py` (수난이대·하근찬 매핑)
- `data/notebooklm_urls/수난이대_part1_ko.md` (신규)
- 이 문서

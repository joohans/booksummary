# 🔴 진행 중 — 「만무방」(김유정) 제작 (렌더 중)

> 세션이 끊기면 이 문서부터 읽고 이어받는다. 2026-09-01 18:45 기준 **렌더 24%**.

## 완료된 것

| 단계 | 결과 |
|---|---|
| 중복 확인 | 480편 전수 — 만무방·김유정·응칠 0건 |
| 번역 매핑 | `만무방 ↔ The Good-for-Nothing`, `김유정 ↔ Kim Yu-jeong` (커밋됨) |
| 요약 원고 | `assets/summaries/The_Good_for_Nothing_summary_kr.md` (1,805자) |
| TTS | `assets/audio/The_Good_for_Nothing_longform_ko.mp3` — **nova, 5분 26초** |
| NLM 소스 | `data/notebooklm_urls/만무방_part1_ko.md` (6개, 봄봄만 404 → `봄봄`으로 교체) |
| NLM 비디오 | **8분 15초** — `assets/video/The_Good_for_Nothing_notebooklm_ko.mp4` |
| 이미지 | **73장** (스톡 40 + Flux 33). 밝기 검사 통과 |
| 썸네일 | `output/The_Good_for_Nothing_kr_thumbnail_ko.jpg` (복면한 남자가 달빛 논에서 벼를 자르는 장면) |
| 렌더 스크립트 | GPU150 `~/booksummary_render/render_mmb.sh` |
| 예약 슬롯 | **9/20 확보 완료** — 13편을 +3일 재조정했다(꼬리 10/31) |

**예상 최종 길이: 13분 41초** (요약 5:26 + NLM 8:15)

## 남은 것

### 1. 렌더 완료 확인 + 회수
```bash
ssh jsong@192.168.0.150 "tail -c 2000 ~/booksummary_render/logs_mmb.log | tr '\r' '\n' | grep -a '%' | tail -1"
scp jsong@192.168.0.150:~/booksummary_render/output/The_Good_for_Nothing_kr.mp4 output/
```

### 2. 검증
```bash
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 output/The_Good_for_Nothing_kr.mp4
# 5초 간격 프레임 밝기 — σ 5 이하는 페이드, σ 20 이상은 어두운 사진
```

### 3. 메타데이터 → 업로드
```bash
.venv/bin/python src/08_create_and_preview_videos.py --book-title "만무방" --metadata-only
rm -f output/The_Good_for_Nothing_en.metadata.json
# 손질: 제목에 저자명 추가 / 맞춤 훅 / 태그 26개 / publish_at 2026-09-20T09:00:00Z
.venv/bin/python src/09_upload_from_metadata.py --privacy private --auto \
  --metadata-files output/The_Good_for_Nothing_kr.metadata.json
# 업로드 후 재생목록 PLrZ4eky3zPhJkKccHEIMN2bQPNPzFPzxT 에 추가
```

## 요약 각도 (훅에 쓸 것)

**어떤 농부가 자기 논의 벼를 훔쳤다. 낮에 당당히 거두면 그 벼가 자기 것이 되지 않기 때문이다.**

- 제목 뜻: **만무방 = 예의도 염치도 없는 뻔뻔한 사람**
- 형 응칠: 전과 4범(도박·절도). 빚 때문에 세간 목록을 적고 **"서로 의논하여 억울치 않도록
  나누어 가기 바라노라"** 글을 남기고 울타리 밑구멍으로 도망. 아내·아들과 흩어졌다
- ★ 노름판에서 기호에게 2원 빌려 9원 80전을 따고 **약속대로 5원을 갚고, 우는 재성에게 2원을 더 줬다**
  — 염치 없는 자가 셈은 지킨다
- 동생 응오: 아내 얻으려 3년 머슴. 그 아내가 2년도 못 되어 송장처럼 누웠다.
  **"계집이 다 죽게 됐는데 벼는 다 뭐지유"**
- 구조: 소작료 + **장리**(봄에 한 가마 빌리면 가을에 한 가마 반) → 두 번 떼이면 남는 게 없다
- 결말: 형이 도둑을 몽둥이로 쳤는데 **동생이었다**. 더 때리고, 업고 돌아온다
- ★ **지주와 김 참판은 소설에 얼굴을 내밀지 않는다** — 가장 염치 없는 자가 가장 보이지 않는다
- 김유정은 2년 뒤 29세에 폐결핵으로 사망. 5년간 30편 가까이 썼다

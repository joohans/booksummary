# 「만세전」 제작 준비 (2026-08-26) — 착수 대기

> ⛔ **아직 제작하지 않는다.** 8/27 「생명이란 무엇인가」 공개 성과 판독 후 재개 판단
> → [[feedback_no_stockpiling]]. 여기까지는 **외부 자원을 쓰지 않는 준비**만 해둔 상태.

## 선정 근거

| 항목 | 값 |
|---|---|
| 경쟁 중간값 | **2,632 → 재측정 2,633** (거의 동일, 측정 안정) |
| 제안어 | 13개 중 **책 의도 7개**, 각색 간섭 **0** |
| 제안어 내용 | 줄거리 · 해설 · **천재교육** · 전문 · **미래엔** · 염상섭 · 요약 · 오디오북 |
| 축 | **교과서·학습 수요** — 유행과 무관하게 매년 반복 |

★ **천재교육이 제안어에 뜨는 이유가 확인됐다** — 「만세전」은 실제로 **천재교육 고등학교 문학
교과서에 수록**되어 있다(위키백과 염상섭 항목). 제안어가 우연이 아니라 구조적 수요다.
관부연락선(209회)·김은국 순교자(124회)와 같은 **한국 근대문학** 축이다.

## 완료된 준비

- [x] 중복 체크 — 채널에 없음 (「만세전」·염상섭 0건)
- [x] 경쟁 2회 측정 (2,632 / 2,633)
- [x] `translations.py` 매핑: `만세전 ↔ On the Eve of the Uprising`, `염상섭 ↔ Yom Sang-seop`
      - 영문 제목은 실제 출간 번역본(Sunyoung Park 역) 제목을 따름
      - `safe_title` = `On_the_Eve_of_the_Uprising` 확인
- [x] NLM 소스 URL 6개: `data/notebooklm_urls/만세전_part1_ko.md` (전부 200 확인)
      - 영문 위키에 작품 항목이 없어 저자 항목 + 3·1운동 + 부관연락선으로 구성
- [x] 요약 원고: `assets/summaries/On_the_Eve_of_the_Uprising_summary_kr.md` (2,184자, 약 4.9분)

## 남은 단계 (재개 시)

1. TTS — OpenAI tts-1-hd, 음성은 랜덤. 최근 사용: alloy(생명) → echo(화씨) → nova(부분과 전체)
2. 이미지 210~260개 → AI 검증 상위 100개 (추상 주제 아님, 2.1배로 충분할 것)
3. NLM 리뷰 비디오: `DISPLAY=:99 python3 scripts/nlm_episode_oneshot.py --title "만세전" --parts 1`
4. GPU150 렌더 (`src/` rsync 선행 필수), 무결성 검사, md5 대조
5. 메타데이터 손질(맞춤 훅 + 큐레이션 태그) → 승인 후 업로드 → 재생목록

## 요약 각도

**"이 소설은 연재 3회가 검열로 통째로 삭제되고 잡지가 폐간돼 끊겼다. 원제는 「묘지」였다."**

- 작가 대비: 염상섭은 게이오 대학 유학 중 **삼일운동 가담 혐의로 투옥**됐다. 만세를 부른 쪽에
  서 있던 사람인데, 그가 쓴 주인공은 아무것도 하지 않는다 — 이 어긋남이 축
- 여로형: 도쿄 → 고베 → 시모노세키 → 부산 → 김천 → 대전 → 서울 → **다시 도쿄**(원점 회귀)
- 핵심 장면: **시모노세키 목욕탕**. 일본인들이 조선에서 사람을 값싸게 모아온다는 이야기를
  날씨 이야기처럼 주고받고, 이인화는 조선인임이 드러날까 몸을 움츠린다.
  **각성하는 장면과 비겁한 장면이 같은 장면**이다
- 김천 형의 분노가 식민 통치가 아니라 **공동묘지 규칙**(관습)을 향한다는 환멸 → 원제 「묘지」
- 아내는 고칠 수 있는 병으로 죽고, 그는 장례 후 도쿄로 도망친다
- 마무리: 제목이 「만세전」인 것은 예고가 아니라 **반성**에 가깝다
- 채널 연결: 이인화가 탄 배가 **부관연락선** — 우리 「관부연락선」 편과 같은 배

## 이미지 영문 키워드 20개 (다운로드 시 사용)

```
1920s Korean street colonial era
old Busan harbor black and white
vintage ferry ship deck passengers
steam train window night
Japanese colonial building Seoul
old public bathhouse tiles steam
1920s Tokyo student overcoat
telegram paper old handwriting
Korean traditional funeral procession
old cemetery gravestones grass
rural Korean village thatched roof
dim tavern lantern night
crowded third class ship cabin
police officer 1920s uniform silhouette
train station platform crowd vintage
newspaper printing press old
young man looking out train window
foggy sea from ship rail
narrow alley wooden houses asia
oil lamp dark room interior
```

썸네일 훅 후보: **"그는 무덤에 돌아왔다"** / **"각성한 사람은 아무것도 하지 않았다"**
(구도: 배 난간에 선 1920년대 청년의 뒷모습 + 안개 낀 바다. 밝기·톤 명시 필수)

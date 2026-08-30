# 「만세전」 메타데이터 손질안 (업로드 시 적용)

자동 생성분은 훅이 일반 문구 + 태그에 책·저자 한글 태그가 없다 → 아래로 교체하고
「📖 책 소개」 블록은 다음 `━━━` 구분선 직전까지 제거한다.

## 제목
```
[핵심 요약] 만세전: 염상섭 (On the Eve of the Uprising · AI 심층 분석)
```

## 설명 훅 (맨 앞, 챕터 타임스탬프 아래)
```
연재 세 번째 회가 조선총독부 검열로 통째로 삭제됐고, 잡지가 폐간되면서 연재가 끊겼습니다.
이 년 뒤 작가는 제목을 바꿔 다시 실었습니다. 처음 제목은 「묘지」였습니다.

염상섭은 삼일운동에 가담한 혐의로 감옥에 갔던 사람입니다.
그런데 그가 쓴 주인공 이인화는, 식민지의 실상을 똑똑히 보고도 아무것도 하지 않습니다.
시모노세키 목욕탕에서 조선인을 값싸게 사 온다는 말을 옆에서 들으면서도
자기가 조선인임이 드러날까 몸을 움츠립니다.
각성하는 장면과 비겁한 장면이 같은 장면입니다.

제목이 「만세전」인 것은 그래서 예고가 아니라 반성에 가깝습니다.
```

## 큐레이션 태그 26개
```
만세전, 염상섭, 만세전 줄거리, 만세전 해설, 만세전 요약, 만세전 분석,
염상섭 만세전, 한국근대문학, 근대소설, 여로형소설, 일제강점기소설, 묘지 염상섭,
고등문학, 문학교과서, 수능문학, 내신문학, 한국소설, 고전문학, 문학작품해설,
삼일운동, 부관연락선, 책요약, 책리뷰, 북튜브, 독서, 책추천
```
※ 앞 12개가 검색 표적(제안어 실측 기반), 13~19는 **교과서·학습 수요 축**(이 편의 선정 근거),
나머지는 채널 공통. 「관부연락선」편과 연결되도록 `부관연락선` 포함.

## 고정 댓글 (공개 후 자동 cron이 달지만, 훅은 위 문구로 교체 권장)

## 썸네일 프롬프트 (GPU Flux)
```
Painted watercolor illustration, grave and somber mood, muted desaturated palette
of grey-blue and faded sepia. A young Korean man in a dark 1920s overcoat stands
alone at a ship's railing, seen from behind, shoulders slightly hunched. Before him
a cold foggy sea at dawn, the faint outline of a harbor dissolving in mist.
Soft diffused light, no harsh contrast. Clearly readable shapes at small size,
strong silhouette separation between figure and background. No text, no letters,
no words anywhere in the image.
```
훅 문구(별도 편집): **"그는 무덤에 돌아왔다"** / **"각성한 사람은 아무것도 하지 않았다"**

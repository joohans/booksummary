#!/bin/bash
# usage: scripts/tts_check.sh <slug> <summary.md>
# 요약 TTS 3테이크 생성 → GPU150 Whisper 로 30초 조각 받아쓰기 → 원고 대조(일치율 + 차이 구간)
# 가장 높은 테이크를 assets/audio/{영문제목}_longform_ko.mp3 로 복사해 쓴다.
# ⚠️ 받아쓰기는 숫자를 아라비아 숫자로, 영문 약어(PMP·DNA)를 영문으로 적어 차이로 나온다 — 정상.
#    30초 경계에서 문장을 반복·지어내는 환각도 있다. 3테이크에 공통으로 나오는 오독만 원고를 고친다.
set -e
S=$1; F=$2; D=/tmp/tts_$S; mkdir -p $D; cd "$(dirname "$0")/.."
for i in 0 1 2; do .venv/bin/python src/09_text_to_speech_multi.py --provider openai --text-file $F --output $D/take$i.mp3 --voice nova --language ko > $D/log$i.txt 2>&1 & done; wait
K=~/.ssh/aws-jsong.pem; G=jsong@192.168.0.150
ssh -i $K $G "mkdir -p ~/tts_check/$S"
scp -q -i $K $D/take*.mp3 $G:~/tts_check/$S/
ssh -i $K $G "cd ~/tts_check/$S && W(){ curl -s -F file=@\$1 -F model=Systran/faster-whisper-large-v3 -F language=ko http://localhost:9200/v1/audio/transcriptions | python3 -c 'import sys,json;print(json.load(sys.stdin)[\"text\"].strip())'; }; for i in 0 1 2; do mkdir -p r\$i; ffmpeg -v error -y -i take\$i.mp3 -f segment -segment_time 30 -c copy r\$i/t%02d.mp3; for f in r\$i/t*.mp3; do W \$f; done > t\$i.txt; done"
for i in 0 1 2; do ssh -i $K $G "cat ~/tts_check/$S/t$i.txt" > $D/heard$i.txt; echo "take$i $(ffprobe -v error -show_entries format=duration -of csv=p=0 $D/take$i.mp3)"; done
.venv/bin/python - "$F" "$D" <<'PY'
import re,difflib,sys
F,D=sys.argv[1],sys.argv[2]
src=open(F).read(); src=re.sub(r'<!--.*?-->','',src,flags=re.S); src=re.sub(r'\[.*?\]','',src)
norm=lambda s: re.sub(r'[^가-힣0-9]','',s); a=norm(src)
for i in range(3):
    h=norm(open(f'{D}/heard{i}.txt').read()); sm=difflib.SequenceMatcher(None,a,h,autojunk=False)
    print('take',i,round(sm.ratio(),3))
    for op,a1,a2,b1,b2 in sm.get_opcodes():
        if op!='equal': print('  ',op,a[max(0,a1-6):a2+6],'→',h[max(0,b1-6):b2+6])
PY

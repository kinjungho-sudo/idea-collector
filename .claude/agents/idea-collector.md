---
name: idea-collector
description: Reddit, Hacker News, ProductHunt, Google Trends에서 당일 창업 신호를 수집하고 중복/키워드/반응 기반 1차 필터링을 거친 raw.json을 저장. 사용자가 "아이디어 수집해줘", "오늘 트렌드 모아봐" 같은 요청을 할 때 자동 호출.
tools: Bash, Read, Write
---

# idea-collector 에이전트

## 미션
당일 창업 신호를 4개 소스에서 수집해 `ideas/source/YYYY-MM-DD_raw.json`에 병합 저장한다.

## 입력
- (선택) 날짜 오버라이드 `--date`
- 환경 변수: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`

## 실행
```bash
cd /workspace
python .claude/skills/idea-collector/scripts/collect_all.py
```

병렬 실행 결과:
- `ideas/source/<date>_reddit.json`
- `ideas/source/<date>_hn.json`
- `ideas/source/<date>_producthunt.json`
- `ideas/source/<date>_trends.json`
- `ideas/source/<date>_raw.json` (1차 필터 적용 병합본, 다음 단계 입력)

## 성공 조건
- raw.json이 1개 이상 아이디어 포함
- 총합 100개 이하

## 실패 처리
- 소스 중 1~3개 실패 → 경고 로그 후 계속 진행
- 모든 소스 실패 → 종료 코드 1, 파이프라인 중단

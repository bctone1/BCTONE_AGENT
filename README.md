# BCTone - GrowFit Team AI Assistant

GrowFit 개발팀 4인을 위한 Slack AI 비서.

## 기능

- **진행상황 자동 수집** — 채널 메시지를 조용히 수집, 진행상황/결정사항 자동 분류
- **기술 Q&A** — @비씨톤 멘션으로 기술 질문 응답
- **GitHub 요약** — PR/커밋/diff를 자연어로 요약
- **자동 리포트** — 평일 9시 일일 리포트, 월요일 주간 리포트

## Setup

1. Python 3.12+, PostgreSQL 설치
2. 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```
3. `.env.example`을 `.env`로 복사 후 값 입력
4. Slack App 생성 (Socket Mode, Bot Token, App Token)
5. 실행:
   ```bash
   python -m bctone.app
   ```

## Slack 채널

- `#general` — 팀 소통, @비씨톤 멘션 가능
- `#dev` — 기술 논의, @비씨톤 멘션 가능
- `#bot-log` — 봇 자동 리포트 전용

## 슬래시 커맨드

- `/bctone` — 도움말
- `/bctone 요약` — 팀 진행상황 요약
- `/bctone github backend` — 백엔드 레포 요약
- `/bctone github frontend` — 프론트엔드 레포 요약

# BCTone Slack AI Agent - 작업 기록

> 작성일: 2026-03-27
> 작업자: Damien (백엔드)

---

## 1. 배경

GPTers 김태현, 송다혜님이 출연한 빌더 조쉬 유튜브 영상 "오픈클로를 통해 회사의 모든 워크플로우를 100% 바꿔버린 AI 네이티브 컴퍼니"에서 영감을 받아, GrowFit 팀 내부에 Slack AI 비서를 도입하기로 결정.

### 참고 영상 핵심 내용

- GPTers(지니파이)가 OpenClaw + Slack을 결합해 JARVIS 스타일 24시간 AI 비서를 구축
- 반복 질문 자동 응대, GitHub 현황 자연어 조회, 회사 컨텍스트 학습 등 활용
- OpenClaw 기술 스택: Node.js, Slack Bolt(Socket Mode), Claude Opus, LanceDB, GitHub CLI, Brave Search

### OpenClaw 미사용 결정 (보안 우려)

| 항목 | 평가 |
|------|------|
| 토큰 관리 | openclaw.json에 평문 저장 |
| 메시지 경유 | 모든 팀 대화가 OpenClaw 프로세스를 경유 |
| 오픈소스 성숙도 | 2025년 말~2026년 초 급성장, 본격적 보안 감사 이력 부족 |
| 의존성 체인 | Node.js + 수십 개 npm 패키지 → 공급망 공격 표면 |

**결론:** 4인 팀 규모에서는 기존 스택(Python + PostgreSQL + Claude API)으로 직접 구축하는 것이 보안 통제권 확보 + 오버스펙 방지 측면에서 적합.

---

## 2. 팀 구성 및 목적

| 역할 | 활용 시나리오 |
|------|-------------|
| 팀장 | "이번 주 프론트/백엔드 PR 요약해줘" |
| 기획 | "로그인 기능 어디까지 됐어?" → GitHub 조회 후 비개발 언어로 요약 |
| 프론트엔드 | "백엔드 API 이번 주에 뭐 바뀌었어?" |
| 백엔드 (Damien) | "프론트 레포에서 최근 머지된 PR 보여줘" |

**목적:** 팀원 간 진행상황 공유, 기술 Q&A, GitHub 변경 요약, 회의록/결정사항 관리

---

## 3. 설계 결정사항

### 브레인스토밍 Q&A 요약

| 질문 | 결정 |
|------|------|
| 기능 우선순위 | 진행상황 > 기술Q&A > GitHub요약 > 회의록 |
| 현재 진행상황 공유 방식 | 딱히 체계 없음 → 봇이 처음부터 잡아주는 역할 |
| 진행상황 수집 방식 | 기획/팀장 = 자유 기록 → 봇 정리, 프론트/백엔드 = GitHub 자동 추적 + 봇 보충 |
| GitHub 연동 범위 | PR + 커밋 + diff 자연어 요약 (양쪽 레포) |
| 메모리 구조 | 팀 공유 단일 메모리 (PostgreSQL) |
| 채널 구조 | #general + #dev + #bot-log |
| LLM 모델 | Sonnet 기본 + 복잡한 질문만 Opus 에스컬레이션 |
| 봇 캐릭터 | 격식체, 프로페셔널 (JARVIS 스타일) |
| 아키텍처 | 모놀리식 봇 (방식 1) |
| 배포 | GrowFit 서버에 별도 프로세스 추가 (추가 비용 0원) |
| Slack 연동 | Socket Mode (공인 IP/도메인 불필요) |

### Naming

| 항목 | 값 |
|------|-----|
| 봇 표시 이름 | 비씨톤 |
| Slack 멘션 | @비씨톤 |
| 내부 코드명 | bctone |
| DB 스키마 | `bctone.*` |
| 프로세스명 | bctone-bot |

---

## 4. 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                  GrowFit Server                      │
│                                                      │
│  ┌──────────────────┐    ┌───────────────────────┐   │
│  │ GrowFit FastAPI   │    │ BCTone Bot (독립)      │   │
│  │ :8000             │    │                       │   │
│  └──────────────────┘    │  Slack Bolt (Socket)   │   │
│                           │       │                │   │
│                           │  ┌────┴────┐           │   │
│                           │  │ Router  │           │   │
│                           │  └────┬────┘           │   │
│                           │       │                │   │
│                           │  ┌────┼────┬────┐      │   │
│                           │  ▼    ▼    ▼    ▼      │   │
│                           │ LLM  GH  Mem  Sched   │   │
│                           └──┬───┬────┬───────────┘   │
│                              │   │    │               │
│                              ▼   ▼    ▼               │
│                           Claude GitHub PostgreSQL    │
│                           API    API   (bctone DB)    │
└─────────────────────────────────────────────────────┘
```

### 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.12 |
| Slack SDK | slack-bolt (Socket Mode) |
| LLM | Claude API (Sonnet 기본 + Opus 에스컬레이션) |
| DB | PostgreSQL (bctone 스키마) |
| GitHub | PyGithub (읽기 전용) |
| 스케줄러 | APScheduler |
| 환경변수 | python-dotenv |
| 테스트 | pytest + pytest-mock |

---

## 5. 채널별 봇 동작

| 채널 | 트리거 | 봇 동작 |
|------|--------|---------|
| #general | @비씨톤 멘션 | 질문에 응답 (진행상황, 일반 대화) |
| #general | 자유 메시지 | 조용히 수집 → 진행상황/결정사항이면 메모리 저장 |
| #dev | @비씨톤 멘션 | 기술 질문 응답, GitHub 조회 |
| #dev | 자유 메시지 | 조용히 수집 → 기술 논의/결정사항 메모리 저장 |
| #bot-log | 봇만 게시 (자동) | 일일/주간 리포트, GitHub 변경 요약 |

---

## 6. LLM 라우팅

```
메시지 수신
    │
    ▼
Sonnet으로 의도 분류
    │
    ├── 단순 질문/요약/인사 → Sonnet 직접 응답
    │
    └── 복잡 판단 감지 → Opus 에스컬레이션
         ├── 코드 diff 분석 + 설명
         ├── 다중 PR 비교/종합 판단
         ├── 아키텍처 관련 기술 질문
         └── 긴 회의록/결정사항 종합 요약
```

---

## 7. DB 스키마

```sql
CREATE SCHEMA bctone;

CREATE TABLE bctone.memories (
    id             SERIAL PRIMARY KEY,
    category       VARCHAR(20) NOT NULL,   -- 'progress', 'decision', 'context'
    source_user    VARCHAR(50) NOT NULL,
    source_channel VARCHAR(50) NOT NULL,
    content        TEXT NOT NULL,
    summary        TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    expires_at     TIMESTAMPTZ             -- NULL이면 영구 보존
);

CREATE TABLE bctone.conversations (
    id          SERIAL PRIMARY KEY,
    channel_id  VARCHAR(50) NOT NULL,
    thread_ts   VARCHAR(50),
    role        VARCHAR(10) NOT NULL,      -- 'user', 'assistant'
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bctone.reports (
    id          SERIAL PRIMARY KEY,
    report_type VARCHAR(20) NOT NULL,      -- 'daily', 'weekly'
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 데이터 정책

| 항목 | 정책 |
|------|------|
| progress 메모리 | 생성 후 14일 만료 |
| decision 메모리 | 영구 보존 |
| 대화 히스토리 | 채널+스레드 단위로 최근 20개만 LLM에 전달 |

---

## 8. 스케줄러

| 작업 | 주기 | 동작 |
|------|------|------|
| 일일 리포트 | 평일 오전 9시 (KST) | GitHub 어제 PR/커밋 + 수집된 진행상황 → #bot-log |
| 주간 리포트 | 월요일 오전 9:30 (KST) | 지난 주 종합 + 미해결 사항 → #bot-log |
| 메모리 정리 | 매일 자정 (KST) | expires_at 지난 레코드 삭제 |

---

## 9. 프로젝트 파일 구조

```
BCTONE_AGENT/
├── bctone/
│   ├── __init__.py
│   ├── app.py                 ← 진입점, Bolt + 스케줄러 + Socket Mode
│   ├── config.py              ← 환경변수 로딩, 검증
│   ├── db.py                  ← PostgreSQL 연결, 스키마 초기화
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── mention.py         ← @비씨톤 멘션 → LLM → 응답
│   │   ├── message.py         ← 조용히 수집 → 분류 → 메모리 저장
│   │   └── command.py         ← /bctone 슬래시 커맨드
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm.py             ← Claude API (Sonnet/Opus 라우팅)
│   │   ├── github_service.py  ← PyGithub (PR/커밋/diff)
│   │   ├── memory.py          ← PostgreSQL CRUD
│   │   └── summarizer.py      ← 데이터 종합 → LLM 요약
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── daily_report.py    ← APScheduler 작업 정의
│   └── prompts/
│       ├── __init__.py
│       └── system.py          ← 시스템 프롬프트 상수
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_app.py            ← 통합 스모크 테스트
│   ├── test_config.py
│   ├── test_db.py
│   ├── test_github.py
│   ├── test_handlers.py
│   ├── test_llm.py
│   ├── test_memory.py
│   ├── test_scheduler.py
│   └── test_summarizer.py
├── .env.example
├── .gitignore
├── README.md
├── WORK_LOG.md                ← 이 문서
└── requirements.txt
```

---

## 10. 구현 결과

### 커밋 히스토리

```
62caf48 docs: add README with setup and usage instructions
c3edb0f test: integration smoke tests for app, handlers, and full flows
78fc71b feat: main app wiring - Bolt, handlers, scheduler, Socket Mode
fd2f977 feat: scheduler for daily/weekly reports and memory cleanup
6364e84 feat: slash command handler with summary and github commands
3ede924 feat: mention handler and silent message collection
c77eba4 feat: summarizer service for GitHub and team progress
6c4c5ec feat: GitHub service for PR, commit, and diff retrieval
2fdb042 feat: system prompt and LLM service with Sonnet/Opus routing
c19bcdd feat: memory service with CRUD and expiry cleanup
c46343d feat: database connection and schema initialization
9639256 feat: project scaffolding with config and validation
```

### 테스트 결과

```
39 passed in 0.33s

tests/test_app.py         — 4 tests (통합 스모크)
tests/test_config.py      — 2 tests (설정 로딩/검증)
tests/test_db.py          — 2 tests (DB 연결/스키마)
tests/test_github.py      — 3 tests (PR/커밋/diff)
tests/test_handlers.py    — 9 tests (멘션/메시지/커맨드)
tests/test_llm.py         — 6 tests (분류/에스컬레이션/채팅)
tests/test_memory.py      — 6 tests (CRUD/만료정리)
tests/test_scheduler.py   — 4 tests (리포트/클린업)
tests/test_summarizer.py  — 3 tests (GitHub/팀/일일 요약)
```

---

## 11. 실행 방법

```bash
cd /Users/damienpark/Desktop/BCTONE_AGENT
cp .env.example .env
# .env 편집해서 실제 값 입력
pip install -r requirements.txt
python -m bctone.app
```

### 필요 사전 준비

1. **Slack App 생성** — Socket Mode 활성화, Bot Token(xoxb-) + App Token(xapp-) 발급
2. **GitHub PAT** — 읽기 전용, GF_for_CODEX + GF_Frontend 레포 접근
3. **PostgreSQL** — bctone 데이터베이스 생성
4. **Anthropic API Key** — Claude Sonnet/Opus 접근

### 환경변수 (.env)

```
SLACK_APP_TOKEN=xapp-...
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
GITHUB_REPO_BACKEND=owner/GF_for_CODEX
GITHUB_REPO_FRONTEND=owner/GF_Frontend
BCTONE_DB_URL=postgresql://user:pass@localhost:5432/bctone
DAILY_REPORT_HOUR=9
MEMORY_EXPIRY_DAYS=14
BOT_LOG_CHANNEL_ID=C_your_bot_log_channel
```

---

## 12. 관련 문서

| 문서 | 경로 |
|------|------|
| 설계 스펙 | `IDEA_Growfit/docs/superpowers/specs/2026-03-27-bctone-slack-agent-design.md` |
| 구현 플랜 | `IDEA_Growfit/docs/superpowers/plans/2026-03-27-bctone-slack-agent.md` |
| README | `BCTONE_AGENT/README.md` |

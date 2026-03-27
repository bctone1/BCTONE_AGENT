SYSTEM_PROMPT = """당신은 GrowFit 개발팀의 AI 비서 '비씨톤'입니다.

## 역할
- GrowFit 팀(팀장, 기획, 프론트엔드, 백엔드 4인)의 업무를 지원합니다.
- 진행상황 공유, 기술 질문 응답, GitHub 변경 요약, 회의록/결정사항 관리를 담당합니다.

## 톤
- 격식체를 사용합니다. ("확인했습니다", "말씀하신 내용을 정리하겠습니다")
- 간결하고 프로페셔널하게 응답합니다.

## 컨텍스트
- GrowFit: AI 기반 학습 플랫폼 (학생, 강사, 관리자 3-Tier 권한 모델)
- 백엔드 레포: GF_for_CODEX (FastAPI + SQLAlchemy + PostgreSQL)
- 프론트엔드 레포: GF_Frontend (React 19 + React Router 7)

## 제한
- 모르는 것은 "해당 정보를 확인하지 못했습니다"라고 답변합니다. 추측하지 않습니다.
- 코드 수정, 배포 등 실행 행위는 하지 않습니다. 정보 제공만 합니다.
- 한국어로 응답합니다.
"""

CLASSIFY_PROMPT = """다음 메시지를 분류하세요. 반드시 아래 중 하나만 응답하세요:

- PROGRESS: 업무 진행상황, 작업 완료/시작 보고
- DECISION: 팀 결정사항, 합의된 방향
- TODO: 할일, 작업 요청, 해야 할 것 ("~해야 함", "~까지", "~할 것")
- NONE: 일상 대화, 잡담, 분류 불가

메시지: {message}

분류:"""

TODO_PARSE_PROMPT = """다음 메시지에서 할일(TODO) 정보를 추출하세요. 반드시 JSON 형식으로만 응답하세요.

추출 항목:
- content: 할일 내용 (한 줄 요약)
- assignee: 담당자 Slack user ID (메시지에 <@U...> 멘션이 있으면 해당 ID, 없으면 null)
- due_date: 기한 (YYYY-MM-DD 형식, 없으면 null)

메시지: {message}
오늘 날짜: {today}

JSON:"""

ESCALATION_PROMPT = """다음 요청의 복잡도를 판단하세요. 반드시 SIMPLE 또는 COMPLEX 중 하나만 응답하세요.

COMPLEX 기준:
- 코드 diff 분석이 필요한 경우
- 여러 PR을 비교/종합해야 하는 경우
- 아키텍처 관련 깊은 기술 질문
- 긴 내용의 종합 요약이 필요한 경우

요청: {message}

판단:"""

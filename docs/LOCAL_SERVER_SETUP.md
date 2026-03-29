# BCTone 로컬 서버 셋업 가이드

회사 PC(Windows 11)를 서버로 사용하여 BCTone 봇을 24시간 운영하는 방법.

두 가지 방식 중 선택:
- **[Option A: WSL2 (Ubuntu)](#option-a-wsl2-ubuntu-방식)** — Linux 환경, systemd 자동 재시작
- **[Option B: Windows 네이티브](#option-b-windows-네이티브-방식)** — WSL 없이 Windows에서 직접 실행

---

## 1. BIOS 설정 (PC 전원 관리) — 공통

> 정전 후 자동으로 PC가 켜지도록 설정

1. PC 재부팅 → BIOS 진입 (보통 `F2` 또는 `DEL` 키)
2. **Power Management** 또는 **Advanced** 메뉴에서:
   - `AC Power Recovery` → **On** (또는 `Power On`)
   - `Wake on LAN` → **Enabled** (원격 부팅 필요 시)
3. 저장 후 재부팅

---

# Option A: WSL2 (Ubuntu) 방식

---

## A-2. WSL2 설치

### 2-1. WSL2 활성화

PowerShell을 **관리자 권한**으로 열고:

```powershell
wsl --install -d Ubuntu
```

설치 완료 후 재부팅.

### 2-2. Ubuntu 초기 설정

재부팅 후 Ubuntu 터미널이 자동으로 열림. 사용자명/비밀번호 설정.

```bash
# 패키지 업데이트
sudo apt update && sudo apt upgrade -y
```

### 2-3. WSL2 자동 시작 설정

Windows 부팅 시 WSL이 자동으로 켜지도록:

1. `Win + R` → `shell:startup` 입력
2. 열린 폴더에 `start-wsl.vbs` 파일 생성:

```vbs
Set ws = CreateObject("Wscript.Shell")
ws.Run "wsl -d Ubuntu", 0
```

> 이렇게 하면 Windows 로그인 시 WSL이 백그라운드로 자동 시작됨

---

## A-3. PostgreSQL 설치

### 3-1. 설치

```bash
sudo apt install postgresql postgresql-contrib -y
```

### 3-2. 서비스 시작

```bash
sudo service postgresql start
```

### 3-3. 유저 및 데이터베이스 생성

```bash
# postgres 계정으로 전환
sudo -u postgres psql
```

SQL 실행:

```sql
-- 유저 생성 (비밀번호는 원하는 값으로 변경)
CREATE USER bctone WITH PASSWORD '여기에비밀번호입력';

-- 데이터베이스 생성
CREATE DATABASE bctone_bot OWNER bctone;

-- 스키마 권한 부여
\c bctone_bot
CREATE SCHEMA IF NOT EXISTS bctone AUTHORIZATION bctone;

-- 종료
\q
```

### 3-4. 연결 테스트

```bash
psql -U bctone -d bctone_bot -h localhost
# 비밀번호 입력 후 접속되면 성공
\q
```

### 3-5. PostgreSQL 자동 시작

WSL에서는 systemd가 기본 비활성이므로 수동 설정:

```bash
# ~/.bashrc 맨 아래에 추가
echo 'sudo service postgresql start 2>/dev/null' >> ~/.bashrc
```

비밀번호 없이 실행되도록:

```bash
sudo visudo
# 맨 아래에 추가 (username은 본인 WSL 유저명):
# username ALL=(ALL) NOPASSWD: /usr/sbin/service postgresql start
```

---

## A-4. 프로젝트 설치

### 4-1. 필수 패키지

```bash
sudo apt install python3 python3-venv python3-pip git -y
```

### 4-2. 프로젝트 클론

```bash
cd ~
git clone https://github.com/bctone1/BCTONE_AGENT.git
cd BCTONE_AGENT
```

### 4-3. 가상환경 생성 및 의존성 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## A-5. 환경변수 설정 (.env)

```bash
cp .env.example .env
nano .env
```

아래 값들을 실제 값으로 채우기:

```bash
# ── Slack ──
SLACK_APP_TOKEN=xapp-...        # api.slack.com > 앱 > Socket Mode > Token
SLACK_BOT_TOKEN=xoxb-...        # 앱 > OAuth & Permissions > Bot User OAuth Token
SLACK_SIGNING_SECRET=...        # 앱 > Basic Information > Signing Secret

# ── LLM ──
ANTHROPIC_API_KEY=sk-ant-...    # console.anthropic.com > API Keys

# ── GitHub ──
GITHUB_TOKEN=ghp_...            # GitHub > Settings > Developer settings > PAT
GITHUB_REPO_BACKEND=bctone1/GF_Backend
GITHUB_REPO_FRONTEND=bctone1/GF_Frontend
GITHUB_REPO_PLANNING=ehdgml53/mintlify-docs
GITHUB_DEFAULT_BRANCH=onecloud

# ── PostgreSQL ──
DB=postgresql
DB_USER=bctone
DB_PASSWORD=3단계에서설정한비밀번호
DB_PORT=5432
DB_NAME=bctone_bot
BCTONE_DB_URL=postgresql://bctone:3단계에서설정한비밀번호@localhost:5432/bctone_bot

# ── 스케줄러 ──
DAILY_REPORT_HOUR=18
WEEKLY_REPORT_HOUR=18
MEMORY_EXPIRY_DAYS=14

# ── Slack 채널 ──
BOT_LOG_CHANNEL_ID=C...         # Slack 채널 우클릭 > 채널 세부정보 > 채널 ID
```

저장: `Ctrl + O` → `Enter` → `Ctrl + X`

---

## A-6. 첫 실행 테스트

```bash
cd ~/BCTONE_AGENT
source .venv/bin/activate
python -m bctone.app
```

확인사항:
- [ ] 터미널에 에러 없이 시작 로그가 출력되는가
- [ ] Slack에서 봇이 온라인(초록불)으로 표시되는가
- [ ] 아무 채널에 메시지 쓰면 봇이 분류하는가
- [ ] `@BCTone` 멘션하면 응답하는가

문제 없으면 `Ctrl + C`로 종료.

---

## A-7. 백그라운드 자동 실행 설정

봇을 항상 켜놓고, 크래시 시 자동 재시작되도록 설정.

### 방법 A: systemd (WSL2에서 systemd 활성화된 경우)

#### 7-A-1. systemd 활성화 확인

```bash
# systemd가 PID 1인지 확인
ps -p 1 -o comm=
```

`systemd`가 출력되면 사용 가능. 아니면 활성화:

```bash
sudo nano /etc/wsl.conf
```

```ini
[boot]
systemd=true
```

저장 후 PowerShell에서:

```powershell
wsl --shutdown
wsl
```

#### 7-A-2. 서비스 파일 생성

```bash
sudo nano /etc/systemd/system/bctone.service
```

```ini
[Unit]
Description=BCTone Slack Bot
After=network.target postgresql.service

[Service]
Type=simple
User=본인WSL유저명
WorkingDirectory=/home/본인WSL유저명/BCTONE_AGENT
EnvironmentFile=/home/본인WSL유저명/BCTONE_AGENT/.env
ExecStart=/home/본인WSL유저명/BCTONE_AGENT/.venv/bin/python -m bctone.app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user-target
```

#### 7-A-3. 서비스 등록 및 시작

```bash
sudo systemctl daemon-reload
sudo systemctl enable bctone
sudo systemctl start bctone
```

#### 7-A-4. 상태 확인

```bash
# 실행 상태 확인
sudo systemctl status bctone

# 로그 보기
sudo journalctl -u bctone -f
```

### 방법 B: 스크립트 방식 (systemd 안 될 때)

#### 7-B-1. 실행 스크립트 생성

```bash
nano ~/start-bctone.sh
```

```bash
#!/bin/bash
cd /home/본인WSL유저명/BCTONE_AGENT
source .venv/bin/activate

while true; do
    echo "[$(date)] BCTone 시작"
    python -m bctone.app
    echo "[$(date)] BCTone 종료됨. 10초 후 재시작..."
    sleep 10
done
```

```bash
chmod +x ~/start-bctone.sh
```

#### 7-B-2. ~/.bashrc에 자동 실행 추가

```bash
echo '
# BCTone 자동 시작
if ! pgrep -f "python -m bctone.app" > /dev/null; then
    nohup ~/start-bctone.sh >> ~/bctone.log 2>&1 &
fi
' >> ~/.bashrc
```

> WSL이 시작될 때마다 봇이 자동으로 백그라운드 실행됨

---

## A-8. 운영 관리 명령어

```bash
# ── 상태 확인 ──
sudo systemctl status bctone        # systemd 방식
pgrep -f "python -m bctone.app"     # 스크립트 방식

# ── 로그 보기 ──
sudo journalctl -u bctone -f        # systemd 방식
tail -f ~/bctone.log                 # 스크립트 방식

# ── 재시작 ──
sudo systemctl restart bctone       # systemd 방식

# ── 중지 ──
sudo systemctl stop bctone          # systemd 방식

# ── 코드 업데이트 후 재시작 ──
cd ~/BCTONE_AGENT
git pull
sudo systemctl restart bctone
```

---

# Option B: Windows 네이티브 방식

---

## B-2. Python 설치

1. [python.org/downloads](https://www.python.org/downloads/) 에서 최신 Python 3.x 다운로드
2. 설치 시 **"Add python.exe to PATH"** 반드시 체크
3. 설치 완료 후 CMD/PowerShell에서 확인:

```powershell
python --version
pip --version
```

---

## B-3. PostgreSQL 설치

### B-3-1. 설치

1. [postgresql.org/download/windows](https://www.postgresql.org/download/windows/) 에서 Windows installer 다운로드
2. 설치 중 설정:
   - 포트: `5432` (기본값)
   - superuser(postgres) 비밀번호 설정 → 기억해둘 것
3. **Stack Builder**는 건너뛰기 (필요 없음)

### B-3-2. 유저 및 데이터베이스 생성

시작 메뉴에서 **SQL Shell (psql)** 실행 후:

```
Server [localhost]: (Enter)
Database [postgres]: (Enter)
Port [5432]: (Enter)
Username [postgres]: (Enter)
Password: (설치 시 설정한 비밀번호)
```

SQL 실행:

```sql
-- 유저 생성
CREATE USER bctone WITH PASSWORD '여기에비밀번호입력';

-- 데이터베이스 생성
CREATE DATABASE bctone_bot OWNER bctone;

-- 스키마 권한 부여
\c bctone_bot
CREATE SCHEMA IF NOT EXISTS bctone AUTHORIZATION bctone;

-- 종료
\q
```

### B-3-3. 연결 테스트

```powershell
# PostgreSQL bin 폴더가 PATH에 있으면:
psql -U bctone -d bctone_bot -h localhost
# 비밀번호 입력 후 접속되면 성공
\q
```

> PostgreSQL은 Windows 서비스로 설치되어 **PC 부팅 시 자동 시작**됨 (별도 설정 불필요)

---

## B-4. 프로젝트 설치

### B-4-1. Git 설치 (없는 경우)

[git-scm.com/download/win](https://git-scm.com/download/win) 에서 설치.

### B-4-2. 프로젝트 클론

```powershell
cd C:\Users\본인유저명
git clone https://github.com/bctone1/BCTONE_AGENT.git
cd BCTONE_AGENT
```

### B-4-3. 가상환경 생성 및 의존성 설치

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## B-5. 환경변수 설정 (.env)

```powershell
copy .env.example .env
notepad .env
```

메모장에서 값 채우기 (내용은 [A-5. 환경변수 설정](#a-5-환경변수-설정-env)과 동일).

---

## B-6. 첫 실행 테스트

```powershell
cd C:\Users\본인유저명\BCTONE_AGENT
.venv\Scripts\activate
python -m bctone.app
```

확인사항:
- [ ] 터미널에 에러 없이 시작 로그가 출력되는가
- [ ] Slack에서 봇이 온라인(초록불)으로 표시되는가
- [ ] 아무 채널에 메시지 쓰면 봇이 분류하는가
- [ ] `@BCTone` 멘션하면 응답하는가

문제 없으면 `Ctrl + C`로 종료.

---

## B-7. 자동 실행 설정 (Task Scheduler)

Windows 작업 스케줄러를 이용하여 로그온 시 자동 실행 + 크래시 시 재시작.

### B-7-1. 실행 스크립트 생성

프로젝트 폴더에 `start-bctone.bat` 파일 생성:

```bat
@echo off
cd /d C:\Users\본인유저명\BCTONE_AGENT
call .venv\Scripts\activate

:loop
echo [%date% %time%] BCTone 시작
python -m bctone.app
echo [%date% %time%] BCTone 종료됨. 10초 후 재시작...
timeout /t 10 /nobreak
goto loop
```

### B-7-2. Task Scheduler 등록

1. `Win + R` → `taskschd.msc` 입력 → 작업 스케줄러 열기
2. 오른쪽 패널에서 **"작업 만들기"** 클릭
3. **일반** 탭:
   - 이름: `BCTone Bot`
   - "사용자가 로그온할 때만 실행" 선택
   - "가장 높은 수준의 권한으로 실행" 체크
4. **트리거** 탭 → 새로 만들기:
   - 작업 시작: **로그온할 때**
   - 확인
5. **동작** 탭 → 새로 만들기:
   - 동작: **프로그램 시작**
   - 프로그램/스크립트: `C:\Users\본인유저명\BCTONE_AGENT\start-bctone.bat`
   - 시작 위치: `C:\Users\본인유저명\BCTONE_AGENT`
   - 확인
6. **설정** 탭:
   - "요청 시 작업을 중지할 수 있도록 허용" 체크
   - "작업이 이미 실행 중이면 다음 규칙 적용" → **새 인스턴스 시작 안 함**
   - 확인

### B-7-3. 자동 로그온 설정 (선택)

PC 재부팅 후 로그인 화면에서 멈추면 Task Scheduler가 동작 안 함. 자동 로그온 설정:

1. `Win + R` → `netplwiz` 입력
2. "사용자 이름과 암호를 입력해야 이 컴퓨터를 사용할 수 있음" 체크 해제
3. 비밀번호 입력 후 확인

> 이제 PC 전원만 들어오면 자동 로그인 → Task Scheduler → BCTone 자동 실행

---

## B-8. 운영 관리 명령어

```powershell
# ── 상태 확인 ──
tasklist | findstr python

# ── 로그 보기 ──
# start-bctone.bat의 출력이 CMD 창에 표시됨

# ── 중지 ──
taskkill /f /im python.exe
# 주의: 다른 Python 프로세스도 종료됨. 특정 프로세스만 종료하려면:
# 작업 관리자 > 세부 정보 > 해당 python.exe PID 확인 후
taskkill /f /pid 프로세스ID

# ── 코드 업데이트 후 재시작 ──
cd C:\Users\본인유저명\BCTONE_AGENT
git pull
# CMD 창 닫고 start-bctone.bat 다시 실행 (또는 PC 재부팅)
```

---

# 공통 섹션

---

## 9. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| Slack에서 봇이 오프라인 | 봇 프로세스 안 돌아감 | WSL: `systemctl status bctone` / Win: `tasklist \| findstr python` |
| DB 연결 실패 | PostgreSQL 안 켜짐 | WSL: `sudo service postgresql start` / Win: 서비스 관리자에서 postgresql 시작 |
| `ANTHROPIC_API_KEY` 에러 | .env 키 잘못됨 | `.env` 파일에서 키 확인 |
| WSL이 안 켜짐 | Windows 재부팅 후 | startup 폴더의 `start-wsl.vbs` 확인 |
| Task Scheduler 안 돌아감 | 자동 로그온 안 됨 | `netplwiz`에서 자동 로그온 설정 확인 |
| 봇이 응답 안 함 | 토큰 만료 또는 권한 부족 | api.slack.com에서 토큰 재발급 |
| 메모리 부족 | 로그 파일 비대 | WSL: `> ~/bctone.log` / Win: 로그 파일 삭제 후 재시작 |
| `pip install` 실패 (Win) | Visual C++ 빌드 도구 없음 | [Build Tools for VS](https://visualstudio.microsoft.com/visual-cpp-build-tools/) 설치 |

---

## 체크리스트

### 공통
- [ ] BIOS: AC Power Recovery = On

### Option A (WSL2) 선택 시
- [ ] WSL2 Ubuntu 설치 완료
- [ ] WSL 자동 시작 설정 (`start-wsl.vbs`)
- [ ] PostgreSQL 설치 + 유저/DB 생성
- [ ] PostgreSQL 자동 시작 설정
- [ ] 프로젝트 클론 + 의존성 설치
- [ ] `.env` 파일 작성
- [ ] 첫 실행 테스트 통과
- [ ] 백그라운드 자동 실행 설정 (systemd 또는 스크립트)
- [ ] PC 재부팅 후에도 봇이 자동 시작되는지 최종 확인

### Option B (Windows) 선택 시
- [ ] Python 설치 + PATH 등록
- [ ] PostgreSQL 설치 + 유저/DB 생성
- [ ] Git 설치
- [ ] 프로젝트 클론 + 의존성 설치
- [ ] `.env` 파일 작성
- [ ] 첫 실행 테스트 통과
- [ ] `start-bctone.bat` 생성
- [ ] Task Scheduler 등록
- [ ] 자동 로그온 설정 (`netplwiz`)
- [ ] PC 재부팅 후에도 봇이 자동 시작되는지 최종 확인

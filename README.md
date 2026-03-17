# CVE-2022-22965 · Spring4Shell 취약점 교육 실습

> **⚠️ 경고 (Warning)**  
> 이 저장소는 **SK쉴더스 이큐스트(EQST) 교육 기관의 가이드라인**에 따른 **교육 목적의 모의해킹(Penetration Testing) 실습 코드**입니다.  
> 모든 공격은 교육기관에서 제공한 **로컬 격리 환경(Docker)**에서만 수행되었습니다.  
> 무단으로 허가받지 않은 시스템에 사용하는 것은 법적으로 엄격히 금지됩니다.

---

## 🚀 원클릭 실습 가이드 (run.py)

본 프로젝트는 복잡한 수동 명령어를 배제하고, 초보자도 한 번에 실습 결과를 확인할 수 있는 **자동 통합 스크립트(`run.py`)**를 중심 기능으로 제공합니다.

### 1. 작업 폴더 이동 및 구동 확인
```bash
cd "/Users/glory1994/Library/CloudStorage/OneDrive-개인/99.Develop/CVE-2022-22965"
docker ps | grep spring
```
*결과 화면에 `cvepratice-spring-1` 컨테이너가 정상 실행 중인지 확인합니다.*

### 2. 공격 자동화 스크립트 실행
```bash
python3 run.py
```

### 3. HTML 보고서 확인
실행이 끝나면 현재 폴더에 자동 생성되는 `report_YYYYMMDD_HHMMSS.html` 파일을 열람하세요. 단순 취약점 공격뿐만 아니라, **데이터베이스 접속 환경 변수가 통째로 탈취되는 심각한 상황(Step 6)**을 직관적인 UI를 통해 직접 확인할 수 있습니다.

---

## 📑 목차
- [취약점 개요](#취약점-개요)
- [영향 받는 환경](#영향-받는-환경)
- [공격 시나리오](#공격-시나리오)
- [테스트 환경](#테스트-환경)
- [프로젝트 구조](#프로젝트-구조)
- [아키텍처 설계 원칙](#아키텍처-설계-원칙)
- [run.py 내부 자동화 원리](#runpy-내부-자동화-원리)
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

## run.py 내부 자동화 원리 (Step 1 ~ 6)

`run.py` 실행 한 번으로 아래의 6개 해킹 공격 및 탈취 과정이 내부적으로 완벽하게 시뮬레이션됩니다.

**Step 1. Stage 1 페이로드 전송**
- 타겟 서버의 `ClassLoader`를 변조하여 외부 코드 실행 지시를 내리는 악의적인 Spring Data Binding 페이로드를 조작해 전송합니다.

**Step 2. Tomcat 로그 Flush 유도**
- 공격 내용이 물리적 디스크(webapps/ROOT/yaho4.jsp)에 실제 웹쉘 파일 형태로 떨어질 수 있도록 Tomcat 로그 기록을 인위적으로 발생시킵니다.

**Step 3. Stage 1 쉘 (Stager) 검증**
- 서버에 생성된 기초 웹쉘(`yaho4.jsp`)에 접속하여 `whoami` 명령을 실행하고 최고 권한(`root`) 획득 여부를 검증합니다.

**Step 4. 완성형 Stage 2 웹쉘 배포**
- 1단계 웹쉘을 거점으로 삼아, 더욱 복잡하고 강력한 행위가 가능한 자체 제작 완성형 웹쉘(`health_check.jsp`)을 서버 네트워크 내부로 자동 다운로드(curl) 또는 복사(docker cp) 배포합니다.

**Step 5. 최종 제어권 획득 검증**
- `health_check.jsp`를 통해 최종적으로 서버에 권한(`uid=0`)을 행사할 수 있는지 응답값을 확인합니다.

**Step 6. 보너스: 데이터베이스 위협 증명 시뮬레이션**
- 개발자와 보안 담당자가 취약점에 대한 위기 의식을 체감할 수 있도록, 해커가 DB 접속 암호를 쉽게 탈취해 갈 수 있는 주요 인프라 **환경변수(`env`)** 목록 전체와 핵심 애플리케이션 **설정 폴더 리스트(`ls -la`)**를 원격으로 강제 덤프(Dump)합니다.

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

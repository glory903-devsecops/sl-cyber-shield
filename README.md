<div align="center">

# 🎯 CVE-2022-22965 (Spring4Shell)
## 모의해킹 자동화 실습 — 메인 & 내부자 위협 서브 시나리오

![Spring](https://img.shields.io/badge/Spring_Framework-6DB33F?style=for-the-badge&logo=spring&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python_3-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SOLID](https://img.shields.io/badge/SOLID_Principles-6366f1?style=for-the-badge&logo=databricks&logoColor=white)
![Clean Arch](https://img.shields.io/badge/Clean_Architecture-f59e0b?style=for-the-badge&logo=circle&logoColor=white)

**SK쉴더스 이큐스트(EQST) 가이드라인 기반 모의해킹 자동화 및 인프라 보안 진단 실습**

---
</div>

> [!CAUTION]
> **본 프로젝트는 철저히 교육 목적으로만 사용할 수 있습니다.**
> 모든 시나리오와 스크립트는 **격리된 로컬 Docker 환경** 전용입니다.
> 권한 없는 외부 시스템에 사용하는 것은 정보통신망법 등에 의거하여 엄격히 금지됩니다.

---

## 🚀 빠른 시작 (Quick Start)

### 전제 조건 — 테스트 서버 구동

```bash
cd 01.TestServer
docker compose up -d
docker ps -a   # 컨테이너 정상 실행 확인
```

### 메인 시나리오 실행

```bash
# 루트 폴더에서 실행
python3 run.py
```

> 실행 후 `03.FinalReport/main_scenario_report_YYYYMMDD_HHMMSS.html` 이 자동 생성됩니다.

### 서브 시나리오 실행 (내부자 위협)

```bash
# 루트 폴더에서 실행
python3 sub_run.py
```

> 실행 후 `03.FinalReport/sub_scenario_insider_threat_YYYYMMDD_HHMMSS.html` 이 자동 생성됩니다.

---

## ⚔️ 두 시나리오 비교

| 구분 | 🔴 메인 시나리오 (`run.py`) | 🟠 서브 시나리오 (`sub_run.py`) |
|:---|:---|:---|
| **공격자** | 외부 해커 | 불만을 품은 내부 직원 |
| **시작점** | 외부 인터넷 → Spring 웹 앱 | 내부망 Employee Desktop |
| **초기 접근** | CVE-2022-22965 제로데이 익스플로잇 | 정상 업무 권한 남용 |
| **9개 Step** | Spring4Shell→ 웹쉘→ DB탈취→ 횡적이동 | 정찰→ NAS탈취→ 크리덴셜→ DB→ CI/CD→ 백도어 |
| **보고서 파일명** | `main_scenario_report_*.html` | `sub_scenario_insider_threat_*.html` |
| **MITRE ATT&CK** | T1190 (External Exploit) | T1078 (Valid Accounts) |

---

## 📁 폴더 구조

```text
CVE-2022-22965/
│
├── README.md                      # 🌟 메인 가이드 (이 문서)
├── run.py                         # 🚀 메인 시나리오 자동 실행기 (9 Steps)
├── sub_run.py                     # 🕵️ 서브 시나리오 실행기 (6 Phases)
│
├── 01.TestServer/                 # 🐳 취약 실습 서버 (Docker Compose) [gitignore]
│   └── docker-compose.yml         #     Spring, Struts, TeamCity, Gitea, NAS 등 포함
│
├── 02.AttackScripts/              # ⚙️ 공격 모듈 (Clean Architecture)
│   ├── stage1_dropper.py          #     [Stage 1] Spring4Shell 페이로드 전송
│   ├── stage2_uploader.py         #     [Stage 2] 고급 웹쉘(health_check.jsp) 배포
│   ├── stage3_lateral_movement.py #     [Stage 3] TeamCity/Struts2/NAS 횡적 이동
│   ├── health_check.jsp           #     [Stage 2 웹쉘] Clean Architecture 구조의 JSP
│   └── tests/                     #     ✅ 유닛 테스트 (SOLID + Clean Architecture)
│       ├── test_stage1_dropper.py  #        Stage 1 페이로드 생성 · 컨트롤러 검증 (16개)
│       ├── test_stage2_uploader.py #        Stage 2 배포 UseCase · Fake I/O 검증 (13개)
│       └── test_stage3_lateral_movement.py # Stage 3 RCE · TeamCity · NAS 검증 (15개)
│
├── 03.FinalReport/                # 📊 HTML 보고서 자동 저장 폴더
│   ├── main_scenario_report_*.html       # run.py 실행 결과 보고서
│   └── sub_scenario_insider_threat_*.html # sub_run.py 실행 결과 보고서
│
├── 04.SubScenarios/               # 🔥 내부자 위협 시나리오 상세 가이드
│   ├── README.md                  #     6-Phase 공격 타임라인 · MITRE ATT&CK 매핑
│   └── tests/                     #     ✅ 내부자 위협 Phase별 유닛 테스트 (21개)
│       └── test_insider_threat_phases.py
│
└── 99.Legacy/                     # 🕰️ 이전 버전 레거시 참고 자료
```

---

## 🔬 메인 시나리오 — 9 Steps 상세

`run.py` 는 Spring4Shell → TeamCity → Struts2 → NAS까지 이어지는 **CVE 연계 공격 체인**을 완전 자동화합니다.

| Step | 작업 | 성공 조건 |
|:---:|:---|:---|
| **1** | Spring4Shell 페이로드 전송 (AccessLogValve 변조) | HTTP 200/400 응답 |
| **2** | Tomcat 로그 Flush (웹쉘 디스크 기록 유도) | GET 요청 성공 |
| **3** | Stage 1 웹쉘(`yaho4.jsp`) 생성 확인 (최대 5회 재시도) | `whoami` 응답 확인 |
| **4** | Stage 2 웹쉘(`health_check.jsp`) 배포 | curl or `docker cp` |
| **5** | Stage 2 웹쉘 동작 검증 | `uid=` 포함 응답 |
| **6** | DB 크리덴셜 탈취 (`application.properties` 직접 추출) | DB URL/USER/PASS 추출 |
| **7** | 내부 MySQL DB 직접 접속 및 덤프 | 고객 테이블 SELECT |
| **8** | TeamCity CVE-2024-27198 → Struts2 CVE-2023-50164 횡적 이동 | 임직원 DB 탈취 |
| **9** | NAS SMB 파일 시스템 열람 (JCIFS-NG) | NAS 파일 목록 확인 |

---

## 🕵️ 서브 시나리오 — 6 Phases 내부자 위협

`sub_run.py` 는 불만을 품은 내부 직원이 **정상 업무 권한만으로** 수행 가능한 APT 공격을 시뮬레이션합니다.

| Phase | 작업 | 위협 수준 |
|:---:|:---|:---:|
| **1** | 정찰 — 내부 시스템 구조 파악 (VNC, Gitea, TeamCity) | 🟡 Low |
| **2** | NAS SMB 기밀 탈취 — 제품 설계도 & CI/CD 토큰 | 🔴 Critical |
| **3** | 크리덴셜 수집 — `application.properties` 하드코딩 DB 정보 추출 | 🟠 High |
| **4** | 내부 DB 직접 접근 — spring-db/struts-db 3306 포트 도달 | 🔴 Critical |
| **5** | CI/CD 장악 — TeamCity API · Gitea push 권한 확인 | 🔴 Critical |
| **6** | 백도어 삽입 & 흔적 은폐 — 정상 commit 위장, bash_history 삭제 | 🔴 Critical |

---

## ✅ 유닛 테스트 실행

모든 공격 스크립트는 **SOLID 원칙과 Clean Architecture** 기반으로 설계되어 있으며, 실제 서버 없이 단위 테스트가 가능합니다.

```bash
# Stage 1, 2, 3 공격 모듈 테스트 (44개)
python3 -m unittest discover -s 02.AttackScripts/tests -p "test_*.py" -v

# 내부자 위협 6 Phase 테스트 (21개)
python3 -m unittest discover -s 04.SubScenarios/tests -p "test_*.py" -v
```

| 원칙 | 적용 방식 |
|:---|:---|
| **SRP** | `ExploitConfig`, `PayloadGenerator`, `ExploitController` 클래스 완전 분리 |
| **OCP** | Fake/Spy 구현체 교체로 새 테스트 추가 시 기존 코드 수정 없음 |
| **LSP** | `FileServerPort`, `Stage1CommandPort` Fake가 추상 계약을 완전 이행 |
| **ISP** | 테스트는 필요한 Port 인터페이스만 사용 |
| **DIP** | 실제 I/O를 인메모리 Fake/Monkeypatch로 완전 대체 |

---

## 🖥️ 실시간 모니터링 (선택사항)

공격 스크립트 실행 중 서버 내부를 실시간으로 확인합니다.

```bash
# Spring 서버 공격 로그 실시간 확인
docker logs -f 01testserver-spring-1

# 웹쉘 생성 여부 1초 주기 감시
docker exec -it 01testserver-spring-1 bash
watch -n 1 ls -la /usr/local/tomcat/webapps/ROOT/
```

---

## 🌐 내부 서비스 구성 (Docker)

| 서비스 | 컨테이너명 | 포트 | 역할 |
|:---|:---|:---:|:---|
| Spring Web | `01testserver-spring-1` | 8011 | 취약 타겟 (CVE-2022-22965) |
| Struts Web | `01testserver-struts-1` | 8080 | 횡적 이동 타겟 (CVE-2023-50164) |
| Spring DB | `01testserver-spring-db-1` | 3306 | 고객 정보 MySQL |
| Struts DB | `01testserver-struts-db-1` | 3306 | 직원 정보 MySQL |
| TeamCity | `01testserver-teamcity-server-1` | 8111 | CI/CD (CVE-2024-27198) |
| Gitea | `01testserver-gitea-1` | 3000 | 소스코드 저장소 |
| NAS | `01testserver-nas-1` | 445 | 내부 파일 서버 (SMB) |

---

## 🛡️ 대응 방안 (Mitigation)

| 중요도 | 조치 방안 | 대상 |
|:---:|:---|:---|
| 🔴 **긴급** | Spring Framework `5.3.18+` / `5.2.20+` 으로 업그레이드 | 개발/운영 |
| 🔴 **긴급** | 소스코드 내 하드코딩 크리덴셜 제거 → Vault/Secret Manager 도입 | 개발 |
| 🟠 **경보** | NAS 파일 ACL 최소 권한 적용, 불필요 SMB 마운트 제거 | 인프라 |
| 🟠 **경보** | TeamCity/Gitea API 토큰 암호화 보관, main 브랜치 직접 push 차단 | DevOps |
| 🟡 **주의** | Apache Tomcat `9.0.62+` 패치 적용 | 인프라/미들웨어 |
| 🟡 **주의** | 내부 사용자 행동 분석(UBA) 솔루션 도입 | 보안 운영 |

---

<div align="center">
  <sub>Created with 💻 Team EQST & AI Assistant | SOLID + Clean Architecture 기반 설계</sub>
</div>

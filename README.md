<div align="center">

# 🎯 모의해킹 자동화 실습 체계
### 🛡️ 제로데이 공격부터 내부자 위협까지, 단 한 번의 클릭으로 경험하세요

![Spring](https://img.shields.io/badge/Spring_Framework-6DB33F?style=for-the-badge&logo=spring&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python_3-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SOLID](https://img.shields.io/badge/Clean_Architecture-f59e0b?style=for-the-badge&logo=databricks&logoColor=white)

**SK쉴더스 이큐스트(EQST) 가이드라인 기반 인프라 보안 진단 플랫폼**

<br>

> 💡 **보안 입문자 환영!**
> 이 프로젝트는 복잡한 해킹 기술을 몰라도, 스크립트 실행 한 번으로 **실제 해커가 시스템을 장악하는 전 과정**을 눈으로 보고 배울 수 있도록 설계되었습니다.

</div>

---

<br>

<div align="center">
  <h2>🚨 주의 사항 (경고)</h2>
</div>

> [!CAUTION]
> **본 프로젝트는 철저히 보안 교육 및 연구 목적으로만 제공됩니다.**
> 제공된 모든 해킹 시나리오는 동봉된 **격리된 로컬 Docker 환경** 내에서만 작동하도록 설계되었습니다.
> 사전 협의 없는 타인의 시스템에 이를 시도하는 것은 정보통신망법 위반으로 엄격히 금지됩니다.

<br>

---

<br>

## 🚀 아주 쉬운 시작 가이드 (Quick Start)

초보자 분들도 아래 명령어 단 3줄만 입력하면 해킹 실습 환경을 띄울 수 있습니다.

### 1️⃣ 타겟 서버 띄우기 (Docker 환경 준비)
```bash
# 서버 폴더로 이동합니다.
cd 01.TestServer

# 가상 서버(Docker)들을 백그라운드에서 실행합니다.
docker compose up -d

# 실행이 완료된 후 원래 폴더로 돌아옵니다.
cd ..
```

---

### 2️⃣ 시나리오 선택 및 실행하기
이 프로젝트는 **두 가지 서로 다른 해킹 시나리오**를 제공합니다. 원하시는 스크립트를 파이썬으로 실행하세요!

<details open>
<summary><b>🎬 [시나리오 A] 외부 공격자 시나리오 (run.py)</b></summary>

외부 인터넷에 노출된 취약점(Spring4Shell)을 뚫고 들어와, 내부 시스템을 차례대로 장악해 나가는 정석적인 해커의 모습을 보여줍니다.
```bash
python3 run.py
```
</details>

<details open>
<summary><b>🕵️ [시나리오 B] 내부자 위협 시나리오 (sub_run.py)</b></summary>

취약점 해킹 기술 없이, 단지 사내망에 접속할 수 있는 '불만 품은 직원'이 관리자의 설정 실수를 이용해 회사 기밀을 빼내는 무서운 현실을 보여줍니다.
```bash
python3 sub_run.py
```
</details>

<br>

> [!TIP]
> 🎉 **자동 보고서 생성! (최신 렌더링 패치 완료)**
> 스크립트 실행이 끝나면 `03.FinalReport` 폴더에 **시각화된 HTML 결과 보고서**가 생성됩니다. 
> 
> *✨ 새로운 기능: `curl` 같은 외부 프로그램 없이 순수 패킷 통신(TCP Ping)으로 내부망을 정찰하며, 브라우저 오류를 유발하는 웹쉘 특수문자를 완벽히 예방(HTML Escape 처리)하여 1단계부터 6단계까지 잘림 없이 스무스하게 렌더링됩니다!*

<br>

---

<br>

## 🔎 두 시나리오는 무엇이 다를까요?

보안 입문자분들을 위해 두 가지 핵심 관점을 비교했습니다.

| 특징 | 🔴 외부 공격자 (run.py) | 🟠 내부자 위협 (sub_run.py) |
|:---:|:---|:---|
| **역할극** | 인터넷 밖의 외부 해커 | 인증받은 내부망 직원 |
| **핵심 무기** | `CVE 제로데이 취약점` (소프트웨어 버그) | `Misconfiguration` (관리자의 설정 오류) |
| **방어 난이도**| 패치(업데이트)를 잘 하면 막을 수 있음 | 권한 관리와 설정이 잘못되면 막기 매우 힘듦 |
| **주요 목표** | Spring 웹쉘 배포 → TeamCity 해킹 → DB 탈취 | 망 분리 우회 → NAS 도면 유출 → CI/CD 백도어 삽입 |
| **생성 보고서**| `main_scenario_report_*.html` | `sub_scenario_insider_threat_*.html` |

<br>

---

<br>

## 📁 템플릿 폴더 구조 안내

코드가 어떻게 나뉘어 있는지 궁금하신가요? 

```text
CVE-2022-22965/
│
├── README.md                      # 🌟 이 가이드 문서
├── run.py                         # 🚀 외부 공격자 시나리오 실행기
├── sub_run.py                     # 🕵️ 내부자 위협 시나리오 실행기
│
├── 01.TestServer/                 # 🐳 안전하게 해킹해 볼 수 있는 가상 서버들 (Docker)
│   └── docker-compose.yml         #    (Spring 웹, 내부 DB, CI/CD, 사내 NAS 등)
│
├── 02.AttackScripts/              # ⚙️ 실제 해킹 기술이 담긴 코드 (고급 개발자용)
│   ├── stage1~3 레이어 파일...    #    객체지향(SOLID)과 클린 아키텍처로 짜여진 공격 모듈
│   └── tests/                     #    ✅ 코드가 잘 도는지 확인하는 유닛 테스트 (총 44개)
│
├── 03.FinalReport/                # 📊 예쁜 HTML 결과 보고서가 저장되는 곳
│
└── 04.SubScenarios/               # 🔥 내부자 위협에 대한 상세 가이드 및 테스트 코드
```

<br>

---

<br>

## 🛡️ 우리는 어떻게 방어해야 할까요? (Mitigation)

공격을 이해했다면 방어할 줄도 알아야 합니다. 아래의 수칙을 지켜 시스템을 보호하세요!

1. 🔴 **라이브러리 패치 (가장 중요)**
   - Spring Framework 버전을 최신으로 업그레이드 하세요. (5.3.18 이상)
2. 🔴 **비밀번호 하드코딩 금지**
   - 개발 소스코드나 `application.properties`에 데이터베이스 비밀번호를 평문으로 적어두지 마세요.
3. 🟠 **내부망 통합 관리의 위험성**
   - 내부 시스템(CI/CD, NAS, DB)이라고 해서 비밀번호를 `test/test` 처럼 대충 지으면 내부자에게 털립니다.
4. 🟡 **망 분리 및 권한 축소**
   - 일반 직원이 개발용 핵심 데이터베이스나 빌드 서버(TeamCity)에 함부로 접근하지 못하도록 네트워크(ACL)를 차단하세요.

<br>

---

<div align="center">
  <sub>🛡️ Created with Team EQST & AI Assistant | 누구나 쉽게 시작하는 보안 자동화 플랫폼</sub>
</div>

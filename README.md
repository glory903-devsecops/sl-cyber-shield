<div align="center">
 
# 🛡️ sl-cyber-shield (SCS-EP)
### 🎯 모의해킹 자동화 및 포스트 익스플로잇 관제 플랫폼
**SL Factory Innovation Team | Cyber Security Strategy**

![Spring](https://img.shields.io/badge/Spring_Framework-6DB33F?style=for-the-badge&logo=spring&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python_3-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SL-Blue](https://img.shields.io/badge/CI_Color-%23151C5A?style=for-the-badge)

**에스엘(SL) 스마트 팩토리 보안 강화를 위한 자동화된 취약점 분석 및 위협 시뮬레이션 체계**

<br>

> 💡 **본 플랫폼의 가치**
> 이 프로젝트는 단순한 해킹 툴이 아닙니다. **에스엘(SL)의 SOC(Security Operations Center) 관점**에서 최신 제로데이 취약점(Spring4Shell)과 내부자 위협이 실제 공장 네트워크(OT/IT)에 어떤 치명적인 영향을 주는지 자동으로 시뮬레이션하고 시각화된 리포트를 제공합니다.
> 
> 📊 **[실시간 보안 보고서 보기 (GitHub Pages)](https://glory903-devsecops.github.io/sl-cyber-shield/)**

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

## 🌐 시각적 공격 여정 (Visual Attack Journey)

전문가가 아닌 사람들에게도 보안 위협의 심각성을 전달하기 위해, 웹 UI 상에서의 공격 경로를 시각화했습니다.

````carousel
![정상적인 로그인 페이지](/Users/glory1994/.gemini/antigravity/brain/63bf562f-fb13-4dac-9ed2-38cbddacb25c/initial_login_state_png_1774680394803.png)
<!-- slide -->
![취약점 공격 성공 (RCE 웹쉘)](/Users/glory1994/.gemini/antigravity/brain/63bf562f-fb13-4dac-9ed2-38cbddacb25c/attack_success_poc_1774680645916.png)
<!-- slide -->
![내부망 내부 도구 노출 (Gitea)](/Users/glory1994/.gemini/antigravity/brain/63bf562f-fb13-4dac-9ed2-38cbddacb25c/gitea_main_page_1774680068622.png)
<!-- slide -->
![CI/CD 빌드 시스템 장악 (TeamCity)](/Users/glory1994/.gemini/antigravity/brain/63bf562f-fb13-4dac-9ed2-38cbddacb25c/teamcity_internal_server_png_1774680494775.png)
````

> [!IMPORTANT]
> **심각성 요약:** 위 이미지는 외부 로그인 페이지의 취약점 하나가 어떻게 서버 전체의 통제권(`root` 권한) 상실로 이어지고, 나아가 사내 모든 소스코드(Gitea)와 빌드 시스템(TeamCity)까지 노출시키는지 실시간으로 보여줍니다.

<br>

---

## 🚀 아주 쉬운 시작 가이드 (Quick Start)
## 🚀 Quick Start (One-Click Simulator)

SL Cyber-Shield는 복잡한 시뮬레이션 환경을 한 번에 제어할 수 있는 통합 러너를 제공합니다.

### 1. 통합 러너 실행
```bash
python3 start_shield.py
```

### 2. 메뉴 구성
- **[Option 1] Main Exploit Chain (run.py)**: 외부 공격자 시나리오 (Spring4Shell -> TeamCity -> NAS)
- **[Option 2] Insider Threat (sub_run.py)**: 내부자 위협 시뮬레이션 (Recon -> Credential -> Supply Chain Attack)
- **[Option 3/4] Infrastructure Control**: Docker Compose를 통한 테스트 서버 부팅 및 종료

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
sl-cyber-shield/
│
├── README.md                      # 🌟 이 가이드 문서 (SL SCS-EP 통합 가이드)
├── start_shield.py                # 🕹️ 통합 원클릭 시뮬레이터 (추천 시작점)
├── run.py                         # 🚀 외부 공격자 시나리오 실행기 (Main Chain)
├── sub_run.py                     # 🕵️ 내부자 위협 시나리오 실행기 (Sub Scenarios)
│
├── 01.TestServer/                 # 🐳 안전하게 해킹해 볼 수 있는 가상 서버들 (Docker)
│   └── docker-compose.yml         #    (Spring 웹, 내부 DB, CI/CD, 사내 NAS 등)
│
├── 02.AttackScripts/              # ⚙️ 실제 해킹 기술이 담긴 코드 (고급 개발자용)
│   ├── stage1_dropper.py          #    Spring4Shell 취약점 공격 모듈
│   ├── stage2_uploader.py         #    세컨드 스테이지 웹쉘 업로드 모듈
│   ├── stage3_lateral_movement.py #    내부망 횡적 이동 및 타겟 시스템 장악 모듈
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

<br>

## 📚 주요 활용 보안 취약점 (Key CVEs)

본 시뮬레이터는 실제 산업 현장에서 발생할 수 있는 다음 3가지 핵심 취약점을 연쇄적으로 활용하여 **킬 체인(Kill Chain)**을 완성합니다.

### 1️⃣ [Spring4Shell] CVE-2022-22965
- **위험도**: <img src="https://img.shields.io/badge/CRITICAL-9.8-red?style=flat-square" />
- **기술적 상세**: Spring Framework의 `DataBinder` 클래스가 클래스 로더 파라미터(Classloader parameters)를 노출하는 결함을 악용합니다. 공격자는 HTTP 파라미터를 조작하여 Tomcat의 로그 설정(`AccessLogValve`)을 강제로 변경하고, 서버에 임의의 `.jsp` 파일(웹쉘)을 생성하여 **원격 코드 실행(RCE)** 권한을 획득합니다.
- **역할**: 외부 공격자의 **최초 침투 경로(Initial Access)** 및 통제권 탈취.
- **참조**: [MITRE CVE-2022-22965](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2022-22965)

### 2️⃣ [TeamCity Auth Bypass] CVE-2024-27198
- **위험도**: <img src="https://img.shields.io/badge/CRITICAL-9.8-red?style=flat-square" />
- **기술적 상세**: TeamCity 웹 서버의 인증 처리 로직을 우회하여 인증되지 않은 사용자가 관리자 엔드포인트에 접근할 수 있게 합니다. 이를 통해 공격자는 관리자 계정을 생성하거나 빌드 환경을 마음대로 조작할 수 있습니다.
- **역할**: 내부망에서의 **권한 상승(Privilege Escalation)** 및 소프트웨어 공급망(Supply Chain) 장악.
- **참조**: [JetBrains Security Bulletin](https://blog.jetbrains.com/teamcity/2024/03/additional-critical-security-issues-affecting-teamcity-on-premises-cve-2024-27198-and-cve-2024-27199-update/)

### 3️⃣ [Struts2 File Upload] CVE-2023-50164
- **위험도**: <img src="https://img.shields.io/badge/HIGH-7.5-orange?style=flat-square" />
- **기술적 상세**: Apache Struts2의 파일 업로드 매개변수에 대한 입력 검증 미흡으로, 공격자가 <b>경로 트래버설(Path Traversal)</b>을 통해 실행 권한이 있는 경로에 악성 파일을 업로드할 수 있습니다.
- **역할**: 내부망 **횡적 이동(Lateral Movement)** 단계에서 격리된 데이터베이스 서버를 장악.
- **참조**: [Apache Security Docs](https://struts.apache.org/announce-2023#a20231207-1)

<br>

---

<div align="center">
  <sub>🛡️ Created by SL Factory Innovation Team & AI Assistant | 에스엘 디지털 트러스트 인프라 보안 솔루션</sub>
</div>

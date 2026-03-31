<div align="center">

# SL Cyber-Shield: 스마트 팩토리 위협 시뮬레이션 플랫폼

### 모의해킹 자동화 및 포스트 익스플로잇 관제 시스템

![Spring](https://img.shields.io/badge/Spring-🌱-green) ![Docker](https://img.shields.io/badge/Docker-🐳-blue) ![Python](https://img.shields.io/badge/Python-🐍-yellow) ![SL-Blue](https://img.shields.io/badge/SL--Blue-blue)

[실시간 보안 보고서 보기 (GitHub Pages) — 웹 포털에서 대화형 보고서 확인하기](https://github.com/glory903-devsecops/sl-cyber-shield?tab=readme-ov-file)

에스엘(SL) 스마트 팩토리 보안 강화를 위한 최신 제로데이(Spring4Shell) 및 공급망 공격 통합 시뮬레이션 체계입니다.

</div>

---

## ⚡ Quick Start
터미널에서 단 몇 줄의 명령만으로 실제 제조업 타겟 시스템에 대한 보안 시뮬레이션을 시작할 수 있습니다.

![Quick start: run script in terminal](./docs/assets/terminal_hero.png)
*(플레이스홀더 — 실제 스크린샷으로 교체 요망)*

```bash
# 1. 저장소 복제
git clone https://github.com/glory903-devsecops/sl-cyber-shield.git
cd sl-cyber-shield

# 2. 통합 시뮬레이터 실행
# 확인 필요: 루트 폴더에 run.sh가 있다면 ./run.sh를 사용하고, 없을 경우 아래 명령을 실행하십시오.
python3 start_shield.py # 또는 docker-compose up -d
```

---

## 🎬 시각적 공격 여정 (Visual Attack Journey)
전문가가 아닌 사람들에게도 보안 위협의 심각성을 전달하기 위해, 웹 UI 상에서의 공격 경로를 시각화했습니다.

### 1단계: 정찰 및 대상 식별 (Initial Recognition)
> 평범해 보이는 제조업 사내 로그인 페이지입니다. 백그라운드에서는 클래스 데이터 바인딩 취약점이 해결되지 않은 채 구동되고 있습니다.
> 
> <img src="./docs/assets/step01_recon_v2.png" width="800" alt="Login page - vulnerable class data binding">

### 2단계: 핵심 침투 및 데이터 유출
2단계에 나오는 내용에 일부 이미지만 보여집니다. 자세한 분석은 [상세 보고서]를 참조하십시오.

<div align="center">
  <img src="./docs/assets/step02_audit_v2.png" width="400" alt="Step 2-1: Audit">
  <img src="./docs/assets/step03_rce_v2.webp" width="400" alt="Step 2-2: RCE">
</div>

---

## 🛡️ 주요 시뮬레이션 시나리오 (Big 3)
`start_shield.py`를 통해 제어되는 세 가지 핵심 위협 모델입니다.

| 시나리오 | 핵심 취약점 (CVE) | 시뮬레이션 목적 |
|:---:|:---|:---|
| **Main Scenario** | Spring4Shell (CVE-2022-22965) | 외부 비인가 사용자의 원격 코드 실행 재현 |
| **Insider Threat** | Credential Leakage | 내부 망 수평 이동 탐지능력 강화 |
| **Advanced Bypass** | Patch Bypass | 보안 설정의 논리적 허점 분석 |

---

> [!CAUTION]
> **본 프로젝트는 교육 및 연구를 목적으로 격리된 Docker 환경에서 구동됩니다.**

<div align="center">
  <sub>에스엘 디지털 트러스트 인프라 보안 솔루션</sub>
</div>

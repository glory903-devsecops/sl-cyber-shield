<div align="center">
  
# 💣 Sub-Scenarios: Misconfiguration Attacks
**실무 APT(지능형 지속 위협) 해킹 기법 증명 가이드**

![Lateral Movement](https://img.shields.io/badge/Lateral_Movement-8A2BE2?style=for-the-badge&logo=hackthebox&logoColor=white)
![Misconfiguration](https://img.shields.io/badge/Security_Misconfiguration-ff69b4?style=for-the-badge&logo=owasp&logoColor=white)
![Privilege Escalation](https://img.shields.io/badge/Privilege_Escalation-FFA500?style=for-the-badge&logo=linux&logoColor=white)

---
</div>

> [!CAUTION]
> 본 디렉터리는 기존의 "CVE 취약점 체이닝" 공격(시나리오 1~3)과 대비되는 **"인프라 설정 오류(Misconfiguration)"** 파급을 조명합니다.
> 해커는 복잡한 제로데이를 찾지 않고 "관리자의 실시"나 "잘못된 인프라 설정"을 집중적으로 파고듭니다.

---

## 💥 3대 신규 침투 시나리오

<details open>
<summary><b>🔥 시나리오 A: SSH 자격 증명 재사용 (Direct Pivoting)</b></summary>

> 기존에 Struts 서버로 넘어가기 위해 TeamCity 취약점을 악용했지만, 사실 `spring`과 `struts` 컨테이너 모두 `SSH_PASSWORD: testtest`라는 동일한 비밀번호를 사용하고 있었습니다. 
*   **공격 방식**: 웹쉘 RCE를 통해 환경변수(`env`)에서 비밀번호를 탈취한 후 곧바로 SSH를 타고 인접 서버로 넘어가는 치명적이고 직관적인 공격입니다.
*   **보안 교훈**: 컨테이너 간 동일한 자격 증명을 템플릿처럼 복사/붙여넣기 할 때 발생하는 [Credential Reuse]의 위험성.
</details>

<details open>
<summary><b>🖥️ 시나리오 B: Employee Desktop(VNC) 하이재킹</b></summary>

> 사내망에 구동 중인 직원의 원격 데스크톱 컨테이너(`employee-desktop`)가 `password`라는 매우 취약한 기본 비밀번호를 사용하고 있습니다. 
*   **공격 방식**: 공격자는 Chisel 등의 프록시 터널을 뚫어 실제 직원의 마우스와 화면을 장악하고, 연동되어 있는 사내 NAS 서버 내 설계도를 시각적(GUI)으로 유유히 빼돌립니다.
*   **보안 교훈**: 내부망에 방치된 GUI 도구(VNC/RDP)에 대한 접근 통제 부재 및 취약한 기본 패스워드 사용의 위험성.
</details>

<details open>
<summary><b>📦 시나리오 C: Gitea 사내 소스코드 저장소 HTTP 직접 강탈</b></summary>

> 애플리케이션 소스코드 형상관리 서버(Gitea)에 보관된 기업 핵심 자산을 탈취합니다.
*   **공격 방식**: 웹쉘 내부에서 과거 개발자가 남긴 `git clone` 기록(`.bash_history`)이나, 메모리에 남겨진 브라우저 쿠키/토큰을 찾아내어 HTTP 프로토콜만으로 전체 소스코드를 조용히 로컬로 다운로드합니다.
*   **보안 교훈**: 개발망이나 테스트 환경에서 권한이 과도하게 부여된 PAT(Personal Access Token)가 남겨지는 [Credential Leakage]의 파급력.
</details>

---

## 🚀 실행 가이드

본 서브 시나리오들을 통합 실행 하려면, 위치 이동(`cd`) 없이 프로젝트 최상위 디렉터리(`../`)에서 아래의 스크립트를 바로 실행하세요.

```bash
# 서브 시나리오 자동 통합 공격 스크립트 실행
python3 sub_run.py
```

> [!TIP]
> `sub_run.py`는 `run.py`와 완벽히 분리되어 동작하지만, 내부적으로는 `02.AttackScripts`의 코어 엔진(Clean Architecture) 레이어를 동일하게 공유하며 실행됩니다.

---

<div align="center">
  <sub>Created with 💻 Team EQST & AI Assistant</sub>
</div>

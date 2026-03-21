<div align="center">

# ⚙️ 02.AttackScripts

**Spring4Shell (CVE-2022-22965) 공격 파이프라인 — 세부 모듈 레이어**

![SOLID](https://img.shields.io/badge/SOLID_Principles-6366f1?style=for-the-badge&logo=solid&logoColor=white)
![Clean Architecture](https://img.shields.io/badge/Clean_Architecture-14b8a6?style=for-the-badge&logo=databricks&logoColor=white)
![Python](https://img.shields.io/badge/Python_3-3776AB?style=for-the-badge&logo=python&logoColor=white)

**실무 모의해킹 엔지니어의 관점으로 작성된 프로덕션 수준의 공격 자동화 코드입니다.**

---
</div>

## 🏗️ Clean Architecture 계층 구조

본 모듈은 실제 현업 소프트웨어 공학의 **Clean Architecture**를 공격 스크립트에도 동일하게 적용합니다. Bob Martin의 의존성 규칙에 따라 안쪽 레이어(Domain)는 바깥 레이어(Infrastructure)를 절대 알지 못합니다.

```
┌─────────────────────────────────────────────┐
│            Frameworks & Drivers              │
│  LocalFileServerAdapter, Stage1CommandAdapter│  ← 실제 HTTP/OS 호출
├─────────────────────────────────────────────┤
│           Interface Adapters                 │
│  Spring4ShellPayloadGenerator, Controllers  │  ← 데이터 변환
├─────────────────────────────────────────────┤
│              Use Cases                       │
│  Stage2UploadUseCase, ExploitController     │  ← 비즈니스 로직
├─────────────────────────────────────────────┤
│            Entities (Domain)                 │
│  ExploitConfig, UploadConfig                │  ← 순수 데이터 모델
└─────────────────────────────────────────────┘
```

> [!NOTE]
> 각 계층은 **단방향 의존성**만 허용합니다. Infrastructure는 Use Case에 의존하지만, Use Case는 Infrastructure를 모릅니다. 이 덕분에 단위 테스트에서 Infrastructure를 Mock으로 완전 교체할 수 있습니다.

---

## 📂 모듈 설명

### `stage1_dropper.py` — RCE 취약점 트리거

> Spring Framework의 Data Binding 취약점(CVE-2022-22965)을 이용해 Tomcat AccessLogValve를 조작, 웹쉘(`.jsp`) 파일을 서버에 기록합니다.

| 컴포넌트 | 역할 | SOLID 원칙 |
|:---|:---|:---:|
| `ExploitConfig` | 공격 설정값 보관 (타겟 URL, 파일명) | SRP |
| `PayloadGeneratorPort` | 페이로드 생성 인터페이스 정의 | ISP |
| `Spring4ShellPayloadGenerator` | CVE-2022-22965 특화 페이로드 구현 | OCP, LSP |
| `ExploitController` | HTTP POST 전송 오케스트레이터 | SRP, DIP |

**핵심 공격 메커니즘:**
```
POST /spring-form/login HTTP/1.1
class.module.classLoader.resources.context.parent.pipeline.first.pattern = <%JSP코드%>
class.module.classLoader.resources.context.parent.pipeline.first.suffix  = .jsp
→ Tomcat AccessLogValve가 로그 파일로 JSP 웹쉘을 webapps/ROOT에 기록
```

---

### `stage2_uploader.py` — 2단계 웹쉘 배포

> Stage 1 웹쉘의 RCE를 활용해 고기능 웹쉘(`health_check.jsp`)을 내려받아 배포합니다. 공격자 PC를 임시 파일 서버로 활용하는 "Living off the Land" 기법입니다.

| 컴포넌트 | 역할 | SOLID 원칙 |
|:---|:---|:---:|
| `UploadConfig` | Stage2 배포 설정값 보관 | SRP |
| `FileServerPort (ABC)` | 파일 서버 시작/종료 인터페이스 | ISP |
| `Stage1CommandPort (ABC)` | RCE 명령 실행 인터페이스 | ISP |
| `LocalFileServerAdapter` | Python 내장 HTTP 서버로 임시 파일 배포 | OCP, DIP |
| `Stage1CommandAdapter` | Stage1 쉘에 명령 전달 | LSP |
| `Stage2UploadUseCase` | Stage1→Stage2 전체 배포 오케스트레이터 | SRP, DIP |

---

### `stage3_lateral_movement.py` — 횡적 이동 (Lateral Movement)

> Stage 2 웹쉘을 발판으로 내부망의 다른 서비스(TeamCity, Struts2, NAS)를 연계 공격합니다.

| 시나리오 | 공격 대상 | 기법 |
|:---|:---|:---|
| **Scenario A** | TeamCity CI/CD | API 토큰 탈취 → 빌드 파이프라인 장악 |
| **Scenario B** | Struts2 웹 서버 | CVE-2017-5638 체이닝 → 직원 DB 접근 |
| **Scenario C** | NAS SMB 파일 서버 | JNDI/JCIFS 활용 → 제품 설계도 시뮬레이션 |

---

### `health_check.jsp` — Stage 2 웹쉘

> 실무 수준의 Clean Architecture가 적용된 교육용 JSP 웹쉘. 인증 레이어(`pwd` 파라미터), 비즈니스 로직(`WebShellUseCase`), OS 어댑터(`SystemCommandAdapter`)로 계층이 분리되어 있습니다.

```bash
# 사용 방법 (배포 완료 후)
curl "http://localhost:8011/health_check.jsp?pwd=glory&cmd=id"
# → uid=0(root) gid=0(root) groups=0(root)
```

---

## ✅ 유닛 테스트 실행

```bash
# 프로젝트 루트에서 실행
python3 -m unittest discover -s 02.AttackScripts -p "test_*.py" -v
```

**테스트 구성 (총 20개):**

| 테스트 클래스 | 검증 대상 | 테스트 수 |
|:---|:---|:---:|
| `TestExploitConfig` | Entity 기본값 및 커스텀값 설정 | 2 |
| `TestSpring4ShellPayloadGenerator` | LSP 준수, 페이로드 구조 검증 | 6 |
| `TestExploitController` | HTTP 응답 처리 (Mock 격리) | 4 |
| `TestUploadConfig` | 공격자 URL 자동 설정 로직 | 4 |
| `TestStage2UploadUseCase` | Use Case 오케스트레이션 (Port Mock) | 4 |

**SOLID 원칙이 테스트에서 어떻게 드러나는가:**

- **SRP** — 테스트 클래스 하나가 컴포넌트 하나만 검증
- **OCP** — Mock 어댑터로 외부 의존성 교체 (코드 변경 없이 테스트 확장)
- **LSP** — `MockExecutor`가 `Stage1CommandPort`를 완전히 대체
- **ISP** — Mock은 필요한 인터페이스 메서드만 구현
- **DIP** — 테스트가 구체 클래스가 아닌 포트(인터페이스)에 의존

---

<div align="center">
  <sub>SOLID + Clean Architecture 적용 | Educational Use Only</sub>
</div>

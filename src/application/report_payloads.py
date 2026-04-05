from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def _artifact_items(report_filename: str) -> list[dict[str, str]]:
    stem = Path(report_filename).stem
    return [
        {"label": "Primary Artifact", "value": f"03.FinalReport/{report_filename}"},
        {"label": "Structured Source", "value": f"03.FinalReport/data/{stem}.json"},
        {"label": "Printable Snapshot", "value": f"03.FinalReport/{stem}.pdf"},
    ]


def build_main_report_payload(
    *,
    report_filename: str,
    current_time: str,
    target_url: str,
    stage2_url: str,
    all_pass: bool,
    labels: dict[str, str],
    step_descriptions: dict[str, str],
    results: dict[str, bool],
    details: dict[str, Any],
    run_mode: str,
    db_dump_result: str,
    step8_result: str,
    step9_result: str,
) -> dict[str, Any]:
    severity_map = {
        "step1": "high",
        "step2": "medium",
        "step3": "high",
        "step4": "critical",
        "step5": "critical",
        "step6": "critical",
        "step7": "critical",
        "step8": "critical",
        "step9": "critical",
    }

    structured_sections: list[dict[str, Any]] = []
    for key, label in labels.items():
        evidence: dict[str, str] = {"kind": "text", "content": ""}
        if key in {"step1", "step2", "step3", "step4", "step5"}:
            evidence = {"kind": "text", "content": str(details.get(key, ""))}
        elif key == "step6":
            detail = details.get("step6", {})
            credentials = detail.get("credentials", {})
            evidence = {
                "kind": "html",
                "content": f"""
<p><strong>발견된 DB 클라이언트:</strong> {escape(', '.join(detail.get('clients', [])) or '없음')}</p>
<p><strong>설정 파일:</strong> <code>{escape(detail.get('config_file', ''))}</code></p>
<ul>
  <li>DB URL: <code>{escape(credentials.get('url', ''))}</code></li>
  <li>USER: <code>{escape(credentials.get('user', ''))}</code></li>
  <li>PASS: <code>{escape(credentials.get('pass', ''))}</code></li>
</ul>
<pre>{escape(detail.get('raw_props', ''))}</pre>
""".strip(),
            }
        elif key == "step7":
            evidence = {
                "kind": "text",
                "content": f"Execution Mode: {run_mode or '미실행'}\n\n{db_dump_result or '덤프 결과 없음'}",
            }
        elif key == "step8":
            evidence = {"kind": "text", "content": step8_result or "실행 결과 없음"}
        elif key == "step9":
            evidence = {"kind": "text", "content": step9_result or "실행 결과 없음"}

        structured_sections.append(
            {
                "id": key,
                "step": label.split("|")[0].strip(),
                "title": label.split("|", 1)[1].strip() if "|" in label else label,
                "description": step_descriptions.get(key, ""),
                "status": "success" if results.get(key, False) else "blocked",
                "severity": severity_map.get(key, "medium"),
                "evidence": evidence,
            }
        )

    return {
        "reportKind": "main",
        "slug": Path(report_filename).stem,
        "meta": {
            "title": "SL Cyber-Shield Main Exploit Chain",
            "subtitle": "Spring4Shell 초기 침투부터 내부 자산 접근과 횡적 이동까지를 구조화 데이터 기반 정적 보고서로 변환한 산출물입니다.",
            "badge": "Structured static export",
            "generatedAt": current_time,
            "classification": "Demo-safe HTML + PDF bundle",
        },
        "summary": {
            "overview": "제출용 데모 링크에 올리는 보고서는 런타임 의존 없이 고정 산출물이어야 합니다. 이 보고서는 기존 시뮬레이션 결과를 JSON으로 구조화한 뒤 React 정적 렌더링과 PDF 생성으로 문서화합니다.",
            "items": [
                {"label": "Target Endpoint", "value": target_url},
                {"label": "Stage 2 Shell", "value": stage2_url},
                {"label": "Overall Status", "value": "Exploitation Success" if all_pass else "Blocked / Incomplete"},
                {"label": "Bundle Output", "value": "JSON + HTML + PDF"},
            ],
        },
        "artifacts": _artifact_items(report_filename),
        "sections": structured_sections,
        "footer": {
            "body": "SL Factory Innovation Team automated exploit report bundle.",
            "note": "Legacy HTML output is kept as a fallback until the hybrid pipeline fully replaces it.",
        },
    }


def build_insider_report_payload(
    *,
    report_filename: str,
    current_time: str,
    results: dict[str, bool],
    details: dict[str, str],
    phase_meta: list[tuple[str, str, str, str, str, str, str, str]],
) -> dict[str, Any]:
    return {
        "reportKind": "insider",
        "slug": Path(report_filename).stem,
        "meta": {
            "title": "SL Cyber-Shield Insider Threat Audit",
            "subtitle": "내부 직원 권한 악용 시나리오를 구조화된 데이터와 정적 렌더링 결과물로 보존하는 보고서입니다.",
            "badge": "Hybrid fixed artifact",
            "generatedAt": current_time,
            "classification": "Static HTML and printable PDF",
        },
        "summary": {
            "overview": "기존 내부자 위협 시나리오 결과를 JSON으로 보존하고, React 정적 렌더러로 HTML과 PDF를 동시에 생성해 제출용 증적과 보관용 문서를 같은 basename으로 유지합니다.",
            "items": [
                {"label": "Role Context", "value": "내부 개발자 / 정상 업무 권한 보유자"},
                {"label": "Initial Footprint", "value": "health_check.jsp 거점 웹쉘 확보"},
                {"label": "Simulation Scope", "value": "6 Phase - Recon to CI/CD Persistence"},
                {"label": "Audit Verdict", "value": "전체 시나리오 장악 성공" if all(results.values()) else "일부 단계 차단됨"},
            ],
        },
        "artifacts": _artifact_items(report_filename),
        "sections": [
            {
                "id": key,
                "step": label,
                "title": title,
                "description": description,
                "status": "success" if results.get(key, False) else "blocked",
                "severity": risk_level.lower(),
                "evidence": {
                    "kind": "html",
                    "content": details.get(key, "결과 없음"),
                },
            }
            for key, label, title, risk_level, description, _color, _bg_color, _border_color in phase_meta
        ],
        "footer": {
            "body": "SL Factory Innovation Team insider threat audit bundle.",
            "note": "The structured JSON payload is preserved alongside the fixed HTML and PDF outputs.",
        },
    }


def build_advanced_report_payload(
    *,
    report_filename: str,
    current_time: str,
) -> dict[str, Any]:
    return {
        "reportKind": "advanced",
        "slug": Path(report_filename).stem,
        "meta": {
            "title": "SL Cyber-Shield Advanced Bypass Scenario",
            "subtitle": "워터홀 공격과 패치 우회 시나리오를 정적 HTML/PDF로 고정하는 구조화 보고서입니다.",
            "badge": "Advanced bypass artifact",
            "generatedAt": current_time,
            "classification": "Static export bundle",
        },
        "summary": {
            "overview": "Scenario 3는 관리 페이지 유도, 다형성 페이로드, 보완책 우회, 민감 정보 노출 흐름을 정적인 제출 산출물로 재구성합니다.",
            "items": [
                {"label": "Scenario", "value": "Advanced Bypass & Watering Hole"},
                {"label": "Phases", "value": "4-stage simulation"},
                {"label": "Primary Output", "value": report_filename},
                {"label": "Bundle Output", "value": "JSON + HTML + PDF"},
            ],
        },
        "artifacts": _artifact_items(report_filename),
        "sections": [
            {
                "id": "phase1",
                "step": "Phase 1",
                "title": "Watering Hole Exposure",
                "description": "운영자 대상 긴급 패치 안내 모달을 통한 유입 경로를 설명합니다.",
                "status": "success",
                "severity": "high",
                "evidence": {
                    "kind": "text",
                    "content": "Admin Page XSS Injection: CVE-2022-22965 urgent patch advisory modal deployed.",
                },
            },
            {
                "id": "phase2",
                "step": "Phase 2",
                "title": "Polymorphic Payload",
                "description": "시그니처 기반 WAF를 우회하기 위한 변형 페이로드 사용 흔적입니다.",
                "status": "success",
                "severity": "critical",
                "evidence": {
                    "kind": "text",
                    "content": "Payload: Class.*, *.class.* variations detected.",
                },
            },
            {
                "id": "phase3",
                "step": "Phase 3",
                "title": "Mitigation Bypass",
                "description": "setDisallowedFields 기반 완화책을 case-sensitivity 취약점으로 우회합니다.",
                "status": "success",
                "severity": "critical",
                "evidence": {
                    "kind": "text",
                    "content": "Case-sensitive payload dropped webshell at /ROOT/patch_status.jsp",
                },
            },
            {
                "id": "phase4",
                "step": "Phase 4",
                "title": "Automatic Data Extraction",
                "description": "Spring Actuator 노출 지점에서 환경 변수와 클라우드 자격 증명을 스캔합니다.",
                "status": "success",
                "severity": "critical",
                "evidence": {
                    "kind": "text",
                    "content": "Found: AWS_SECRET_ACCESS_KEY=**** (masked in static report)",
                },
            },
        ],
        "footer": {
            "body": "SL Factory Innovation Team advanced bypass bundle.",
            "note": "The legacy HTML file remains a fallback if the React static renderer is unavailable.",
        },
    }

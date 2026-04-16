from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, Mapping


@dataclass(frozen=True)
class ReportBundleResult:
    success: bool
    json_path: Path
    html_path: Path
    pdf_path: Path
    manifest_path: Path
    stdout: str = ""
    stderr: str = ""


def _load_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        return {"version": 1, "updatedAt": "", "reports": []}

    with manifest_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _sort_reports(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        reports,
        key=lambda item: (
            item.get("generatedAt", ""),
            item.get("slug", ""),
        ),
        reverse=True,
    )


def _update_manifest(
    manifest_path: Path,
    payload: Mapping[str, Any],
    *,
    stem: str,
    report_filename: str,
    json_relative_path: str,
    pdf_filename: str,
    renderer_succeeded: bool,
) -> None:
    manifest = _load_manifest(manifest_path)

    entry = {
        "slug": stem,
        "kind": payload.get("reportKind", "report"),
        "title": payload.get("meta", {}).get("title", stem),
        "subtitle": payload.get("meta", {}).get("subtitle", ""),
        "generatedAt": payload.get("meta", {}).get("generatedAt", ""),
        "htmlFile": report_filename,
        "jsonFile": json_relative_path,
        "pdfFile": pdf_filename,
        "hasPdf": (manifest_path.parent.parent / pdf_filename).exists(),
        "renderer": "react-static" if renderer_succeeded else "legacy-html-fallback",
    }

    reports = [
        existing
        for existing in manifest.get("reports", [])
        if existing.get("slug") != stem
    ]
    reports.append(entry)

    manifest["version"] = 1
    manifest["updatedAt"] = payload.get("meta", {}).get("generatedAt", "")
    manifest["reports"] = _sort_reports(reports)

    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)


def export_report_bundle(
    project_root: Path | str,
    report_filename: str,
    payload: Mapping[str, Any],
) -> ReportBundleResult:
    root = Path(project_root)
    report_dir = root / "03.FinalReport"
    report_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(report_filename).stem
    json_dir = report_dir / "data"
    json_dir.mkdir(parents=True, exist_ok=True)

    json_path = json_dir / f"{stem}.json"
    html_path = report_dir / report_filename
    pdf_path = report_dir / f"{stem}.pdf"
    manifest_path = json_dir / "reports-manifest.json"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    node_binary = shutil.which("node")
    renderer_script = root / "reporting" / "scripts" / "build-report.mjs"
    if not node_binary or not renderer_script.exists():
        _update_manifest(
            manifest_path,
            payload,
            stem=stem,
            report_filename=report_filename,
            json_relative_path=f"data/{json_path.name}",
            pdf_filename=pdf_path.name,
            renderer_succeeded=False,
        )
        return ReportBundleResult(
            success=False,
            json_path=json_path,
            html_path=html_path,
            pdf_path=pdf_path,
            manifest_path=manifest_path,
            stderr="Node.js renderer is not available.",
        )

    completed = subprocess.run(
        [
            node_binary,
            str(renderer_script),
            "--input",
            str(json_path),
            "--output-dir",
            str(report_dir),
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )

    _update_manifest(
        manifest_path,
        payload,
        stem=stem,
        report_filename=report_filename,
        json_relative_path=f"data/{json_path.name}",
        pdf_filename=pdf_path.name,
        renderer_succeeded=completed.returncode == 0,
    )

    return ReportBundleResult(
        success=completed.returncode == 0,
        json_path=json_path,
        html_path=html_path,
        pdf_path=pdf_path,
        manifest_path=manifest_path,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )

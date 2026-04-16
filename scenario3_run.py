import os
import sys
import time
import datetime
import subprocess

from src.application.report_bundle import export_report_bundle
from src.application.report_payloads import build_advanced_report_payload

# Scenario 3: Spring4Shell Polymorphic Payload & Patch Bypass (Watering Hole)
# Logic based on 서브시나리오2.md

def header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def info(msg): print(f"  [*] {msg}")
def success(msg): print(f"  [SUCCESS] {msg}")
def warn(msg): print(f"  [!] {msg}")

def generate_report(results):
    report_dir = "03.FinalReport"
    os.makedirs(report_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Scenario3_AdvancedBypass_{timestamp}.html"
    filepath = os.path.join(report_dir, filename)
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Scenario 3 | Advanced Bypass Report</title>
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #000814; color: #f8f9fa; padding: 40px; }}
        .container {{ max-width: 900px; margin: auto; background: rgba(255,255,255,0.05); padding: 40px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); }}
        h1 {{ color: #0192BF; }}
        .step {{ margin-bottom: 20px; padding: 15px; background: rgba(0,0,0,0.3); border-left: 4px solid #0192BF; }}
        .success {{ color: #00ff88; font-weight: bold; }}
        pre {{ background: #000; color: #00d4ff; padding: 15px; border-radius: 8px; font-size: 13px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Advanced Bypass Simulation Report</h1>
        <p>Target: Manufacturing Management System (Legacy Patch Applied)</p>
        <p>Execution Time: {current_time}</p>
        <hr style="border: 0.5px solid #333;">
        
        <div class="step">
            <h3>Phase 1: Watering Hole Exposure</h3>
            <p>Admin Page XSS Injection: "CVE-2022-22965 Urgent Patch Advisory" modal deployed.</p>
        </div>
        
        <div class="step">
            <h3>Phase 2: Polymorphic Payload (WAF Bypass)</h3>
            <p>Using <b>fullhunt/spring4shell-scan</b> technique to bypass signature-based WAF.</p>
            <pre>Payload: Class.*, *.class.* variations detected.</pre>
        </div>
        
        <div class="step">
            <h3>Phase 3: Mitigation Bypass (CVE-2022-22968)</h3>
            <p>Server identified with <code>setDisallowedFields</code>. Exploiting case-sensitivity vulnerability to override AccessLogValve.</p>
            <p class="success">Result: Tomcat configuration successfully manipulated.</p>
        </div>
        
        <div class="step">
            <h3>Phase 4: Automatic Data Extraction</h3>
            <p>Scanned Spring Actuator for unsecured endpoints. Discovered AWS tokens and system environment variables.</p>
            <pre>Found: AWS_SECRET_ACCESS_KEY=**** (Masked in report)</pre>
        </div>
        
        <div class="footer" style="margin-top: 50px; text-align: center; color: #666;">
            SL Factory Innovation | Cyber Security Team
        </div>
    </div>
</body>
</html>"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    structured_payload = build_advanced_report_payload(
        report_filename=filename,
        current_time=current_time,
    )

    bundle_result = export_report_bundle(os.path.dirname(os.path.abspath(__file__)), filename, structured_payload)
    if bundle_result.success:
        info(f"Manifest Updated: {bundle_result.manifest_path}")
        if bundle_result.pdf_path.exists():
            info(f"Structured PDF Generated: {bundle_result.pdf_path}")
        return str(bundle_result.html_path)

    warn(f"Hybrid report pipeline fallback activated: {bundle_result.stderr or bundle_result.stdout or 'renderer unavailable'}")
    info(f"Manifest Updated: {bundle_result.manifest_path}")
    
    return filepath

def main():
    header("Scenario 3: Advanced Bypass & Watering Hole Attack")
    
    info("Phase 1: Deploying Watering Hole modal to Admin Dashboard...")
    time.sleep(1.5)
    success("Modal injected successfully. Waiting for admin trigger...")
    
    info("Phase 2: Admin clicked. Sending Polymorphic WAF Bypass payload...")
    time.sleep(2)
    warn("Detected WAF filtering. Rotating to 'class.module.classLoader' obfuscation...")
    time.sleep(1)
    
    info("Phase 3: Attacking 'setDisallowedFields' mitigation (CVE-2022-22968)...")
    time.sleep(2)
    success("Bypass successful. Case-sensitivity payload dropped webshell at /ROOT/patch_status.jsp")
    
    info("Phase 4: Running Post-Exploit Toolkit (Actuator Scan)...")
    time.sleep(2)
    success("Sensitive Info Leaked: Environment variables and cloud credentials harvested.")
    
    report_path = generate_report(True)
    header("Simulation Completed")
    info(f"Final Report Generated: {report_path}")

if __name__ == "__main__":
    main()

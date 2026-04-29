import requests, json

BASE = "http://localhost:8082"

# Test 1: Health
print("=== Test 1: Health ===")
try:
    res = requests.get(f"{BASE}/health", timeout=10)
    print(f"Status: {res.status_code}")
    print(json.dumps(res.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 2: Advisor with student_id (should use search_jobs tool)
print("=== Test 2: Advisor - Find Jobs ===")
try:
    payload = {
        "messages": [{"role": "user", "content": "Find jobs that match my skills"}],
        "student_id": "STU_0001"
    }
    res = requests.post(f"{BASE}/ai/advisor/chat", json=payload, timeout=60)
    print(f"Status: {res.status_code}")
    data = res.json()
    print(f"Tools used: {data.get('tools_used', [])}")
    print(f"Response: {data.get('text', '')[:500]}...")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 3: Advisor - Skill gap (should use analyze_skill_gap tool)
print("=== Test 3: Advisor - Skill Gap ===")
try:
    payload = {
        "messages": [{"role": "user", "content": "Analyze my skill gap for Software Engineer"}],
        "student_id": "STU_0001"
    }
    res = requests.post(f"{BASE}/ai/advisor/chat", json=payload, timeout=60)
    print(f"Status: {res.status_code}")
    data = res.json()
    print(f"Tools used: {data.get('tools_used', [])}")
    print(f"Response: {data.get('text', '')[:500]}...")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 4: Advisor - Courses (should use recommend_courses tool)
print("=== Test 4: Advisor - Courses ===")
try:
    payload = {
        "messages": [{"role": "user", "content": "Recommend courses to improve Python and SQL"}],
        "student_id": "STU_0001"
    }
    res = requests.post(f"{BASE}/ai/advisor/chat", json=payload, timeout=60)
    print(f"Status: {res.status_code}")
    data = res.json()
    print(f"Tools used: {data.get('tools_used', [])}")
    print(f"Response: {data.get('text', '')[:500]}...")
except Exception as e:
    print(f"Error: {e}")

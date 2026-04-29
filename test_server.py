import requests, json, sys

def test_health():
    try:
        res = requests.get('http://localhost:8081/health', timeout=10)
        print(f"Health: {res.status_code}")
        print(json.dumps(res.json(), indent=2))
    except Exception as e:
        print(f"Health check failed: {e}")

def test_advisor():
    try:
        payload = {
            "messages": [{"role": "user", "content": "What jobs match my skills?"}],
            "student_id": "STU_0001",
            "system_context": "You are FutureAlign AI Advisor."
        }
        res = requests.post('http://localhost:8081/ai/advisor/chat', json=payload, timeout=60)
        print(f"Advisor: {res.status_code}")
        print(json.dumps(res.json(), indent=2))
    except Exception as e:
        print(f"Advisor test failed: {e}")

if __name__ == "__main__":
    test_health()
    print("---")
    test_advisor()

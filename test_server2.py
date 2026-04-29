import requests, json

# Test 1: Advisor with student_id (should use RAG + student context)
payload = {
    "messages": [{"role": "user", "content": "What jobs match my skills?"}],
    "student_id": "STU_0001"
}
res = requests.post('http://localhost:8081/ai/advisor/chat', json=payload, timeout=60)
print("Test 1 - Advisor with student_id:")
print(f"Status: {res.status_code}")
print(json.dumps(res.json(), indent=2))
print("\n" + "="*60 + "\n")

# Test 2: Advisor asking about skill gap (should trigger tool)
payload = {
    "messages": [{"role": "user", "content": "Analyze my skill gap for Software Engineer"}],
    "student_id": "STU_0001"
}
res = requests.post('http://localhost:8081/ai/advisor/chat', json=payload, timeout=60)
print("Test 2 - Skill gap analysis:")
print(f"Status: {res.status_code}")
print(json.dumps(res.json(), indent=2))
print("\n" + "="*60 + "\n")

# Test 3: Advisor asking for courses (should trigger tool)
payload = {
    "messages": [{"role": "user", "content": "Recommend courses to improve my Python and SQL skills"}],
    "student_id": "STU_0001"
}
res = requests.post('http://localhost:8081/ai/advisor/chat', json=payload, timeout=60)
print("Test 3 - Course recommendations:")
print(f"Status: {res.status_code}")
print(json.dumps(res.json(), indent=2))

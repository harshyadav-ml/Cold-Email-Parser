"""scripts/verify_api.py — Full API integration test suite for The Closer.

Runs against the live running FastAPI server on http://localhost:8000.
Tests:
1. GET /api/status (labels: THE CLOSER, Groq LLaMA-3.3-70B, Harsh Yadav)
2. GET /api/contacts (quality scores & drafts)
3. POST /api/generate (3x consecutive calls for same contact -> 3 different subjects & bodies)
4. POST /api/settings/dry-run (toggle on/off)
5. POST /api/dispatch (draft, skip, send in dry-run mode)
6. GET /api/audit/logs & GET /api/audit/csv (8 audit columns & CSV file stream)
"""
import json
import sys
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"

def request_json(path: str, method: str = "GET", payload: dict = None) -> tuple[int, dict]:
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            return status_code, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": body}

def request_raw(path: str) -> tuple[int, str, dict]:
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        status_code = response.getcode()
        body = response.read().decode("utf-8")
        headers = dict(response.info())
        return status_code, body, headers

def run_suite():
    results = {}
    print("=" * 60)
    print("THE CLOSER — FULL API INTEGRATION TEST SUITE")
    print(f"Target: {BASE_URL}")
    print("=" * 60)

    # 1. GET /api/status
    print("\n[TEST 1] Testing GET /api/status...")
    code, data = request_json("/api/status")
    print(f"  HTTP {code}")
    print(f"  engine: {data.get('engine')}")
    print(f"  llm_model: {data.get('llm_model')}")
    print(f"  operator: {data.get('operator')}")
    print(f"  send_method_label: {data.get('send_method_label')}")
    print(f"  session_limit: {data.get('session_limit')}")

    test1_pass = (
        code == 200
        and "THE CLOSER" in data.get("engine", "")
        and "Groq LLaMA-3.3-70B" in data.get("llm_model", "")
        and "Harsh Yadav" in data.get("operator", "")
    )
    results["1. GET /api/status Labels Check"] = test1_pass
    print(f"  -> {'PASS' if test1_pass else 'FAIL'}")

    # 2. GET /api/contacts
    print("\n[TEST 2] Testing GET /api/contacts...")
    code, data = request_json("/api/contacts")
    contacts = data.get("contacts", [])
    print(f"  HTTP {code}, Total Contacts Loaded: {len(contacts)}")
    all_scored = len(contacts) > 0 and all(
        c.get("quality") and c.get("generated_subject") and c.get("generated_body")
        for c in contacts
    )
    if all_scored:
        first = contacts[0]
        print(f"  Contact 1: {first['contact']['recipient_name']} ({first['contact']['company']})")
        print(f"  Draft Subject: {first['generated_subject']}")
        print(f"  Quality Score: {first['quality']['score']}/10, Words: {first['quality']['word_count']}, Guard: {first['quality']['hallucination_guard']}")

    test2_pass = code == 200 and len(contacts) >= 3 and all_scored
    results["2. GET /api/contacts Scoring & Drafts"] = test2_pass
    print(f"  -> {'PASS' if test2_pass else 'FAIL'}")

    # 3. POST /api/generate (3 sequential calls for same contact -> 3 different outputs)
    print("\n[TEST 3] Testing POST /api/generate (3 calls for same contact)...")
    sample_contact = contacts[0]["contact"] if contacts else {
        "recipient_name": "Priya Sharma",
        "recipient_email": "priya@acmeai.com",
        "company": "Acme AI",
        "role": "Backend Engineering Intern",
    }
    
    code1, gen1 = request_json("/api/generate", method="POST", payload={"contact": sample_contact})
    code2, gen2 = request_json("/api/generate", method="POST", payload={"contact": sample_contact})
    code3, gen3 = request_json("/api/generate", method="POST", payload={"contact": sample_contact})

    print(f"  Call 1: Subject = \"{gen1.get('subject')}\"")
    print(f"  Call 2: Subject = \"{gen2.get('subject')}\"")
    print(f"  Call 3: Subject = \"{gen3.get('subject')}\"")

    subjects = [gen1.get("subject"), gen2.get("subject"), gen3.get("subject")]
    bodies = [gen1.get("body"), gen2.get("body"), gen3.get("body")]

    unique_subjects = len(set(subjects)) == 3
    unique_bodies = len(set(bodies)) == 3

    print(f"  Unique Subjects: {len(set(subjects))}/3 -> {unique_subjects}")
    print(f"  Unique Bodies: {len(set(bodies))}/3 -> {unique_bodies}")

    test3_pass = (code1 == 200 and code2 == 200 and code3 == 200 and unique_subjects and unique_bodies)
    results["3. POST /api/generate Variation (3x Distinct Calls)"] = test3_pass
    print(f"  -> {'PASS' if test3_pass else 'FAIL'}")

    # 4. POST /api/settings/dry-run
    print("\n[TEST 4] Testing POST /api/settings/dry-run (Toggle on/off)...")
    code_off, res_off = request_json("/api/settings/dry-run", method="POST", payload={"dry_run": False})
    print(f"  Set dry_run=False -> HTTP {code_off}, dry_run = {res_off.get('dry_run')}")
    
    code_on, res_on = request_json("/api/settings/dry-run", method="POST", payload={"dry_run": True})
    print(f"  Set dry_run=True  -> HTTP {code_on}, dry_run = {res_on.get('dry_run')}")

    test4_pass = (
        code_off == 200 and res_off.get("dry_run") is False
        and code_on == 200 and res_on.get("dry_run") is True
    )
    results["4. POST /api/settings/dry-run Runtime Toggle"] = test4_pass
    print(f"  -> {'PASS' if test4_pass else 'FAIL'}")

    # 5. POST /api/dispatch
    print("\n[TEST 5] Testing POST /api/dispatch (draft, skip, send in dry-run mode)...")
    
    # 5a: draft
    code_draft, res_draft = request_json(
        "/api/dispatch",
        method="POST",
        payload={
            "contact": sample_contact,
            "subject": gen1["subject"],
            "body": gen1["body"],
            "action": "draft",
        },
    )
    print(f"  Action 'draft' -> HTTP {code_draft}, status = {res_draft.get('status')}")

    # 5b: skip
    code_skip, res_skip = request_json(
        "/api/dispatch",
        method="POST",
        payload={
            "contact": sample_contact,
            "subject": gen2["subject"],
            "body": gen2["body"],
            "action": "skip",
        },
    )
    print(f"  Action 'skip'  -> HTTP {code_skip}, status = {res_skip.get('status')}")

    # 5c: send (in dry run)
    code_send, res_send = request_json(
        "/api/dispatch",
        method="POST",
        payload={
            "contact": sample_contact,
            "subject": gen3["subject"],
            "body": gen3["body"],
            "action": "send",
        },
    )
    print(f"  Action 'send' (DRY_RUN) -> HTTP {code_send}, status = {res_send.get('status')}")

    test5_pass = (
        code_draft == 200 and res_draft.get("status") in ("dry_run", "drafted")
        and code_skip == 200 and res_skip.get("status") == "skipped"
        and code_send == 200 and res_send.get("status") == "dry_run"
    )
    results["5. POST /api/dispatch (draft, skip, send)"] = test5_pass
    print(f"  -> {'PASS' if test5_pass else 'FAIL'}")

    # 6. GET /api/audit/logs & GET /api/audit/csv
    print("\n[TEST 6] Testing GET /api/audit/logs & GET /api/audit/csv...")
    code_logs, data_logs = request_json("/api/audit/logs?limit=10")
    columns = data_logs.get("columns", [])
    logs_list = data_logs.get("logs", [])
    print(f"  Logs count: {len(logs_list)}, Expected columns: {len(columns)}")
    print(f"  Columns: {columns}")
    
    expected_cols = [
        "TIMESTAMP (UTC)",
        "RECIPIENT EMAIL",
        "COMPANY",
        "ROLE",
        "SUBJECT",
        "STATUS",
        "WORDS",
        "ERROR DETAILS",
    ]
    cols_match = columns == expected_cols

    code_csv, csv_content, csv_headers = request_raw("/api/audit/csv")
    csv_lines = csv_content.strip().split("\n")
    print(f"  CSV Download -> HTTP {code_csv}, Total lines: {len(csv_lines)}")
    print(f"  CSV Header: {csv_lines[0] if csv_lines else 'EMPTY'}")

    test6_pass = (
        code_logs == 200
        and cols_match
        and len(logs_list) > 0
        and code_csv == 200
        and "text/csv" in csv_headers.get("content-type", "")
        and len(csv_lines) >= 2
    )
    results["6. GET /api/audit/logs & /csv (8 Columns Enforced)"] = test6_pass
    print(f"  -> {'PASS' if test6_pass else 'FAIL'}")

    # SUMMARY
    print("\n" + "=" * 60)
    print("TEST SUITE SUMMARY")
    print("=" * 60)
    all_passed = True
    for test_name, status in results.items():
        state = "PASS [✓]" if status else "FAIL [✗]"
        print(f"  {state} - {test_name}")
        if not status:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED SUCCESSFULLY (6/6)")
    else:
        print("SOME TESTS FAILED")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    run_suite()

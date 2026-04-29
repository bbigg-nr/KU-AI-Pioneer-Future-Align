#!/usr/bin/env python3
"""
extract_jd_skills.py
--------------------
Reads JD text files from data/jd/, uses Claude to extract skills per career,
then compares against the hardcoded CAREER_SKILL_MAP in Generate_DATA.py.

Usage:
    python extract_jd_skills.py

Outputs:
    data/jd_skill_map.json   — structured skills extracted from JD files
    data/jd_gap_report.json  — gap analysis vs current CAREER_SKILL_MAP in code
"""

import ast
import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

JD_DIR   = Path("data/jd")
OUT_MAP  = Path("data/jd_skill_map.json")
OUT_GAPS = Path("data/jd_gap_report.json")
MODEL    = "claude-haiku-4-5"

SYSTEM_PROMPT = """\
You are a structured skill extraction specialist.

Given Job Description text that may contain one or more career role sections,
extract the required skills for EACH career role you find.

Return ONLY valid JSON (no markdown fences, no commentary) in this exact schema:
{
  "Career Title": {
    "core_skills": ["skill1", "skill2", ...],
    "adjacent_skills": ["skill3", ...]
  }
}

Rules:
- core_skills: skills listed as "required", "must have", or appear in core qualifications
- adjacent_skills: skills listed as "preferred", "a plus", "advantageous", "nice to have"
- Keep skill names concise: "Python" not "Python programming language"
- Include tools, frameworks, certifications, and methodologies
- If a skill appears in both, put it in core_skills only
- Career title should match the heading in the JD as closely as possible
- Only include skills, NOT general qualifications like "Bachelor's degree" or "years of experience"
"""


def extract_skills_from_jd(client: anthropic.Anthropic, jd_text: str) -> dict:
    """Call Claude to extract structured skills from one JD file using prompt caching."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{
            "role": "user",
            "content": [{
                "type": "text",
                "text": jd_text,
                "cache_control": {"type": "ephemeral"},
            }],
        }],
    )

    u = response.usage
    print(f"    tokens  in={u.input_tokens}  cached={u.cache_read_input_tokens}  out={u.output_tokens}")

    raw = response.content[0].text.strip()
    # Strip markdown code fences if Claude wraps the output
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json\n"):
            raw = raw[5:]

    return json.loads(raw)


def load_career_skill_map_from_source() -> dict:
    """
    Parse CAREER_SKILL_MAP from Generate_DATA.py using AST — no code execution,
    no side effects, no CSV regeneration.
    """
    src = Path("Generate_DATA.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    result: dict = {}

    for node in ast.walk(tree):
        # CAREER_SKILL_MAP = { ... }
        if (isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "CAREER_SKILL_MAP"
                        for t in node.targets)):
            try:
                result = ast.literal_eval(node.value)
            except Exception:
                pass

        # CAREER_SKILL_MAP.update({ ... })
        elif (isinstance(node, ast.Expr)
              and isinstance(node.value, ast.Call)
              and isinstance(node.value.func, ast.Attribute)
              and isinstance(node.value.func.value, ast.Name)
              and node.value.func.value.id == "CAREER_SKILL_MAP"
              and node.value.func.attr == "update"
              and node.value.args):
            try:
                result.update(ast.literal_eval(node.value.args[0]))
            except Exception:
                pass

    return result


def gap_analysis(jd_map: dict, code_map: dict) -> dict:
    """
    For each career in the JD map, check how well the hardcoded CAREER_SKILL_MAP covers it.
    Returns a report dict with statuses: OK | GAPS | NOT_IN_CAREER_SKILL_MAP | NOT_IN_ANY_JD
    """
    report: dict = {}

    for career, jd_data in jd_map.items():
        jd_core = set(jd_data.get("core_skills", []))
        jd_adj  = set(jd_data.get("adjacent_skills", []))
        jd_all  = jd_core | jd_adj

        # Case-insensitive match against code career names
        match = next((k for k in code_map if k.lower() == career.lower()), None)
        if match is None:
            report[career] = {"status": "NOT_IN_CAREER_SKILL_MAP"}
            continue

        cur_all = set(code_map[match]["core"]) | set(code_map[match]["adjacent"])

        missing_core = sorted(jd_core - cur_all)
        missing_adj  = sorted(jd_adj  - cur_all)
        extra        = sorted(cur_all  - jd_all)

        if missing_core or missing_adj:
            report[career] = {
                "status": "GAPS",
                "missing_core_skills":     missing_core,
                "missing_adjacent_skills": missing_adj,
                "in_code_not_in_jd":       extra,
            }
        else:
            report[career] = {
                "status": "OK",
                "in_code_not_in_jd": extra,
            }

    # Careers in code but absent from all JD files
    for career in code_map:
        if not any(career.lower() == k.lower() for k in jd_map):
            report[career] = {"status": "NOT_IN_ANY_JD"}

    return report


def main() -> None:
    client = anthropic.Anthropic()
    JD_DIR.mkdir(parents=True, exist_ok=True)

    jd_files = sorted(JD_DIR.glob("*.txt"))
    if not jd_files:
        print(f"[!] No .txt files found in {JD_DIR}/")
        print("    Add JD text files there and re-run.")
        return

    print(f"[+] Found {len(jd_files)} JD file(s): {[f.name for f in jd_files]}")

    # ── Extract skills from each JD file ---───────────────────────────────
    merged: dict = {}
    for jd_file in jd_files:
        print(f"\n  Processing {jd_file.name} …")
        text = jd_file.read_text(encoding="utf-8-sig")
        extracted = extract_skills_from_jd(client, text)
        print(f"    Found {len(extracted)} career section(s)")

        for career, data in extracted.items():
            if career in merged:
                # Merge skills from duplicate career sections across files
                merged[career]["core_skills"] = list(
                    set(merged[career]["core_skills"] + data.get("core_skills", []))
                )
                merged[career]["adjacent_skills"] = list(
                    set(merged[career].get("adjacent_skills", []) + data.get("adjacent_skills", []))
                )
            else:
                merged[career] = data

    OUT_MAP.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[+] Saved {len(merged)} careers -> {OUT_MAP}")

    # ── Gap analysis ---────────────────────────────────────────────────────
    print("\n[+] Running gap analysis against Generate_DATA.py CAREER_SKILL_MAP …")
    code_map = load_career_skill_map_from_source()
    if not code_map:
        print("    [!] Could not parse CAREER_SKILL_MAP — check Generate_DATA.py")
        return

    print(f"    Loaded {len(code_map)} careers from code")
    gaps = gap_analysis(merged, code_map)
    OUT_GAPS.write_text(json.dumps(gaps, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── Summary ---─────────────────────────────────────────────────────────
    statuses = [v["status"] for v in gaps.values()]
    print("\n  ---Gap Report Summary ---")
    print(f"    OK (fully covered):        {statuses.count('OK')}")
    print(f"    Gaps found (skills missing): {statuses.count('GAPS')}")
    print(f"    Not in CAREER_SKILL_MAP:   {statuses.count('NOT_IN_CAREER_SKILL_MAP')}")
    print(f"    Not in any JD file:        {statuses.count('NOT_IN_ANY_JD')}")
    print(f"\n[+] Full gap report -> {OUT_GAPS}")

    # Print careers with gaps
    gapped = [(k, v) for k, v in gaps.items() if v["status"] == "GAPS"]
    if gapped:
        print("\n  ---Careers with Missing Skills ---")
        for career, info in sorted(gapped):
            mc = info.get("missing_core_skills", [])
            ma = info.get("missing_adjacent_skills", [])
            print(f"\n    [{career}]")
            if mc:
                print(f"      core missing:     {mc}")
            if ma:
                print(f"      adjacent missing: {ma}")

    not_in_jd = [k for k, v in gaps.items() if v["status"] == "NOT_IN_ANY_JD"]
    if not_in_jd:
        print(f"\n  ---Careers in Code but NOT in any JD ---")
        for career in sorted(not_in_jd):
            print(f"    {career}")


if __name__ == "__main__":
    main()

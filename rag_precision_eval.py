# -*- coding: utf-8 -*-
"""
rag_precision_eval.py
---------------------
RAGAS-style manual evaluation ของ RAG pipeline:

  - Context Precision  (X/k)  — กี่ chunks ใน k ที่ retrieved มาแล้วเกี่ยวข้องกับ query
  - Faithfulness       (1/0)  — Claude ตอบจาก context หรือคิดเอง?
  - Answer Relevance   (1/0)  — คำตอบตรงคำถามหรือเปล่า?
  - Latency (s)

Output: Markdown table พร้อม print ออก stdout (copy ใส่ README.md ได้เลย)

รัน: python rag_precision_eval.py
     python rag_precision_eval.py --k 5 --out results.md
"""

import argparse
import time
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv
import anthropic
from matcher import SkillMatcher

load_dotenv()

# ── Config ─────────────────────────────────────────────────────
JUDGE_MODEL    = "claude-haiku-4-5-20251001"   # ใช้ Haiku เพื่อประหยัด cost
ADVISOR_MODEL  = "claude-haiku-4-5-20251001"
DEFAULT_K      = 3   # top_k_jobs ที่ดึงมา

# ── Question Bank (10 คำถาม) ───────────────────────────────────
QUESTION_BANK = [
    {
        "query":    "What careers suit someone with Python, Machine Learning, SQL, and data skills?",
        "expected": ["data scientist", "ml engineer", "data analyst", "data engineer"],
    },
    {
        "query":    "I know Docker, Kubernetes, Terraform, and CI/CD — what jobs should I apply for?",
        "expected": ["devops", "site reliability engineer", "cloud architect", "sre"],
    },
    {
        "query":    "What jobs involve LangChain, RAG, prompt engineering, and LLM fine-tuning?",
        "expected": ["ai engineer", "ml engineer", "mlops"],
    },
    {
        "query":    "I have JavaScript, TypeScript, React, Node.js skills — what jobs fit?",
        "expected": ["full-stack", "software engineer", "frontend", "backend"],
    },
    {
        "query":    "What career paths exist for someone skilled in penetration testing and OWASP?",
        "expected": ["cybersecurity", "security engineer", "appsec"],
    },
    {
        "query":    "What jobs are suitable for blockchain developers who know Solidity and DeFi?",
        "expected": ["blockchain", "web3", "smart contract", "crypto"],
    },
    {
        "query":    "I want a finance career — I know DCF valuation, financial modeling, and Bloomberg.",
        "expected": ["financial analyst", "investment banker", "fp&a", "corporate finance"],
    },
    {
        "query":    "What jobs involve ESG reporting, sustainability, and green finance?",
        "expected": ["esg", "sustainability", "environmental"],
    },
    {
        "query":    "What career fits someone with C/C++, RTOS, and embedded systems experience?",
        "expected": ["embedded systems", "embedded"],
    },
    {
        "query":    "I have Apache Spark, Airflow, dbt, and AWS skills — what jobs are available?",
        "expected": ["data engineer", "data scientist", "mlops"],
    },
]


# ── Helpers ────────────────────────────────────────────────────

def ctx_precision(retrieved_jobs: list[dict], expected: list[str], k: int) -> tuple[int, int]:
    """คืน (X, k) — กี่ jobs ใน top-k ที่ title ตรงกับ expected keywords"""
    relevant = 0
    for job in retrieved_jobs[:k]:
        title = job["job_title"].lower()
        if any(kw in title for kw in expected):
            relevant += 1
    return relevant, min(k, len(retrieved_jobs))


def build_context_str(retrieved_jobs: list[dict], k: int) -> str:
    lines = []
    for i, j in enumerate(retrieved_jobs[:k], 1):
        skills = ", ".join(j.get("skills", [])[:8])
        industry = j.get("industry", "")
        salary_info = ""
        if j.get("min_salary") and j.get("max_salary"):
            salary_info = f" | Salary: {j['min_salary']}-{j['max_salary']} THB"
        industry_info = f" | Industry: {industry}" if industry else ""
        lines.append(
            f"{i}. {j['job_title']}{industry_info}{salary_info} — requires: {skills}"
        )
    return "\n".join(lines)


def generate_answer(client: anthropic.Anthropic, query: str, context: str) -> str:
    """ให้ Claude ตอบคำถามโดยใช้ context ที่ให้มา — บังคับให้ grounded อย่างเคร่งครัด"""
    prompt = (
        "You are a career advisor. CRITICAL RULES (STRICT — NO EXCEPTIONS):\n"
        "1. You MUST base your answer ONLY on the Retrieved Job Context below.\n"
        "2. Do NOT use any external knowledge, assumptions, or invented facts.\n"
        "3. If the context does not explicitly mention the job titles or skills asked about, "
        "you MUST respond with ONLY this exact sentence:\n"
        "'Based on the available data, I cannot answer this specifically.'\n"
        "4. If the context DOES contain relevant jobs, mention ONLY those specific job titles "
        "and skills that appear in the context.\n"
        "5. Do NOT generalize or infer. Do NOT say 'you are well-positioned for X' unless X is literally in the context.\n\n"
        f"### Retrieved Job Context\n{context}\n\n"
        f"### Student Question\n{query}\n\n"
        "Answer in 1-3 sentences following the rules above."
    )
    resp = client.messages.create(
        model=ADVISOR_MODEL,
        max_tokens=256,
        temperature=0.0,  # zero temperature for maximum faithfulness
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip() if resp.content else ""


def judge_faithfulness(client: anthropic.Anthropic, context: str, answer: str) -> int:
    """
    1 = คำตอบอ้างอิงจาก context (faithful)
    0 = คำตอบคิดเองหรือมีข้อมูลที่ไม่มีใน context (hallucinate)
    """
    prompt = (
        "You are an evaluator. Given a CONTEXT and an ANSWER, decide:\n"
        "Reply with exactly '1' if every claim in the ANSWER can be found in the CONTEXT.\n"
        "Reply with exactly '0' if the ANSWER contains claims NOT present in the CONTEXT.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"ANSWER:\n{answer}\n\n"
        "Reply with only '1' or '0'."
    )
    resp = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=4,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip() if resp.content else "0"
    return 1 if raw.startswith("1") else 0


def judge_relevance(client: anthropic.Anthropic, query: str, answer: str) -> int:
    """
    1 = คำตอบตรงกับคำถาม (relevant)
    0 = คำตอบไม่ตรงหรือออกนอกเรื่อง
    """
    prompt = (
        "You are an evaluator. Given a QUESTION and an ANSWER, decide:\n"
        "Reply with exactly '1' if the ANSWER directly addresses the QUESTION.\n"
        "Reply with exactly '0' if the ANSWER is off-topic or does not address the QUESTION.\n\n"
        f"QUESTION:\n{query}\n\n"
        f"ANSWER:\n{answer}\n\n"
        "Reply with only '1' or '0'."
    )
    resp = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=4,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip() if resp.content else "0"
    return 1 if raw.startswith("1") else 0


# ── Main Evaluation ────────────────────────────────────────────

def run_eval(k: int = DEFAULT_K) -> list[dict]:
    print(f"\nLoading SkillMatcher & Anthropic client (k={k})...\n")
    matcher = SkillMatcher()
    client  = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    rows = []
    for i, q in enumerate(QUESTION_BANK, 1):
        print(f"  [{i:02d}/{len(QUESTION_BANK)}] {q['query'][:60]}...")

        # ── RAG retrieval ─────────────────────────────────────
        t0 = time.perf_counter()
        result = matcher.rag_search(q["query"], top_k_jobs=k, top_k_alumni=1)
        latency = time.perf_counter() - t0

        retrieved = result.get("relevant_jobs", [])
        context   = build_context_str(retrieved, k)

        # ── Context Precision X/k ─────────────────────────────
        x, actual_k = ctx_precision(retrieved, q["expected"], k)

        # ── Generate answer via Claude ────────────────────────
        answer = generate_answer(client, q["query"], context) if context else "No context retrieved."

        # ── Judge Faithfulness & Relevance ────────────────────
        faith = judge_faithfulness(client, context, answer) if context else 0
        relev = judge_relevance(client, q["query"], answer)

        rows.append({
            "query":     q["query"],
            "answer":    answer,
            "latency":   latency,
            "faith":     faith,
            "relevance": relev,
            "x":         x,
            "k":         actual_k,
        })

        print(f"         latency={latency:.2f}s  faith={faith}  rel={relev}  ctx={x}/{actual_k}")

    return rows


def print_markdown_table(rows: list[dict]) -> str:
    short_q  = lambda s: (s[:55] + "…") if len(s) > 55 else s
    short_a  = lambda s: (s[:70] + "…") if len(s) > 70 else s

    header = (
        "| Query | Answer | Latency | Faithfulness (1/0) | Relevance (1/0) | Ctx Precision (X/k) |\n"
        "|---|---|---|---|---|---|"
    )
    lines = [header]
    for r in rows:
        lines.append(
            f"| {short_q(r['query'])} "
            f"| {short_a(r['answer'])} "
            f"| {r['latency']:.1f}s "
            f"| {r['faith']} "
            f"| {r['relevance']} "
            f"| {r['x']}/{r['k']} |"
        )

    # ── Summary row ───────────────────────────────────────────
    n          = len(rows)
    avg_lat    = sum(r["latency"] for r in rows) / n
    avg_faith  = sum(r["faith"]   for r in rows) / n
    avg_rel    = sum(r["relevance"] for r in rows) / n
    avg_ctx    = sum(r["x"] / r["k"] for r in rows if r["k"] > 0) / n

    lines.append(
        f"| **Average ({n} Qs)** | — "
        f"| {avg_lat:.1f}s "
        f"| {avg_faith:.1f} "
        f"| {avg_rel:.1f} "
        f"| {avg_ctx:.2f} |"
    )

    table = "\n".join(lines)

    print("\n" + "=" * 70)
    print("  RAGAS-style Evaluation Results")
    print("=" * 70)
    print(table)
    print()
    print(f"  Avg Latency       : {avg_lat:.2f}s")
    print(f"  Avg Faithfulness  : {avg_faith:.2f}  (target: >= 0.80)")
    print(f"  Avg Ans Relevance : {avg_rel:.2f}  (target: >= 0.80)")
    print(f"  Avg Ctx Precision : {avg_ctx:.2f}  (target: >= 0.60)")
    print()

    return table


def main():
    parser = argparse.ArgumentParser(description="RAGAS-style RAG Precision Evaluation")
    parser.add_argument("--k",   type=int, default=DEFAULT_K, help=f"top_k_jobs (default: {DEFAULT_K})")
    parser.add_argument("--out", type=str, default="",        help="บันทึก Markdown table ลงไฟล์ (optional)")
    args = parser.parse_args()

    rows  = run_eval(k=args.k)
    table = print_markdown_table(rows)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(f"# RAG Evaluation (k={args.k})\n\n")
            f.write(table + "\n")
        print(f"  Saved to {args.out}")


if __name__ == "__main__":
    main()

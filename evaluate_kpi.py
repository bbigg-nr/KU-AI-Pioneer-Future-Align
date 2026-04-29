# -*- coding: utf-8 -*-
"""
evaluate_kpi.py
---------------
วัดผล 5 KPI หลักของระบบ Career Matcher

รัน: python evaluate_kpi.py
     python evaluate_kpi.py --sample 100
     python evaluate_kpi.py --kpi backtest
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import argparse
import csv
import json
import time
import random
from difflib import SequenceMatcher

from matcher import SkillMatcher

# ── Config ────────────────────────────────────────────────────

ALUMNI_PATH         = "data/alumni_dataset_500.csv"
BACKTEST_ALUMNI_PATH = "data/backtest_alumni.csv"   # holdout set (ไม่มี data leakage)
STUDENT_PATH        = "data/synthetic_student_dataset_500_clean.csv"
RANDOM_SEED  = 42
random.seed(RANDOM_SEED)

# ── Helpers ───────────────────────────────────────────────────

def load_alumni(path: str) -> list[dict]:
    """รองรับทั้ง alumni_dataset_500.csv (skills_at_graduation) และ backtest_alumni.csv (skills)"""
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        skill_col = "skills_at_graduation" if "skills_at_graduation" in reader.fieldnames else "skills"
        for row in reader:
            rows.append({
                "alumni_id":       row["alumni_id"],
                "first_job_title": row["first_job_title"],
                "skills":          json.loads(row[skill_col]),
            })
    return rows


def load_students(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows.append({
                "student_id":    row["student_id"],
                "target_career": row["target_career"],
                "skills":        json.loads(row["skills"]),
            })
    return rows


def title_match(predicted: str, actual: str) -> bool:
    p = predicted.lower().strip()
    a = actual.lower().strip()
    if p == a:
        return True
    return SequenceMatcher(None, p, a).ratio() >= 0.75


def rank_of_title(job_title: str, top_jobs: list[dict]) -> int | None:
    for i, job in enumerate(top_jobs):
        if title_match(job["job_title"], job_title):
            return i
    return None


def print_header(title: str):
    print(f"\n{'=' * 58}")
    print(f"  {title}")
    print(f"{'=' * 58}")


def print_result(label: str, value: str, pass_: bool | None = None):
    tag = "      " if pass_ is None else ("[PASS]" if pass_ else "[FAIL]")
    print(f"  {tag} {label:<38} {value}")


# ═══════════════════════════════════════════════════════════════
#  KPI 1 — Backtesting: Hit@1, Hit@3, MRR
# ═══════════════════════════════════════════════════════════════

def kpi_backtest(matcher: SkillMatcher, alumni: list[dict], sample: int) -> dict:
    print_header("KPI 1 — Backtesting (Hit@1 / Hit@3 / MRR)")
    print(f"  holdout alumni {sample} คน — skills มี noise 15-40%, level ไม่ตรง job requirement\n")
    print(f"  {'Profile':<40} {'Rank':>5}  {'MRR':>6}")
    print(f"  {'-'*55}")

    subset = random.sample(alumni, min(sample, len(alumni)))
    hit1, hit3, mrr_sum, total, skipped = 0, 0, 0.0, 0, 0

    for alum in subset:
        skills = alum["skills"]
        if not skills:
            skipped += 1
            continue

        result   = matcher.match(skills, top_n=5)
        top_jobs = result.get("top_jobs", [])
        actual   = alum["first_job_title"]

        rank = None
        for i, job in enumerate(top_jobs):
            if title_match(job["job_title"], actual):
                rank = i + 1   # 1-indexed
                break

        if rank == 1:
            hit1 += 1
        if rank is not None and rank <= 3:
            hit3 += 1
        mrr_sum += (1.0 / rank) if rank else 0.0
        total   += 1

        rank_str = f"#{rank}" if rank else "miss"
        mrr_str  = f"{1/rank:.2f}" if rank else "0.00"
        print(f"  {alum['first_job_title']:<40} {rank_str:>5}  {mrr_str:>6}")

    p1  = hit1    / total if total > 0 else 0
    p3  = hit3    / total if total > 0 else 0
    mrr = mrr_sum / total if total > 0 else 0

    print(f"\n  {'-'*55}")
    print_result("Hit@1 (Precision@1)",  f"{p1:.1%}  ({hit1}/{total})",  p1  >= 0.60)
    print_result("Hit@3",                f"{p3:.1%}  ({hit3}/{total})",  p3  >= 0.75)
    print_result("MRR (Mean Reciprocal Rank)", f"{mrr:.3f}",             mrr >= 0.70)
    print_result("Target", "Hit@1>=60%, Hit@3>=75%, MRR>=0.70", None)
    if skipped:
        print(f"  [SKIP] ข้าม {skipped} คน (ไม่มี skills)")
    return {"hit1": p1, "hit3": p3, "mrr": mrr, "total": total}


# ═══════════════════════════════════════════════════════════════
#  KPI 2 — Precision@3 (Constructed Ground Truth)
# ═══════════════════════════════════════════════════════════════

# profiles สร้างจาก JD จริงในไฟล์ FutureAlign.txt — skill names ตรงกับ CAREER_SKILL_MAP ใน Generate_DATA.py
GROUND_TRUTH_PROFILES = [
    {   # JD: Go+Next.js SWE, Node.js SWE (multiple Thai companies)
        "label": "Software Engineer",
        "skills": [
            {"name": "Python",                    "level": "Intermediate"},
            {"name": "Go",                        "level": "Intermediate"},
            {"name": "REST API Design",           "level": "Intermediate"},
            {"name": "Docker",                    "level": "Intermediate"},
            {"name": "SQL",                       "level": "Intermediate"},
            {"name": "Git / Version Control",     "level": "Intermediate"},
            {"name": "Agile / Scrum Methodology", "level": "Beginner"},
        ],
        "expected_keywords": ["software engineer", "backend", "full-stack", "fintech software"],
    },
    {   # JD: Data Scientist (ML/predictive models, ETL, deployment)
        "label": "Data Scientist",
        "skills": [
            {"name": "Python",               "level": "Advanced"},
            {"name": "Machine Learning",     "level": "Intermediate"},
            {"name": "Scikit-learn",         "level": "Intermediate"},
            {"name": "Statistical Modeling", "level": "Intermediate"},
            {"name": "Feature Engineering",  "level": "Intermediate"},
            {"name": "SQL",                  "level": "Intermediate"},
            {"name": "Data Visualization",   "level": "Beginner"},
        ],
        "expected_keywords": ["data scientist", "ml engineer", "data analyst", "data engineer"],
    },
    {   # JD: Data Engineer (ETL, Airflow, Spark, cloud — Thai finance/tech)
        "label": "Data Engineer",
        "skills": [
            {"name": "Python",                  "level": "Advanced"},
            {"name": "SQL",                     "level": "Advanced"},
            {"name": "Apache Spark",            "level": "Intermediate"},
            {"name": "Airflow",                 "level": "Intermediate"},
            {"name": "dbt (Data Build Tool)",   "level": "Intermediate"},
            {"name": "AWS (EC2, S3, Lambda)",   "level": "Intermediate"},
            {"name": "Docker",                  "level": "Beginner"},
        ],
        "expected_keywords": ["data engineer", "data scientist", "mlops"],
    },
    {   # JD: AI Engineer (LangChain, LangGraph, Agentic AI, LLM — Thai tech)
        "label": "AI Engineer",
        "skills": [
            {"name": "Python",                              "level": "Advanced"},
            {"name": "LangChain",                          "level": "Intermediate"},
            {"name": "LLM Fine-tuning",                    "level": "Intermediate"},
            {"name": "Prompt Engineering",                 "level": "Intermediate"},
            {"name": "RAG (Retrieval-Augmented Generation)","level": "Intermediate"},
            {"name": "Hugging Face Transformers",          "level": "Intermediate"},
            {"name": "Docker",                             "level": "Beginner"},
        ],
        "expected_keywords": ["ai engineer", "ml engineer", "mlops", "machine learning"],
    },
    {   # JD: MLOps Engineer (Kubernetes, MLflow, Airflow, CI/CD — Agoda/SCB X)
        "label": "MLOps Engineer",
        "skills": [
            {"name": "Model Deployment (MLOps)",    "level": "Intermediate"},
            {"name": "Kubernetes",                  "level": "Intermediate"},
            {"name": "Airflow",                     "level": "Intermediate"},
            {"name": "MLflow / Weights & Biases",   "level": "Intermediate"},
            {"name": "Python",                      "level": "Advanced"},
            {"name": "CI/CD Pipelines",             "level": "Intermediate"},
            {"name": "Docker",                      "level": "Intermediate"},
        ],
        "expected_keywords": ["mlops", "ml engineer", "ai engineer", "data engineer"],
    },
    {   # JD: DevOps (Docker, K8s, Terraform, GitLab CI, Azure/GCP)
        "label": "DevOps / SRE Engineer",
        "skills": [
            {"name": "Docker",               "level": "Advanced"},
            {"name": "Kubernetes",           "level": "Intermediate"},
            {"name": "CI/CD Pipelines",      "level": "Intermediate"},
            {"name": "Terraform",            "level": "Intermediate"},
            {"name": "Linux System Admin",   "level": "Advanced"},
            {"name": "GitHub Actions",       "level": "Intermediate"},
            {"name": "Prometheus & Grafana", "level": "Beginner"},
        ],
        "expected_keywords": ["devops", "sre", "site reliability engineer", "cloud architect"],
    },
    {   # JD: Cloud Architect (multi-cloud OCI/AWS/Azure, Landing Zones, IAM, HA/DR)
        "label": "Cloud Architect",
        "skills": [
            {"name": "AWS (EC2, S3, Lambda)",    "level": "Advanced"},
            {"name": "Azure (AKS, Functions)",   "level": "Intermediate"},
            {"name": "GCP (BigQuery, GKE)",      "level": "Intermediate"},
            {"name": "Kubernetes",               "level": "Intermediate"},
            {"name": "Terraform",                "level": "Intermediate"},
            {"name": "Microservices Architecture","level": "Intermediate"},
            {"name": "CI/CD Pipelines",          "level": "Beginner"},
        ],
        "expected_keywords": ["cloud architect", "devops", "site reliability engineer"],
    },
    {   # JD: Cybersecurity (SIEM, EDR, Pen Test, ISO 27001, Incident Response)
        "label": "Cybersecurity Engineer",
        "skills": [
            {"name": "Penetration Testing",     "level": "Intermediate"},
            {"name": "Network Security",        "level": "Intermediate"},
            {"name": "SIEM Tools",              "level": "Intermediate"},
            {"name": "OWASP Top 10",            "level": "Intermediate"},
            {"name": "Vulnerability Assessment", "level": "Intermediate"},
            {"name": "Linux System Admin",      "level": "Advanced"},
            {"name": "Python",                  "level": "Beginner"},
        ],
        "expected_keywords": ["cybersecurity", "security engineer", "appsec"],
    },
    {   # JD: Full-Stack (Vue.js/NestJS/ElysiaJS, PostgreSQL, Docker, K8s)
        "label": "Full-Stack Developer",
        "skills": [
            {"name": "JavaScript",          "level": "Advanced"},
            {"name": "TypeScript",          "level": "Intermediate"},
            {"name": "Vue.js",              "level": "Intermediate"},
            {"name": "Node.js",             "level": "Intermediate"},
            {"name": "Next.js",             "level": "Intermediate"},
            {"name": "PostgreSQL",          "level": "Intermediate"},
            {"name": "REST API Design",     "level": "Intermediate"},
            {"name": "Docker",              "level": "Beginner"},
        ],
        "expected_keywords": ["full-stack", "software engineer", "backend"],
    },
    {   # JD: Embedded (C/C++/VHDL, FPGA, DSP, IoT, RTOS — Toyota Tsucho TH)
        "label": "Embedded Systems Engineer",
        "skills": [
            {"name": "C/C++",                                  "level": "Advanced"},
            {"name": "Embedded Systems (Arduino/Raspberry Pi)", "level": "Intermediate"},
            {"name": "Real-Time Operating Systems (RTOS)",     "level": "Intermediate"},
            {"name": "FPGA Programming",                       "level": "Intermediate"},
            {"name": "Microcontroller Programming",            "level": "Intermediate"},
            {"name": "IoT Development",                        "level": "Beginner"},
        ],
        "expected_keywords": ["embedded systems", "embedded"],
    },
    {   # JD: Web3 Developer (Java/Spring Cloud + Solidity, high-concurrency, DeFi)
        "label": "Blockchain / Web3 Developer",
        "skills": [
            {"name": "Solidity",                   "level": "Intermediate"},
            {"name": "Ethereum / EVM",             "level": "Intermediate"},
            {"name": "Smart Contract Development", "level": "Intermediate"},
            {"name": "Web3.js / Ethers.js",        "level": "Intermediate"},
            {"name": "DeFi Protocols",             "level": "Intermediate"},
            {"name": "Cryptography",               "level": "Beginner"},
            {"name": "JavaScript / TypeScript",    "level": "Intermediate"},
        ],
        "expected_keywords": ["blockchain", "web3", "smart contract"],
    },
    {   # JD: Investment Banker (IPO, M&A, IFA, Due Diligence, SEC/SET — Thai securities)
        "label": "Investment Banker",
        "skills": [
            {"name": "Investment Banking (M&A Modeling)", "level": "Intermediate"},
            {"name": "Valuation (DCF, Comps)",            "level": "Intermediate"},
            {"name": "Financial Modeling",                "level": "Intermediate"},
            {"name": "Financial Statement Analysis",      "level": "Intermediate"},
            {"name": "Bloomberg Terminal",                "level": "Beginner"},
            {"name": "Negotiation",                       "level": "Beginner"},
            {"name": "Presentation Skills",               "level": "Intermediate"},
        ],
        "expected_keywords": ["investment banker", "investment banking", "corporate finance", "equity research"],
    },
    {   # JD: Financial Analyst (FP&A + Cash Flow + Variance Analysis — Thai MNC)
        "label": "Financial Analyst",
        "skills": [
            {"name": "Financial Modeling",                         "level": "Intermediate"},
            {"name": "Excel (Advanced: Solver, VBA, Power Query)", "level": "Advanced"},
            {"name": "Financial Statement Analysis",               "level": "Intermediate"},
            {"name": "Budgeting & Forecasting",                    "level": "Intermediate"},
            {"name": "Valuation (DCF, Comps)",                     "level": "Beginner"},
            {"name": "Bloomberg Terminal",                         "level": "Beginner"},
        ],
        "expected_keywords": ["financial analyst", "fp&a", "corporate finance", "investment banker"],
    },
    {   # JD: Risk Manager (Credit Risk, BCP, AML, Regulatory — Thai bank/securities)
        "label": "Risk Manager",
        "skills": [
            {"name": "Risk Management (VaR, CVaR)",   "level": "Intermediate"},
            {"name": "Credit Analysis",               "level": "Intermediate"},
            {"name": "Regression Analysis",           "level": "Intermediate"},
            {"name": "Bloomberg Terminal",            "level": "Beginner"},
            {"name": "Monte Carlo Simulation",        "level": "Beginner"},
            {"name": "Econometrics",                  "level": "Beginner"},
        ],
        "expected_keywords": ["risk manager", "credit analyst", "actuarial", "compliance"],
    },
    {   # JD: Data Analyst – Finance (Collections analytics, SQL, Power BI — Thai bank)
        "label": "Data Analyst (Finance)",
        "skills": [
            {"name": "SQL (Data Querying)",                  "level": "Advanced"},
            {"name": "Python (Pandas, NumPy, Statsmodels)",  "level": "Intermediate"},
            {"name": "Power BI",                             "level": "Intermediate"},
            {"name": "Excel (Advanced: Solver, VBA, Power Query)", "level": "Intermediate"},
            {"name": "Statistical Modeling",                 "level": "Intermediate"},
            {"name": "Data Visualization",                   "level": "Intermediate"},
            {"name": "Regression Analysis",                  "level": "Beginner"},
        ],
        "expected_keywords": ["data analyst", "financial analyst", "fp&a", "data scientist"],
    },
    {   # JD: Wealth Manager (HNW clients, IC License, Portfolio, Estate — KBank/SCB)
        "label": "Wealth Manager",
        "skills": [
            {"name": "Portfolio Management",         "level": "Intermediate"},
            {"name": "Financial Planning",           "level": "Intermediate"},
            {"name": "Client Relationship Management","level": "Intermediate"},
            {"name": "Bloomberg Terminal",           "level": "Beginner"},
            {"name": "Investment Analysis",          "level": "Intermediate"},
            {"name": "Fixed Income Analysis",        "level": "Beginner"},
            {"name": "Communication",                "level": "Advanced"},
        ],
        "expected_keywords": ["wealth manager", "portfolio manager", "financial analyst"],
    },
    {   # JD: FP&A Analyst (Budgeting, Variance, SAP/Oracle, Power BI — Thai MNC)
        "label": "FP&A Analyst",
        "skills": [
            {"name": "Financial Modeling",                         "level": "Intermediate"},
            {"name": "Budgeting & Forecasting",                    "level": "Advanced"},
            {"name": "Excel (Advanced: Solver, VBA, Power Query)", "level": "Advanced"},
            {"name": "Variance Analysis",                          "level": "Intermediate"},
            {"name": "Power BI",                                   "level": "Intermediate"},
            {"name": "SAP / Oracle ERP",                           "level": "Beginner"},
            {"name": "Financial Statement Analysis",               "level": "Intermediate"},
        ],
        "expected_keywords": ["fp&a", "financial analyst", "corporate finance", "investment banker", "equity research"],
    },
    {   # JD: Compliance Officer/RegTech (AML/KYC, PDPA, BOT/SEC/AMLO — Thai FinTech)
        "label": "Compliance Officer (RegTech)",
        "skills": [
            {"name": "AML / KYC Compliance",                    "level": "Intermediate"},
            {"name": "Regulatory Frameworks (Basel III, MiFID II)", "level": "Intermediate"},
            {"name": "RegTech Tools (ComplyAdvantage)",         "level": "Beginner"},
            {"name": "SQL (Data Querying)",                     "level": "Intermediate"},
            {"name": "Report Writing",                          "level": "Intermediate"},
            {"name": "Policy Brief Writing",                    "level": "Beginner"},
            {"name": "Data Analytics",                          "level": "Beginner"},
        ],
        "expected_keywords": ["compliance", "risk manager", "financial analyst", "esg", "fintech product"],
    },
    {   # JD: FinTech PM (Agile, payments, BOT/SEC compliance, KPIs — Thai FinTech)
        "label": "FinTech Product Manager",
        "skills": [
            {"name": "Product Roadmapping",          "level": "Intermediate"},
            {"name": "Agile / Scrum Methodology",    "level": "Intermediate"},
            {"name": "Stakeholder Management",       "level": "Intermediate"},
            {"name": "Payment Systems Knowledge",    "level": "Intermediate"},
            {"name": "A/B Testing",                  "level": "Beginner"},
            {"name": "SQL (Data Querying)",          "level": "Beginner"},
            {"name": "Communication",                "level": "Advanced"},
        ],
        "expected_keywords": ["fintech product", "product manager", "financial analyst", "data analyst"],
    },
    {   # JD: Crypto/Digital Asset Analyst (On-chain, DeFi, Tokenomics — Bitkub/Binance TH)
        "label": "Crypto / Digital Asset Analyst",
        "skills": [
            {"name": "On-Chain Data Analysis (Dune Analytics, Glassnode)", "level": "Intermediate"},
            {"name": "DeFi Protocol Analysis",                             "level": "Intermediate"},
            {"name": "Tokenomics Modeling",                                "level": "Intermediate"},
            {"name": "Python (Pandas, NumPy, Statsmodels)",                "level": "Intermediate"},
            {"name": "Risk Management (VaR, CVaR)",                        "level": "Beginner"},
            {"name": "Behavioral Finance",                                 "level": "Beginner"},
        ],
        "expected_keywords": ["crypto", "digital asset", "blockchain", "web3", "derivatives trader", "risk manager"],
    },
    {   # JD: ESG/Sustainability Finance (GRI/TCFD, Climate Risk, Green Bond — PTT/EY TH)
        "label": "Sustainability / ESG Finance Analyst",
        "skills": [
            {"name": "ESG Reporting Frameworks (GRI, TCFD, ISSB)",    "level": "Intermediate"},
            {"name": "Green Bond / Sustainable Finance Analysis",      "level": "Intermediate"},
            {"name": "Environmental Economics",                        "level": "Intermediate"},
            {"name": "Data Visualization",                             "level": "Intermediate"},
            {"name": "Report Writing",                                 "level": "Intermediate"},
            {"name": "Regression Analysis",                            "level": "Beginner"},
        ],
        "expected_keywords": ["esg", "sustainability", "environmental"],
    },
]


def _dedup_top_jobs(top_jobs: list[dict], k: int = 3) -> list[dict]:
    """คืน top_jobs ที่ dedup job_title แล้ว (case-insensitive) เอาแค่ k อันแรก"""
    seen, unique = set(), []
    for job in top_jobs:
        title_key = job["job_title"].strip().lower()
        if title_key not in seen:
            seen.add(title_key)
            unique.append(job)
        if len(unique) == k:
            break
    return unique


def _top3_has_keyword(top_jobs: list[dict], keywords: list[str]) -> bool:
    """Hit@3 (deduped): อย่างน้อย 1 ใน 3 unique titles ตรงกับ keyword"""
    for job in _dedup_top_jobs(top_jobs, k=3):
        if any(kw in job["job_title"].lower() for kw in keywords):
            return True
    return False


def _count_keyword_hits(top_jobs: list[dict], keywords: list[str]) -> tuple[int, int]:
    """นับจำนวน unique titles ที่ตรง keyword และจำนวน unique titles ทั้งหมด (Precision@3 แท้ๆ)"""
    unique = _dedup_top_jobs(top_jobs, k=3)
    hits = sum(
        1 for job in unique
        if any(kw in job["job_title"].lower() for kw in keywords)
    )
    return hits, len(unique)


def kpi_precision_at_3(matcher: SkillMatcher) -> dict:
    print_header("KPI 2 — Precision@3 (Constructed Ground Truth, Deduped)")
    print(f"  ทดสอบด้วย {len(GROUND_TRUTH_PROFILES)} profiles ที่รู้คำตอบล่วงหน้า")
    print(f"  ★ dedup job_title ก่อนนับ — ดึง top_n=5 แล้วเอา 3 unique แรก")
    print(f"  [Hit@3]       = มีอย่างน้อย 1 ใน 3 unique ตรง (Pass/Fail)")
    print(f"  [Precision@3] = สัดส่วน (unique ที่ตรง / 3) เฉลี่ยทุก profile\n")
    print(f"  {'Profile':<35} {'Hit@3':<8} {'P@3':>6}  {'Uniq':>4}  Top-3 Unique Results")
    print(f"  {'-'*100}")

    hits, total = 0, len(GROUND_TRUTH_PROFILES)
    precision_scores = []

    for profile in GROUND_TRUTH_PROFILES:
        # ดึง top_n=5 แล้วค่อย dedup เพื่อให้ได้ 3 unique
        result   = matcher.match(profile["skills"], top_n=5)
        top_jobs = result.get("top_jobs", [])
        unique3  = _dedup_top_jobs(top_jobs, k=3)

        # Hit@3 (deduped)
        hit = any(
            any(kw in job["job_title"].lower() for kw in profile["expected_keywords"])
            for job in unique3
        )
        if hit:
            hits += 1

        # Precision@3 แท้ๆ (deduped)
        n_correct = sum(
            1 for job in unique3
            if any(kw in job["job_title"].lower() for kw in profile["expected_keywords"])
        )
        denom     = len(unique3)  # อาจได้น้อยกว่า 3 ถ้า matcher คืนน้อยกว่า 5
        precision = n_correct / denom if denom > 0 else 0.0
        precision_scores.append(precision)

        hit_tag  = "✓" if hit else "✗"
        top3_str = ", ".join(
            f"[{j['job_title']}]" if any(kw in j["job_title"].lower() for kw in profile["expected_keywords"])
            else j["job_title"]
            for j in unique3
        )
        dup_count = len(top_jobs) - len(set(j["job_title"].strip().lower() for j in top_jobs))
        dup_note  = f"(dup={dup_count})" if dup_count > 0 else ""
        print(f"  {profile['label']:<35} {hit_tag:<8} {precision:>5.2f}  {len(unique3):>4}  {top3_str} {dup_note}")

    hit_rate      = hits / total
    avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0.0

    print(f"\n  {'-' * 50}")
    print_result("Hit@3  (deduped, ≥1 ใน 3 ตรง)",     f"{hit_rate:.1%}  ({hits}/{total})",  hit_rate      >= 0.75)
    print_result("Precision@3 (deduped, เฉลี่ย)",     f"{avg_precision:.3f} / 1.000",       avg_precision >= (2/3))
    print_result("Target",                              "Hit@3 >= 75%, Precision@3 >= 66.7%",  None)
    return {"precision_at_3": hit_rate, "true_precision_at_3": avg_precision, "hits": hits, "total": total}


# ═══════════════════════════════════════════════════════════════
#  KPI 3 — Monotonicity Rate
# ═══════════════════════════════════════════════════════════════

def kpi_monotonicity(matcher: SkillMatcher, students: list[dict], sample: int) -> dict:
    print_header("KPI 3 — Monotonicity Rate")
    print(f"  ทดสอบ {sample} students: เพิ่ม missing skill -> rank ต้องไม่ลง\n")

    subset = random.sample(students, min(sample, len(students)))
    passed, failed, skipped = 0, 0, 0

    for student in subset:
        skills   = student["skills"]
        result   = matcher.match(skills, top_n=5)
        top_jobs = result.get("top_jobs", [])

        if not top_jobs:
            skipped += 1
            continue

        top_job = top_jobs[0]
        missing = top_job.get("missing_skills", [])
        if not missing:
            skipped += 1
            continue

        added_skill  = {"name": missing[0], "level": "Intermediate"}
        new_result   = matcher.match(skills + [added_skill], top_n=5)
        new_top_jobs = new_result.get("top_jobs", [])

        orig_rank = rank_of_title(top_job["job_title"], top_jobs)
        new_rank  = rank_of_title(top_job["job_title"], new_top_jobs)

        if new_rank is None or new_rank > (orig_rank or 0):
            failed += 1
        else:
            passed += 1

    tested = passed + failed
    rate   = passed / tested if tested > 0 else 0
    print_result("Monotonicity Rate", f"{rate:.1%}  ({passed}/{tested})", rate >= 0.85)
    print_result("Target",            ">= 85%", None)
    if skipped:
        print(f"  [SKIP] ข้าม {skipped} คน (top job ไม่มี missing_skills)")
    return {"monotonicity_rate": rate, "passed": passed, "tested": tested}


# ═══════════════════════════════════════════════════════════════
#  KPI 4 — Score Separation (Discriminability)
# ═══════════════════════════════════════════════════════════════

def kpi_score_separation(matcher: SkillMatcher, students: list[dict], sample: int) -> dict:
    print_header("KPI 4 — Score Separation (Discriminability)")
    print(f"  top1_score - top5_score เฉลี่ยบน {sample} students\n")

    subset  = random.sample(students, min(sample, len(students)))
    spreads = []
    skipped = 0

    for student in subset:
        result   = matcher.match(student["skills"], top_n=5)
        top_jobs = result.get("top_jobs", [])
        if len(top_jobs) < 5:
            skipped += 1
            continue
        spreads.append(top_jobs[0]["match_score"] - top_jobs[-1]["match_score"])

    if not spreads:
        print("  [FAIL] ไม่มีข้อมูลเพียงพอ")
        return {}

    avg_spread = sum(spreads) / len(spreads)
    pct_above  = sum(1 for s in spreads if s > 0.05) / len(spreads)

    print_result("Average Score Spread",          f"{avg_spread:.4f}", avg_spread > 0.05)
    print_result("% with spread > 0.05",          f"{pct_above:.1%}",  pct_above >= 0.60)
    print_result("Target", "avg > 0.05, >= 60% above threshold", None)
    if skipped:
        print(f"  [SKIP] ข้าม {skipped} คน (top_jobs < 5)")
    return {"avg_spread": avg_spread, "pct_above_threshold": pct_above}


# ═══════════════════════════════════════════════════════════════
#  KPI 5 — API Response Time
# ═══════════════════════════════════════════════════════════════

def kpi_response_time(matcher: SkillMatcher, students: list[dict], sample: int) -> dict:
    print_header("KPI 5 — API Response Time")
    print(f"  จับเวลา matcher.match() บน {sample} students\n")

    subset = random.sample(students, min(sample, len(students)))
    times  = []

    for student in subset:
        t0 = time.perf_counter()
        matcher.match(student["skills"], top_n=5)
        times.append(time.perf_counter() - t0)

    avg_ms = (sum(times) / len(times)) * 1000
    p95_ms = sorted(times)[int(len(times) * 0.95)] * 1000
    max_ms = max(times) * 1000

    print_result("Average response time", f"{avg_ms:.0f} ms", avg_ms < 2000)
    print_result("P95 response time",     f"{p95_ms:.0f} ms", p95_ms < 3000)
    print_result("Max response time",     f"{max_ms:.0f} ms", None)
    print_result("Target",                "avg < 2,000 ms", None)
    return {"avg_ms": avg_ms, "p95_ms": p95_ms, "max_ms": max_ms}


# ═══════════════════════════════════════════════════════════════
#  RAG Ground Truth Queries
# ═══════════════════════════════════════════════════════════════

# RAG queries จาก keyword จริงที่ปรากฏใน JD ไทย (FutureAlign.txt)
RAG_QUERY_PROFILES = [
    {   # JD keywords: Go, REST API, Docker, SQL, Node.js, Microservices, Agile
        "query": "software engineer go python rest api docker sql microservices git agile",
        "expected_keywords": ["software engineer", "backend", "full-stack", "fintech software"],
        "label": "Software Engineer",
    },
    {   # JD keywords: Python, ML models, Feature Engineering, ETL, Airflow, Spark, BigQuery
        "query": "data engineer data scientist python machine learning airflow spark etl bigquery sql",
        "expected_keywords": ["data scientist", "data engineer", "ml engineer", "data analyst"],
        "label": "Data / ML Engineer",
    },
    {   # JD keywords: LangChain, LangGraph, LLM, Prompt Engineering, RAG, Agentic AI, Kubernetes
        "query": "ai engineer llm langchain prompt engineering rag generative ai pytorch kubernetes",
        "expected_keywords": ["ai engineer", "ml engineer", "mlops"],
        "label": "AI / MLOps Engineer",
    },
    {   # JD keywords: Docker, Kubernetes, Terraform, GitLab CI, Azure, GCP, IaC, SAST/DAST
        "query": "devops cloud kubernetes docker terraform ci cd azure gcp infrastructure sre",
        "expected_keywords": ["devops", "site reliability engineer", "cloud architect"],
        "label": "DevOps / Cloud / SRE",
    },
    {   # JD keywords: SIEM, EDR, Penetration Testing, ISO 27001, NIST, Incident Response, OWASP
        "query": "cybersecurity penetration testing siem owasp vulnerability network security iso27001",
        "expected_keywords": ["cybersecurity", "security engineer", "appsec"],
        "label": "Cybersecurity / AppSec",
    },
    {   # JD keywords: Solidity, Spring Cloud, DeFi, Smart Contract, Cryptography, Dune, On-chain
        "query": "blockchain web3 solidity smart contract defi ethereum on-chain crypto tokenomics",
        "expected_keywords": ["blockchain", "web3", "smart contract", "crypto", "digital asset"],
        "label": "Blockchain / Web3 / Crypto",
    },
    {   # JD keywords: DCF, M&A, IPO, Bloomberg, Financial Modeling, SEC/SET, FP&A, Variance Analysis
        "query": "financial analyst investment banking valuation dcf bloomberg fpanda budgeting modeling excel",
        "expected_keywords": ["financial analyst", "investment banker", "fp&a", "corporate finance", "equity research"],
        "label": "Finance / IB / FP&A",
    },
    {   # JD keywords: GRI, TCFD, Green Bond, Climate Risk, AML, KYC, BOT, SEC, AMLO, PDPA
        "query": "esg sustainability gri tcfd green bond aml kyc compliance risk management reporting",
        "expected_keywords": ["esg", "sustainability", "risk manager", "compliance", "actuarial"],
        "label": "ESG / Risk / Compliance",
    },
]


# ═══════════════════════════════════════════════════════════════
#  KPI 6 — RAG Context Relevance
# ═══════════════════════════════════════════════════════════════

def kpi_rag_context_relevance(matcher: SkillMatcher) -> dict:
    print_header("KPI 6 — RAG Context Relevance")
    print(f"  ทดสอบ {len(RAG_QUERY_PROFILES)} queries — top-5 retrieved jobs ต้องมี keyword ที่ถูก\n")

    hits, total = 0, len(RAG_QUERY_PROFILES)
    relevance_scores = []

    for profile in RAG_QUERY_PROFILES:
        result        = matcher.rag_search(profile["query"], top_k_jobs=5, top_k_alumni=3)
        retrieved_jobs = result.get("relevant_jobs", [])

        hit = any(
            any(kw in job["job_title"].lower() for kw in profile["expected_keywords"])
            for job in retrieved_jobs
        )
        if hit:
            hits += 1

        scores    = [j["relevance"] for j in retrieved_jobs]
        avg_rel   = sum(scores) / len(scores) if scores else 0.0
        relevance_scores.append(avg_rel)

        tag  = "[HIT ]" if hit else "[MISS]"
        top3 = [j["job_title"] for j in retrieved_jobs[:3]]
        print(f"  {tag} {profile['label']}")
        print(f"         Top-3: {', '.join(top3)}  (avg relevance: {avg_rel:.4f})")

    hit_rate     = hits / total
    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0

    print(f"\n  {'-' * 50}")
    print_result("RAG Keyword Hit Rate",    f"{hit_rate:.1%}  ({hits}/{total})", hit_rate >= 0.75)
    print_result("Avg Retrieval Relevance", f"{avg_relevance:.4f}",             avg_relevance >= 0.70)
    print_result("Target", "Hit Rate >= 75%, Avg Relevance >= 0.70", None)
    return {"rag_hit_rate": hit_rate, "avg_relevance": avg_relevance, "hits": hits, "total": total}


# ═══════════════════════════════════════════════════════════════
#  KPI 7 — RAG Retrieval Diversity
# ═══════════════════════════════════════════════════════════════

JOB_CATEGORY_KEYWORDS = [
    ("swe",        ["software engineer", "backend", "full-stack", "full stack", "fintech software"]),
    ("data",       ["data scientist", "data analyst", "data engineer", "ml engineer", "mlops"]),
    ("ai_ml",      ["machine learning", "deep learning", "ai engineer", "computer vision", "mlops"]),
    ("devops",     ["devops", "cloud architect", "site reliability", "sre"]),
    ("security",   ["cybersecurity", "security engineer", "appsec", "penetration"]),
    ("blockchain", ["blockchain", "web3", "smart contract", "crypto", "digital asset"]),
    ("finance",    ["financial analyst", "investment banker", "corporate finance", "equity research",
                    "derivatives trader", "credit analyst", "portfolio manager", "fp&a",
                    "wealth manager", "fintech product"]),
    ("esg_risk",   ["esg", "sustainability", "risk manager", "compliance", "actuarial"]),
    ("quant",      ["quantitative", "quantitative researcher"]),
    ("game",       ["game developer"]),
    ("embedded",   ["embedded systems"]),
    ("economist",  ["economist"]),
]


def _categorize_job(title: str) -> str:
    t = title.lower()
    for cat, keywords in JOB_CATEGORY_KEYWORDS:
        if any(kw in t for kw in keywords):
            return cat
    return "other"


def kpi_rag_diversity(matcher: SkillMatcher) -> dict:
    print_header("KPI 7 — RAG Retrieval Diversity")
    print(f"  ตรวจว่า retrieved jobs หลากหลาย — ไม่ return job title เดิมซ้ำๆ\n")
    print(f"  {'Query':<35} {'Jobs':>4}  {'Categories':>10}  {'Diversity':>10}")
    print(f"  {'-' * 65}")

    diversity_scores = []

    for profile in RAG_QUERY_PROFILES:
        result        = matcher.rag_search(profile["query"], top_k_jobs=5, top_k_alumni=3)
        retrieved_jobs = result.get("relevant_jobs", [])

        categories = set(_categorize_job(j["job_title"]) for j in retrieved_jobs)
        n_jobs     = len(retrieved_jobs)
        n_cats     = len(categories)
        diversity  = n_cats / n_jobs if n_jobs > 0 else 0.0
        diversity_scores.append(diversity)

        print(f"  {profile['label']:<35} {n_jobs:>4}  {n_cats:>10}  {diversity:>10.2f}")

    avg_diversity = sum(diversity_scores) / len(diversity_scores) if diversity_scores else 0
    pct_diverse   = sum(1 for d in diversity_scores if d >= 0.40) / len(diversity_scores)

    print(f"\n  {'-' * 65}")
    print_result("Avg Diversity (categories/jobs)",  f"{avg_diversity:.2f}", avg_diversity >= 0.40)
    print_result("% queries with diversity >= 0.40", f"{pct_diverse:.1%}",   pct_diverse >= 0.60)
    print_result("Target", "avg >= 0.40, >= 60% queries diverse", None)
    return {"avg_diversity": avg_diversity, "pct_diverse": pct_diverse}


# ═══════════════════════════════════════════════════════════════
#  KPI 8 — RAG Alumni Retrieval Accuracy (Hit@3)
# ═══════════════════════════════════════════════════════════════

def kpi_rag_alumni_accuracy(matcher: SkillMatcher, alumni: list[dict], sample: int) -> dict:
    print_header("KPI 8 — RAG Alumni Retrieval Accuracy (Hit@3)")
    print(f"  Query ด้วย first_job_title ของ alumni → ตรวจว่า retrieved alumni มี title ที่ match\n")

    subset = random.sample(alumni, min(sample, len(alumni)))
    hit3, total, skipped = 0, 0, 0

    for alum in subset:
        job_title = alum["first_job_title"]
        if not job_title:
            skipped += 1
            continue

        result            = matcher.rag_search(job_title, top_k_jobs=5, top_k_alumni=3)
        retrieved_alumni  = result.get("relevant_alumni", [])

        found = any(
            title_match(ra["first_job_title"], job_title)
            for ra in retrieved_alumni[:3]
        )
        if found:
            hit3 += 1
        total += 1

    rate = hit3 / total if total > 0 else 0
    print_result("Alumni Retrieval Hit@3", f"{rate:.1%}  ({hit3}/{total})", rate >= 0.50)
    print_result("Target", ">= 50%", None)
    if skipped:
        print(f"  [SKIP] ข้าม {skipped} คน")
    return {"rag_alumni_hit3": rate, "total": total}


# ═══════════════════════════════════════════════════════════════
#  KPI 9 — RAG Response Time
# ═══════════════════════════════════════════════════════════════

def kpi_rag_response_time(matcher: SkillMatcher) -> dict:
    print_header("KPI 9 — RAG Response Time")
    print(f"  จับเวลา rag_search() บน {len(RAG_QUERY_PROFILES)} queries\n")

    times = []
    for profile in RAG_QUERY_PROFILES:
        t0 = time.perf_counter()
        matcher.rag_search(profile["query"], top_k_jobs=5, top_k_alumni=3)
        times.append(time.perf_counter() - t0)

    avg_ms = (sum(times) / len(times)) * 1000
    p95_idx = max(0, int(len(times) * 0.95) - 1)
    p95_ms  = sorted(times)[p95_idx] * 1000
    max_ms  = max(times) * 1000

    print_result("Average response time", f"{avg_ms:.0f} ms", avg_ms < 1000)
    print_result("P95 response time",     f"{p95_ms:.0f} ms", p95_ms < 2000)
    print_result("Max response time",     f"{max_ms:.0f} ms", None)
    print_result("Target", "avg < 1,000 ms", None)
    return {"rag_avg_ms": avg_ms, "rag_p95_ms": p95_ms, "rag_max_ms": max_ms}


# ═══════════════════════════════════════════════════════════════
#  Summary
# ═══════════════════════════════════════════════════════════════

def print_summary(results: dict):
    print_header("SUMMARY")
    targets = {
        # ── Matching Engine KPIs ──────────────────────────────────
        "backtest_h1":      ("Backtesting Hit@1",              lambda r: r.get("hit1", 0),              0.60,  ".1%", False),
        "backtest_mrr":     ("Backtesting MRR",                lambda r: r.get("mrr",  0),              0.70,  ".3f", False),
        "precision":        ("Precision@3 (avg, deduped)",      lambda r: r.get("true_precision_at_3", 0), 2/3,  ".1%", False),
        "precision_true":   ("Precision@3 Hit@3 (≥1 in top-3)", lambda r: r.get("precision_at_3", 0),    0.75, ".1%", False),
        "monotonic":        ("Monotonicity Rate",              lambda r: r.get("monotonicity_rate", 0), 0.85,  ".1%", False),
        "separation":       ("Score Separation (avg)",         lambda r: r.get("avg_spread", 0),        0.05,  ".4f", False),
        "response":         ("Matcher Response Time (avg)",    lambda r: r.get("avg_ms", 9999),         2000,  ".0f", True),
        # ── RAG KPIs ─────────────────────────────────────────────
        "rag_relevance":    ("RAG Context Relevance (hit%)",   lambda r: r.get("rag_hit_rate", 0),      0.75,  ".1%", False),
        "rag_avg_rel":      ("RAG Avg Retrieval Relevance",    lambda r: r.get("avg_relevance", 0),     0.70,  ".4f", False),
        "rag_diversity":    ("RAG Diversity Score (avg)",      lambda r: r.get("avg_diversity", 0),     0.40,  ".2f", False),
        "rag_alumni":       ("RAG Alumni Retrieval Hit@3",     lambda r: r.get("rag_alumni_hit3", 0),   0.50,  ".1%", False),
        "rag_response":     ("RAG Response Time (avg)",        lambda r: r.get("rag_avg_ms", 9999),     1000,  ".0f", True),
    }
    src_map = {
        "backtest_h1": "backtest", "backtest_mrr": "backtest",
        "precision": "precision", "precision_true": "precision",
        "rag_relevance": "rag_relevance", "rag_avg_rel": "rag_relevance",
        "rag_diversity": "rag_diversity",
        "rag_alumni": "rag_alumni",
        "rag_response": "rag_response",
    }
    for key, (label, fn, threshold, fmt, lower_is_better) in targets.items():
        src_key = src_map.get(key, key)
        if src_key not in results:
            continue
        val   = fn(results[src_key])
        pass_ = val <= threshold if lower_is_better else val >= threshold
        unit  = " ms" if lower_is_better else ""
        print_result(label, f"{val:{fmt}}{unit}", pass_)
    print()


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Career Matcher KPI Evaluation")
    parser.add_argument("--sample", type=int, default=50,
                        help="จำนวน sample ต่อ KPI (default: 50)")
    parser.add_argument("--kpi", type=str, default="all",
                        choices=[
                            "all", "backtest", "precision", "monotonic", "separation", "response",
                            "rag_relevance", "rag_diversity", "rag_alumni", "rag_response", "rag",
                        ],
                        help="เลือก KPI ที่ต้องการรัน ('rag' รันทั้ง 4 RAG KPIs)")
    args = parser.parse_args()

    print("\n  Loading SkillMatcher...")
    matcher  = SkillMatcher()
    alumni   = load_alumni(BACKTEST_ALUMNI_PATH)   # holdout set — no leakage
    students = load_students(STUDENT_PATH)
    print(f"  Backtest alumni (holdout): {len(alumni)} | Students: {len(students)}\n")

    results = {}
    run_all = args.kpi == "all"
    run_rag = args.kpi == "rag"

    if run_all or args.kpi == "backtest":
        results["backtest"]      = kpi_backtest(matcher, alumni, sample=len(alumni))

    if run_all or args.kpi == "precision":
        results["precision"]     = kpi_precision_at_3(matcher)

    if run_all or args.kpi == "monotonic":
        results["monotonic"]     = kpi_monotonicity(matcher, students, sample=args.sample)

    if run_all or args.kpi == "separation":
        results["separation"]    = kpi_score_separation(matcher, students, sample=args.sample)

    if run_all or args.kpi == "response":
        results["response"]      = kpi_response_time(matcher, students, sample=min(args.sample, 20))

    if run_all or run_rag or args.kpi == "rag_relevance":
        results["rag_relevance"] = kpi_rag_context_relevance(matcher)

    if run_all or run_rag or args.kpi == "rag_diversity":
        results["rag_diversity"] = kpi_rag_diversity(matcher)

    if run_all or run_rag or args.kpi == "rag_alumni":
        results["rag_alumni"]    = kpi_rag_alumni_accuracy(matcher, alumni, sample=min(args.sample, 30))

    if run_all or run_rag or args.kpi == "rag_response":
        results["rag_response"]  = kpi_rag_response_time(matcher)

    if run_all or run_rag:
        print_summary(results)


if __name__ == "__main__":
    main()

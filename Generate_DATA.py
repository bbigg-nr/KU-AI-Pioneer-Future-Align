"""
Synthetic Student Dataset Generator
Based on:
  - CPE (Computer Engineering) curriculum: Kasetsart University B.Eng. 2565
  - ECON (Economics) curriculum:           Kasetsart University B.Econ. 2565

Outputs three CSV files:
  synthetic_student_dataset_500_clean.csv
  alumni_dataset_500.csv
  labor_market_dataset_with_salary.csv
"""

import pandas as pd
import numpy as np
import json
import random
import os
from dotenv import load_dotenv

load_dotenv()

random.seed(42)
np.random.seed(42)

# ─────────────────────────────────────────────
# 1. COURSE DEFINITIONS  (from actual curricula)
# ─────────────────────────────────────────────

# ---------- CPE Core Courses (บังคับ) ----------
CPE_CORE_COURSES = [
    # Science & Math core
    ("01204215", "Mathematical Foundations for Computer Engineers"),
    ("01403114", "Lab: Fundamentals of General Chemistry"),
    ("01403117", "Fundamentals of General Chemistry"),
    ("01417167", "Engineering Mathematics I"),
    ("01417168", "Engineering Mathematics II"),
    ("01420111", "General Physics I"),
    ("01420113", "Physics Laboratory I"),
    # Engineering core
    ("01204216", "Probability and Statistics for Computer Engineers"),
    ("01204371", "Transform Techniques in Signal Processing"),
    ("01205211", "Electric Circuit Analysis I"),
    ("01205242", "Electronic Circuits and Systems I"),
    ("01208111", "Engineering Drawing"),
    # Software group
    ("01204113", "Computer and Programming for Computer Engineers"),
    ("01204212", "Abstract Data Types and Problem Solving"),
    ("01204214", "Problem Solving Laboratory"),
    ("01204332", "Operating Systems"),
    ("01204341", "Software Engineering"),
    ("01204437", "Computer System Security"),
    # System infrastructure group
    ("01204211", "Discrete Mathematics and Theory of Computation"),
    ("01204313", "Algorithm Design and Analysis"),
    ("01204325", "Data Communication and Computer Networks"),
    ("01204421", "Computer Networks"),
    # Hardware & Architecture group
    ("01204114", "Introduction to Computer Hardware Development"),
    ("01204222", "Digital Systems Design"),
    ("01204223", "Practicum in Computer Engineering"),
    ("01204224", "Logic Circuit Laboratory"),
    ("01204225", "Computer Architecture and Organization"),
    ("01204322", "Embedded System"),
    ("01204323", "Electronic Laboratory for Embedded Systems"),
    ("01204324", "Computer System Laboratory"),
    # Professional skills group
    ("01204271", "Introduction to Computer Engineering"),
    ("01204391", "Career and Social Skill Development Laboratory"),
    ("01204495", "Computer Engineering Project Preparation"),
    ("01204499", "Computer Engineering Project"),
]

# ---------- CPE Major Electives (วิชาเฉพาะเลือก) ----------
CPE_ELECTIVE_COURSES = [
    ("01204213", "Theory of Computation"),
    ("01204314", "Statistics for Computer Engineering Applications"),
    ("01204331", "System Software Interface"),
    ("01204342", "Managing Software Development"),
    ("01204352", "Laws and Ethics in Information Technology"),
    ("01204411", "Quantum Computing"),
    ("01204422", "Basic Networks and Network Configuration Laboratory"),
    ("01204423", "Network Kernel Architectures and Implementation"),
    ("01204425", "Internet System Programming"),
    ("01204426", "Advanced Network and Network Configuration"),
    ("01204427", "Computer System and Network Security"),
    ("01204428", "Wireless Embedded Systems"),
    ("01204429", "Wireless Networks and Simulation"),
    ("01204432", "Object-Oriented Design"),
    ("01204433", "Programming Language Translation"),
    ("01204434", "Parallel and Distributed Computing Systems"),
    ("01204435", "Programming Language Concepts"),
    ("01204436", "Real-time System Engineering"),
    ("01204438", "Enterprise Application Architecture"),
    ("01204451", "Database System Design"),
    ("01204452", "Information Technology Management"),
    ("01204453", "Web Information Retrieval and Mining"),
    ("01204454", "Management of Technology and Innovation"),
    ("01204456", "Social Networks Data Mining"),
    ("01204457", "Semantic Web Technology"),
    ("01204458", "Introduction to Computational Finance"),
    ("01204461", "Artificial Intelligence"),
    ("01204462", "Introduction to Expert Systems"),
    ("01204463", "Introduction to Natural Language Processing"),
    ("01204464", "Computer Vision"),
    ("01204465", "Introduction to Data Mining and Knowledge Discovery"),
    ("01204466", "Deep Learning"),
    ("01204467", "Introduction to Robotics"),
    ("01204472", "Numerical Computation"),
    ("01204473", "Mechatronic System and Control"),
    ("01204481", "Foundations of Computer Graphics"),
    ("01204482", "Computer-Human Interfaces"),
    ("01204483", "Digital Image Processing"),
    ("01219312", "Functional Programming"),
    ("01219322", "Electronic Commerce Engineering"),
    ("01219325", "Software Development Security"),
    ("01219332", "Data Warehouse"),
    ("01219333", "Introduction to Data Mining"),
    ("01219334", "Transaction Processing"),
    ("01219335", "Data Acquisition and Integration"),
    ("01219336", "Advanced Database"),
    ("01219343", "Software Testing"),
    ("01219344", "Mobile Software Development"),
    ("01219349", "Digital Game Production"),
    ("01219351", "Web Application Development"),
    ("01219361", "Business Intelligence"),
    ("01219362", "Machine Learning"),
    ("01219364", "Knowledge Discovery"),
    ("01219367", "Data Analytics"),
    ("01219421", "Cloud Computing Technology and Management"),
    ("01219422", "Distributed Systems"),
    ("01219451", "Web Services Technology"),
    ("01219452", "Principle of Information Security"),
    ("01219461", "Big Data Engineering"),
    ("01219482", "Data Visualization"),
    ("01219492", "Software Entrepreneurship"),
    ("01204351", "Database Systems"),
    ("01205314", "Digital Signal Processing"),
    ("01205338", "VLSI Systems"),
    ("01206321", "Operations Research for Engineers I"),
    ("01206323", "Operations Research for Engineers II"),
    ("01200311", "Communication Skills in Engineering I"),
]

# ---------- ECON Core Courses (บังคับ) ----------
ECON_CORE_COURSES = [
    ("01101171", "Mathematical Economics I"),
    ("01101181", "Microeconomics I"),
    ("01101182", "Macroeconomics I"),
    ("01101231", "Labour and Industrial Economics"),
    ("01101271", "Mathematical Economics II"),
    ("01101272", "Economics Statistics I"),
    ("01101273", "Introduction to Computational Economics"),
    ("01101281", "Microeconomics II"),
    ("01101282", "Macroeconomics II"),
    ("01101283", "Economic Thinking"),
    ("01101284", "Economics of Natural Resources and Public Policy"),
    ("01101312", "Thai Economy"),
    ("01101371", "Economics Statistics II"),
    ("01101372", "Econometrics I"),
    ("01101375", "Operations Research for Economic Applications"),
    ("01101381", "History of Economic Thought"),
    ("01101384", "Economics of Money and Banking"),
    ("01101385", "Economic Development and International Trade"),
    ("01101491", "Research Methods in Economics"),
    ("01101497", "Seminar"),
    ("01130101", "General Accounting"),
]

# ---------- ECON Major Electives (วิชาเฉพาะเลือก) ----------
ECON_ELECTIVE_COURSES = [
    ("01101411", "Regional Economics"),
    ("01101412", "Project Preparation and Evaluation"),
    ("01101413", "Economic Administration"),
    ("01101414", "Economic Development of ASEAN Countries"),
    ("01101415", "Economics of Poverty and Inequality"),
    ("01101417", "Comparative Economic Development"),
    ("01101421", "Business Economic Forecasting"),
    ("01101422", "Economics of Financial Risk Management"),
    ("01101423", "Marketing Business Economics"),
    ("01101424", "Business Economics of Strategy"),
    ("01101425", "Business Economic Ethics"),
    ("01101426", "Real Estate Business Economics"),
    ("01101431", "Economics of Industrialization"),
    ("01101432", "Game Theory and Its Applications in Industrial Economics"),
    ("01101433", "Economics of Labour Market"),
    ("01101435", "Human Capital and Education Economics"),
    ("01101437", "International Trade Theory and Policy"),
    ("01101438", "International Finance and Exchange Rate"),
    ("01101441", "Public Economics"),
    ("01101444", "Environmental Economics"),
    ("01101445", "Urban and Housing Economics"),
    ("01101451", "Economics of Industrial Organization"),
    ("01101452", "Monetary Theory and Policy"),
    ("01101454", "Financial Economics"),
    ("01101455", "Investment Analysis"),
    ("01101456", "Behavioral Finance"),
    ("01101458", "Economics of Government Expenditure"),
    ("01101459", "Economics of Government Revenue"),
    ("01101461", "Economic Valuation of Natural Resources"),
    ("01101462", "Energy Resources Economics"),
    ("01101471", "Mathematical Programming for Economic Applications"),
    ("01101473", "Input-Output Analysis"),
    ("01101474", "Econometrics II"),
    ("01101475", "Mathematical Economics IV"),
    ("01101476", "Microeconometrics"),
    ("01101478", "Intermediate Computational Economics"),
    ("01101481", "Welfare Economics"),
    ("01101482", "Economic Growth and Stability"),
    ("01101483", "Political Economics"),
    ("01101485", "Buddhist Economics"),
    ("01101486", "Behavioural Economics"),
    ("01101496", "Selected Topics in Economics"),
    ("01101498", "Special Problems"),
]

# ─────────────────────────────────────────────
# 2. SKILLS POOLS  (50-100 skills per faculty)
# ─────────────────────────────────────────────

CPE_HARD_SKILLS = [
    # Languages
    "Python", "Java", "C/C++", "JavaScript", "TypeScript", "Go", "Rust",
    "Kotlin", "Swift", "Scala", "R", "MATLAB", "Bash/Shell Scripting",
    "Assembly Language", "SQL", "NoSQL (MongoDB)", "GraphQL",
    # Frameworks & Libraries
    "React", "Vue.js", "Angular", "Node.js", "Django", "Flask", "FastAPI",
    "Spring Boot", "Express.js", "Next.js", "TensorFlow", "PyTorch", "Keras",
    "Scikit-learn", "OpenCV", "Hugging Face Transformers", "LangChain",
    # Data & ML
    "Machine Learning", "Deep Learning", "Natural Language Processing",
    "Computer Vision", "Reinforcement Learning", "Data Engineering",
    "Feature Engineering", "Model Deployment (MLOps)", "A/B Testing",
    "Time Series Analysis", "Statistical Modeling",
    # Databases
    "PostgreSQL", "MySQL", "Redis", "Elasticsearch", "Apache Kafka",
    "Apache Spark", "Hadoop", "dbt (Data Build Tool)", "Airflow",
    # DevOps & Cloud
    "Docker", "Kubernetes", "CI/CD Pipelines", "GitHub Actions",
    "Terraform", "Ansible", "AWS (EC2, S3, Lambda)", "GCP (BigQuery, GKE)",
    "Azure (AKS, Functions)", "Prometheus & Grafana", "Nginx", "Linux System Admin",
    # Security
    "Penetration Testing", "Cryptography", "OWASP Top 10",
    "Network Security", "Vulnerability Assessment", "SIEM Tools",
    # Systems & Embedded
    "Embedded Systems (Arduino/Raspberry Pi)", "FPGA Programming",
    "Real-Time Operating Systems (RTOS)", "TCP/IP Networking",
    "Microcontroller Programming", "IoT Development",
    # Tools
    "Git / Version Control", "JIRA / Agile Tools", "Figma (UI/UX)",
    "Postman (API Testing)", "Jupyter Notebook", "VS Code",
    # Blockchain / Web3
    "Solidity", "Ethereum / EVM", "Web3.js / Ethers.js",
    "Smart Contract Development", "Hardhat / Foundry",
    "DeFi Protocols", "IPFS / Decentralized Storage",
    "JavaScript / TypeScript", "Zero-Knowledge Proofs (ZKP)",
    # AR/VR
    "Unity 3D", "Unreal Engine", "WebXR / WebGL",
    "3D Modeling (Blender)", "Spatial Computing (Meta Quest / Apple Vision Pro)",
    "Shader Programming", "C#",
    # MLOps / AI Platform
    "LLM Fine-tuning", "Vector Databases (Pinecone/Weaviate)",
    "RAG (Retrieval-Augmented Generation)", "Prompt Engineering",
    "MLflow / Weights & Biases",
    # Platform / SRE
    "Service Mesh (Istio)", "Internal Developer Platforms (IDP)",
    "SLO / SLA / SLI Design", "Chaos Engineering (Chaos Monkey)",
    "Incident Management",
    # AppSec
    "SAST / DAST Tools", "Secure Code Review", "Burp Suite",
    "Cloud Security (AWS / GCP)",
    # FinTech
    "Payment Systems (ISO 20022, SWIFT)", "PCI-DSS Compliance",
    "Microservices Architecture", "REST API Design",
    # Data Structures (ใช้ใน Software Engineer JD)
    "Data Structures & Algorithms",
]

CPE_SOFT_SKILLS = [
    "Communication", "Teamwork & Collaboration", "Problem Solving",
    "Critical Thinking", "Leadership", "Project Management",
    "Agile / Scrum Methodology", "Time Management", "Presentation Skills",
    "Technical Writing", "Mentoring", "Cross-functional Collaboration",
    "Self-directed Learning", "Creativity & Innovation", "Adaptability",
]

ECON_HARD_SKILLS = [
    # Quantitative & Econometrics
    "Econometrics", "Microeconometrics", "Time Series Forecasting",
    "Panel Data Analysis", "Regression Analysis", "Bayesian Inference",
    "Monte Carlo Simulation", "Game Theory", "Input-Output Analysis",
    "Causal Inference (DiD, RDD, IV)", "Stochastic Modeling",
    # Programming & Data Tools
    "R (ggplot2, dplyr, tidyr)", "Python (Pandas, NumPy, Statsmodels)",
    "Stata", "EViews", "MATLAB (Economic Modeling)", "SPSS",
    "Excel (Advanced: Solver, VBA, Power Query)", "Power BI", "Tableau",
    "SQL (Data Querying)", "GAMS (Optimization)", "Julia (Economic Modeling)",
    # Finance & Investment
    "Financial Modeling", "Valuation (DCF, Comps)", "Portfolio Management",
    "Fixed Income Analysis", "Derivatives Pricing (Black-Scholes)",
    "Bloomberg Terminal", "Reuters Eikon", "Risk Management (VaR, CVaR)",
    "Investment Banking (M&A Modeling)", "Credit Analysis",
    "Equity Research", "Quantitative Trading", "Factor Investing",
    "Capital Budgeting", "Financial Statement Analysis",
    # Policy & Development
    "Cost-Benefit Analysis (CBA)", "Public Finance",
    "Development Economics", "Environmental Economics",
    "Social Impact Evaluation", "Poverty Analysis",
    "Policy Brief Writing", "Survey Design & Analysis",
    "National Accounts Analysis", "International Trade Policy",
    # Research & Academic
    "Literature Review", "Academic Paper Writing",
    "Hypothesis Testing", "Research Design", "Data Visualization",
    "Economic Forecasting", "Macro Modeling (DSGE, CGE)",
    "Labor Market Analysis", "Industrial Organization Analysis",
    # Sectoral
    "Real Estate Valuation", "Energy Economics",
    "Agricultural Economics", "Healthcare Economics",
    "Regulatory Economics", "Behavioral Economics",
    "Central Banking Operations", "Tax Policy Analysis",
    # Crypto / Digital Asset
    "On-Chain Data Analysis (Dune Analytics, Glassnode)",
    "DeFi Protocol Analysis", "Tokenomics Modeling",
    # ESG / Sustainability
    "ESG Reporting Frameworks (GRI, TCFD, ISSB)",
    "Green Bond / Sustainable Finance Analysis",
    "Social Impact Evaluation", "Sustainability Reporting",
    # FinTech PM
    "Product Roadmapping", "Open Banking / API Finance",
    "Payment Systems Knowledge", "A/B Testing",
    # Compliance / RegTech
    "AML / KYC Compliance", "Regulatory Frameworks (Basel III, MiFID II)",
    "RegTech Tools (ComplyAdvantage)",
    # FP&A
    "Budgeting & Forecasting", "Variance Analysis", "SAP / Oracle ERP",
    # Supply Chain
    "Supply Chain Modeling",
    # Wealth
    "Financial Planning", "Tax Planning", "Estate Planning",
    "Client Relationship Management",
    # Behavioral
    "Experimental Economics", "Nudge Theory",
    # Research
    "Literature Review", "Research Design", "Report Writing",
]

ECON_SOFT_SKILLS = [
    "Communication", "Analytical Thinking", "Report Writing",
    "Presentation Skills", "Critical Thinking", "Problem Solving",
    "Leadership", "Teamwork & Collaboration", "Research Skills",
    "Project Management", "Negotiation", "Stakeholder Management",
    "Cross-cultural Communication", "Attention to Detail", "Adaptability",
]

# Combined skill pools per faculty
CPE_ALL_SKILLS   = CPE_HARD_SKILLS + CPE_SOFT_SKILLS
ECON_ALL_SKILLS  = ECON_HARD_SKILLS + ECON_SOFT_SKILLS

# ─────────────────────────────────────────────
# 3. ACTIVITIES  (role → project templates)
# ─────────────────────────────────────────────

CPE_ACTIVITY_TEMPLATES = [
    ("Team Lead",               "KU Hackathon"),
    ("Backend Developer",       "Senior Capstone Project"),
    ("AI Research Intern",      "NECTEC AI Lab"),
    ("Competitor",              "ICPC Programming Contest"),
    ("Full-Stack Developer",    "Student Startup (YC-backed)"),
    ("Data Engineer Intern",    "Agoda Data Platform"),
    ("Cybersecurity Analyst",   "NCSA Thailand CTF"),
    ("Cloud Intern",            "SCB Tech Group"),
    ("DevOps Engineer Intern",  "LINE Thailand"),
    ("ML Engineer Intern",      "Grab Thailand"),
    ("Frontend Developer",      "KBTG Digital Banking"),
    ("Embedded Systems Dev",    "Thai IoT Startup"),
    ("Researcher",              "KU Computer Vision Lab"),
    ("Software Intern",         "True Digital Group"),
    ("Teaching Assistant",      "CPE Department - Data Structures"),
    ("Product Manager Intern",  "Wongnai / LINE MAN"),
    ("Open-Source Contributor", "GitHub Projects"),
    ("Workshop Facilitator",    "KU Coding Club"),
    ("Blockchain Developer",    "Web3 Thailand Hackathon"),
    ("Game Developer Intern",   "Yggdrazil Group"),
    # New activities for trending careers
    ("MLOps Engineer Intern",   "Sertis AI"),
    ("LLM App Developer",       "AI Builders Thailand"),
    ("Smart Contract Dev",      "Bitkub Chain Hackathon"),
    ("XR Developer",            "Meta Spark AR Challenge"),
    ("Platform Eng Intern",     "Agoda Engineering"),
    ("AppSec Engineer Intern",  "Kasikorn Bank CyberSec"),
    ("FinTech Dev Intern",      "SCB 10X"),
    ("SRE Intern",              "Grab Thailand SRE Team"),
]

ECON_ACTIVITY_TEMPLATES = [
    ("Research Assistant",      "Bank of Thailand (BOT)"),
    ("Equity Analyst Intern",   "Bualuang Securities"),
    ("Winner",                  "CFA Research Challenge Thailand"),
    ("Member",                  "KU Investment Club"),
    ("Economic Analyst",        "TDRI Policy Research"),
    ("Quantitative Analyst",    "Kasikorn Asset Management"),
    ("M&A Intern",              "Phatra Capital"),
    ("Teaching Assistant",      "ECON Department - Econometrics"),
    ("Data Analyst Intern",     "SCB EIC"),
    ("Policy Research Intern",  "NESDC Thailand"),
    ("Risk Analyst Intern",     "Krungsri Bank"),
    ("Corporate Finance Intern","PTT Global Chemical"),
    ("ESG Analyst Intern",      "Gulf Energy Development"),
    ("Bond Trader Intern",      "Finansa Capital"),
    ("Country Risk Analyst",    "Export-Import Bank of Thailand"),
    ("Startup Advisor",         "DTAC Accelerate Program"),
    ("Budget Analyst Intern",   "Ministry of Finance Thailand"),
    ("International Trade RA",  "WTO Academic Chair KU"),
    ("Behavioral Research RA",  "KU Experimental Economics Lab"),
    ("FinTech Intern",          "KASIKORN Business-Technology Group"),
    # New activities for trending careers
    ("Crypto Analyst Intern",   "Bitkub Exchange"),
    ("FinTech PM Intern",       "Rabbit Finance"),
    ("Wealth Mgmt Intern",      "SCB Julius Baer"),
    ("FP&A Intern",             "Central Group Finance"),
    ("RegTech Intern",          "SEC Thailand"),
    ("Supply Chain Analyst",    "CP Group Strategy"),
    ("Green Finance RA",        "Climate Policy Initiative"),
    ("Behavioral Econ RA",      "NIDA Economic Research"),
]

# ─────────────────────────────────────────────
# 4. CAREER PATHS
# ─────────────────────────────────────────────

CPE_CAREERS  = [
    # Core engineering
    "Software Engineer", "Data Scientist", "AI/ML Engineer",
    "Data Engineer", "DevOps / SRE Engineer", "Cloud Architect",
    "Cybersecurity Engineer", "Backend Engineer", "Full-Stack Developer",
    "Embedded Systems Engineer", "Computer Vision Engineer",
    "NLP Engineer", "Quantitative Developer", "Game Developer",
    "Product Manager (Technical)", "Robotics Engineer",
    # Trending 2025-2026
    "MLOps Engineer",
    "AI Platform Engineer",
    "Platform Engineer",
    "Security Engineer (AppSec)",
    "Blockchain / Web3 Developer",
    "AR/VR Developer",
    "Site Reliability Engineer",
    "FinTech Software Engineer",
]

ECON_CAREERS = [
    # Core finance/econ
    "Quantitative Researcher", "Financial Analyst", "Investment Banker",
    "Risk Manager", "Policy Analyst", "Data Analyst (Finance)",
    "Portfolio Manager", "Equity Research Analyst", "Economist",
    "Derivatives Trader", "Credit Analyst", "ESG Analyst",
    "Actuarial Analyst", "Corporate Finance Analyst",
    "Economic Development Consultant", "Regulatory Economist",
    # Trending 2025-2026
    "FinTech Product Manager",
    "Crypto / Digital Asset Analyst",
    "Wealth Manager",
    "FP&A Analyst",
    "Compliance Officer (RegTech)",
    "Supply Chain Economist",
    "Sustainability / ESG Finance Analyst",
    "Behavioral Economist",
]

# ─────────────────────────────────────────────
# 5. HELPER FUNCTIONS
# ─────────────────────────────────────────────

LEVELS = ["Beginner", "Intermediate", "Advanced"]

def year_from_id(student_id: str) -> int:
    """Infer study year from student ID suffix (simple heuristic)."""
    n = int(student_id[-4:])
    if n < 125:   return 1
    if n < 250:   return 2
    if n < 375:   return 3
    return 4

def skill_level_bias(year: int) -> list:
    """More advanced students lean toward higher proficiency."""
    if year == 1:
        return ["Beginner"] * 5 + ["Intermediate"]
    elif year == 2:
        return ["Beginner"] * 2 + ["Intermediate"] * 4
    elif year == 3:
        return ["Intermediate"] * 4 + ["Advanced"] * 2
    else:
        return ["Intermediate"] * 2 + ["Advanced"] * 4

def gen_skills(faculty: str, year: int) -> str:
    pool = CPE_ALL_SKILLS if faculty == "Computer Engineering" else ECON_ALL_SKILLS
    n    = random.randint(8, 14)
    selected = random.sample(pool, min(n, len(pool)))
    level_pool = skill_level_bias(year)
    return json.dumps([
        {"name": s, "level": random.choice(level_pool)}
        for s in selected
    ])

def gen_activities(faculty: str, year: int = 4) -> str:
    templates = CPE_ACTIVITY_TEMPLATES if faculty == "Computer Engineering" else ECON_ACTIVITY_TEMPLATES
    max_acts  = {1: 2, 2: 3, 3: 4, 4: 4}.get(year, 4)
    selected  = random.sample(templates, random.randint(2, max_acts))
    min_year  = {1: 2024, 2: 2023, 3: 2022, 4: 2022}.get(year, 2022)
    year_tag  = random.randint(min_year, 2025)
    return " | ".join([f"[{role}] at [{project} {year_tag}]" for role, project in selected])

# careers ที่ต้องการ English สูง (international-facing, global reports, cross-border)
CAREER_ENG_HIGH = {
    "Investment Banker", "Equity Research Analyst", "Portfolio Manager",
    "Quantitative Researcher", "AI Platform Engineer", "NLP Engineer",
    "ESG Analyst", "Economic Development Consultant",
    "Sustainability / ESG Finance Analyst", "Crypto / Digital Asset Analyst",
    "Blockchain / Web3 Developer", "Computer Vision Engineer",
    "Robotics Engineer", "AR/VR Developer",
}
# careers ที่ต้องการ English ปานกลาง
CAREER_ENG_MID = {
    "Software Engineer", "Data Scientist", "AI/ML Engineer", "Data Engineer",
    "DevOps / SRE Engineer", "Cloud Architect", "Cybersecurity Engineer",
    "Backend Engineer", "Full-Stack Developer", "MLOps Engineer",
    "Platform Engineer", "Security Engineer (AppSec)", "Site Reliability Engineer",
    "FinTech Software Engineer", "Financial Analyst", "Risk Manager",
    "Policy Analyst", "Economist", "Derivatives Trader", "Credit Analyst",
    "Data Analyst (Finance)", "Corporate Finance Analyst", "Actuarial Analyst",
    "Regulatory Economist", "FinTech Product Manager", "Wealth Manager",
    "Compliance Officer (RegTech)",
}
# careers ที่เหลือ = English Beginner ok

def gen_languages(career: str = None) -> str:
    # กำหนด English level pool ตาม career
    if career in CAREER_ENG_HIGH:
        eng_pool = ["Advanced", "Advanced", "Intermediate"]
    elif career in CAREER_ENG_MID:
        eng_pool = ["Intermediate", "Intermediate", "Advanced", "Beginner"]
    else:
        eng_pool = ["Beginner", "Intermediate", "Intermediate"]

    optional_pool = [
        ("Japanese", random.choice(["Beginner", "Intermediate"])),
        ("Chinese",  random.choice(["Beginner", "Intermediate"])),
        ("Korean",   "Beginner"),
        ("German",   "Beginner"),
        ("French",   "Beginner"),
    ]
    result = [
        {"name": "Thai",    "level": "Native"},
        {"name": "English", "level": random.choice(eng_pool)},
    ]
    if random.random() < 0.5:
        extra = random.choice(optional_pool)
        result.append({"name": extra[0], "level": extra[1]})
    return json.dumps(result)

# ─────────────────────────────────────────────
# 5b. CAREER → SKILLS MAPPING
#     Each career has: core skills (must-have, high weight) + adjacent skills (nice-to-have)
# ─────────────────────────────────────────────

CAREER_SKILL_MAP = {
    # ── CPE careers ──────────────────────────────────────────────────────────
    "Software Engineer": {
        "core": ["Python", "Java", "Go", "JavaScript", "TypeScript", "SQL",
                 "Git / Version Control", "Data Structures & Algorithms",
                 "Spring Boot", "Node.js", "PostgreSQL", "Docker",
                 "Agile / Scrum Methodology", "Software Engineering",
                 "REST API Design", "Unit Testing"],
        "adjacent": ["Kubernetes", "AWS (EC2, S3, Lambda)", "React",
                     "CI/CD Pipelines", "Technical Writing", "Problem Solving"],
    },
    "Data Scientist": {
        "core": ["Python", "Machine Learning", "Statistical Modeling",
                 "Scikit-learn", "Pandas / NumPy", "SQL", "Data Visualization",
                 "Feature Engineering", "A/B Testing", "Jupyter Notebook",
                 "TensorFlow", "PyTorch"],
        "adjacent": ["R", "Apache Spark", "Tableau", "Communication",
                     "Problem Solving", "dbt (Data Build Tool)", "Airflow"],
    },
    "AI/ML Engineer": {
        "core": ["Python", "Deep Learning", "TensorFlow", "PyTorch", "Keras",
                 "Machine Learning", "Model Deployment (MLOps)", "Hugging Face Transformers",
                 "Natural Language Processing", "Computer Vision",
                 "Feature Engineering", "Docker"],
        "adjacent": ["Kubernetes", "GCP (BigQuery, GKE)", "AWS (EC2, S3, Lambda)",
                     "LangChain", "Reinforcement Learning", "Problem Solving"],
    },
    "Data Engineer": {
        "core": ["Python", "SQL", "Apache Spark", "Apache Kafka", "Airflow",
                 "dbt (Data Build Tool)", "Hadoop", "AWS (EC2, S3, Lambda)",
                 "GCP (BigQuery, GKE)", "PostgreSQL", "Elasticsearch",
                 "Data Engineering", "Docker"],
        "adjacent": ["Kubernetes", "Scala", "Terraform", "CI/CD Pipelines",
                     "Technical Writing", "Problem Solving"],
    },
    "DevOps / SRE Engineer": {
        "core": ["Docker", "Kubernetes", "CI/CD Pipelines", "Terraform",
                 "Ansible", "Linux System Admin", "AWS (EC2, S3, Lambda)",
                 "GCP (BigQuery, GKE)", "Azure (AKS, Functions)",
                 "Prometheus & Grafana", "Nginx", "GitHub Actions", "Bash/Shell Scripting"],
        "adjacent": ["Python", "Go", "Network Security", "Technical Writing",
                     "Problem Solving", "Communication"],
    },
    "Cloud Architect": {
        "core": ["AWS (EC2, S3, Lambda)", "GCP (BigQuery, GKE)", "Azure (AKS, Functions)",
                 "Kubernetes", "Terraform", "Docker", "Microservices Architecture",
                 "CI/CD Pipelines", "Linux System Admin",
                 "Parallel and Distributed Computing Systems"],
        "adjacent": ["Python", "Go", "Network Security", "Technical Writing",
                     "Leadership", "Communication"],
    },
    "Cybersecurity Engineer": {
        "core": ["Penetration Testing", "Network Security", "Cryptography",
                 "OWASP Top 10", "Vulnerability Assessment", "SIEM Tools",
                 "TCP/IP Networking", "Linux System Admin", "Python",
                 "Computer System Security", "Bash/Shell Scripting"],
        "adjacent": ["Docker", "Cloud Security", "Incident Response",
                     "Technical Writing", "Problem Solving"],
    },
    "Backend Engineer": {
        "core": ["Python", "Java", "Go", "Node.js", "Spring Boot", "FastAPI",
                 "Django", "Flask", "SQL", "PostgreSQL", "Redis",
                 "REST API Design", "Docker", "Git / Version Control"],
        "adjacent": ["Kubernetes", "Apache Kafka", "Microservices Architecture",
                     "Technical Writing", "Problem Solving"],
    },
    "Full-Stack Developer": {
        "core": ["JavaScript", "TypeScript", "React", "Vue.js", "Node.js",
                 "Express.js", "Next.js", "Python", "SQL", "PostgreSQL",
                 "REST API Design", "Git / Version Control", "Docker",
                 "Figma (UI/UX)"],
        "adjacent": ["Agile / Scrum Methodology", "AWS (EC2, S3, Lambda)",
                     "CI/CD Pipelines", "Communication"],
    },
    "Embedded Systems Engineer": {
        "core": ["C/C++", "Embedded Systems (Arduino/Raspberry Pi)",
                 "Real-Time Operating Systems (RTOS)", "Microcontroller Programming",
                 "FPGA Programming", "TCP/IP Networking", "IoT Development",
                 "Assembly Language", "Embedded System (Course)", "Digital Systems Design"],
        "adjacent": ["Python", "Linux System Admin", "Wireless Networks",
                     "Problem Solving", "Technical Writing"],
    },
    "Computer Vision Engineer": {
        "core": ["Python", "Computer Vision", "Deep Learning", "OpenCV",
                 "PyTorch", "TensorFlow", "Convolutional Neural Networks",
                 "Digital Image Processing", "Feature Engineering",
                 "Model Deployment (MLOps)"],
        "adjacent": ["C/C++", "CUDA Programming", "Machine Learning",
                     "Scikit-learn", "Problem Solving"],
    },
    "NLP Engineer": {
        "core": ["Python", "Natural Language Processing", "Hugging Face Transformers",
                 "Deep Learning", "PyTorch", "TensorFlow", "LangChain",
                 "Machine Learning", "Text Mining", "Feature Engineering"],
        "adjacent": ["SQL", "Elasticsearch", "Model Deployment (MLOps)",
                     "Problem Solving", "Research Skills"],
    },
    "Quantitative Developer": {
        "core": ["Python", "C++", "Java", "Scala", "Statistical Modeling",
                 "Time Series Analysis", "SQL", "Machine Learning",
                 "Introduction to Computational Finance",
                 "Parallel and Distributed Computing Systems"],
        "adjacent": ["R", "MATLAB", "Monte Carlo Simulation",
                     "Financial Modeling", "Problem Solving"],
    },
    "Game Developer": {
        "core": ["C++", "C#", "Python", "Unity / Unreal Engine",
                 "Digital Game Production", "Computer Graphics",
                 "Object-Oriented Design", "Physics Engine Programming",
                 "Git / Version Control", "Agile / Scrum Methodology"],
        "adjacent": ["Java", "JavaScript", "3D Math", "Creativity & Innovation",
                     "Problem Solving"],
    },
    "Product Manager (Technical)": {
        "core": ["Agile / Scrum Methodology", "JIRA / Agile Tools",
                 "Product Roadmapping", "User Research", "Data Analytics",
                 "SQL", "A/B Testing", "Stakeholder Management",
                 "Communication", "Leadership"],
        "adjacent": ["Python", "Figma (UI/UX)", "Technical Writing",
                     "Financial Modeling", "Problem Solving"],
    },
    "Robotics Engineer": {
        "core": ["C++", "Python", "ROS (Robot Operating System)",
                 "Embedded Systems (Arduino/Raspberry Pi)", "Control Systems",
                 "Introduction to Robotics", "Mechatronic System and Control",
                 "Computer Vision", "Real-Time Operating Systems (RTOS)",
                 "Kinematics & Motion Planning"],
        "adjacent": ["MATLAB", "FPGA Programming", "Machine Learning",
                     "Problem Solving"],
    },

    # ── ECON careers ─────────────────────────────────────────────────────────
    "Quantitative Researcher": {
        "core": ["Econometrics", "Stochastic Modeling", "Monte Carlo Simulation",
                 "Python (Pandas, NumPy, Statsmodels)", "R (ggplot2, dplyr, tidyr)",
                 "MATLAB (Economic Modeling)", "Time Series Forecasting",
                 "Statistical Modeling", "Regression Analysis",
                 "Causal Inference (DiD, RDD, IV)", "Julia (Economic Modeling)",
                 "Quantitative Trading"],
        "adjacent": ["Bloomberg Terminal", "Factor Investing",
                     "SQL (Data Querying)", "Academic Paper Writing", "Research Skills"],
    },
    "Financial Analyst": {
        "core": ["Financial Modeling", "Valuation (DCF, Comps)",
                 "Financial Statement Analysis", "Excel (Advanced: Solver, VBA, Power Query)",
                 "Bloomberg Terminal", "Capital Budgeting",
                 "Equity Research", "Fixed Income Analysis",
                 "Economics of Money and Banking", "Corporate Finance"],
        "adjacent": ["Power BI", "Tableau", "Python (Pandas, NumPy, Statsmodels)",
                     "Communication", "Presentation Skills"],
    },
    "Investment Banker": {
        "core": ["Investment Banking (M&A Modeling)", "Valuation (DCF, Comps)",
                 "Financial Modeling", "Capital Budgeting",
                 "Financial Statement Analysis", "Excel (Advanced: Solver, VBA, Power Query)",
                 "Bloomberg Terminal", "Negotiation",
                 "Financial Economics", "Presentation Skills"],
        "adjacent": ["Credit Analysis", "Stakeholder Management",
                     "Leadership", "Communication", "Attention to Detail"],
    },
    "Risk Manager": {
        "core": ["Risk Management (VaR, CVaR)", "Stochastic Modeling",
                 "Econometrics", "Derivatives Pricing (Black-Scholes)",
                 "Fixed Income Analysis", "Bloomberg Terminal",
                 "Monte Carlo Simulation", "Regression Analysis",
                 "Economics of Financial Risk Management", "Credit Analysis"],
        "adjacent": ["Python (Pandas, NumPy, Statsmodels)", "R (ggplot2, dplyr, tidyr)",
                     "Analytical Thinking", "Attention to Detail"],
    },
    "Policy Analyst": {
        "core": ["Policy Brief Writing", "Cost-Benefit Analysis (CBA)",
                 "Development Economics", "Regression Analysis",
                 "Research Design", "Survey Design & Analysis",
                 "Stata", "National Accounts Analysis",
                 "Economic Thinking", "Research Methods in Economics"],
        "adjacent": ["R (ggplot2, dplyr, tidyr)", "Python (Pandas, NumPy, Statsmodels)",
                     "Communication", "Report Writing", "Stakeholder Management"],
    },
    "Data Analyst (Finance)": {
        "core": ["SQL (Data Querying)", "Python (Pandas, NumPy, Statsmodels)",
                 "Tableau", "Power BI", "Excel (Advanced: Solver, VBA, Power Query)",
                 "Statistical Modeling", "Data Visualization",
                 "Financial Statement Analysis", "Economics Statistics I/II",
                 "Regression Analysis"],
        "adjacent": ["R (ggplot2, dplyr, tidyr)", "Bloomberg Terminal",
                     "Communication", "Presentation Skills", "Problem Solving"],
    },
    "Portfolio Manager": {
        "core": ["Portfolio Management", "Equity Research", "Factor Investing",
                 "Valuation (DCF, Comps)", "Risk Management (VaR, CVaR)",
                 "Bloomberg Terminal", "Fixed Income Analysis",
                 "Financial Modeling", "Investment Analysis",
                 "Reuters Eikon"],
        "adjacent": ["Derivatives Pricing (Black-Scholes)", "Behavioral Finance",
                     "Leadership", "Communication", "Negotiation"],
    },
    "Equity Research Analyst": {
        "core": ["Equity Research", "Financial Modeling", "Valuation (DCF, Comps)",
                 "Financial Statement Analysis", "Bloomberg Terminal",
                 "Industry Analysis", "Excel (Advanced: Solver, VBA, Power Query)",
                 "Capital Budgeting", "Investment Analysis", "Report Writing"],
        "adjacent": ["Reuters Eikon", "Power BI", "Communication",
                     "Presentation Skills", "Attention to Detail"],
    },
    "Economist": {
        "core": ["Econometrics", "Macro Modeling (DSGE, CGE)", "Stata",
                 "R (ggplot2, dplyr, tidyr)", "Economic Forecasting",
                 "Regression Analysis", "Academic Paper Writing",
                 "Research Methods in Economics", "National Accounts Analysis",
                 "Causal Inference (DiD, RDD, IV)"],
        "adjacent": ["Python (Pandas, NumPy, Statsmodels)", "MATLAB (Economic Modeling)",
                     "Policy Brief Writing", "Communication", "Research Skills"],
    },
    "Derivatives Trader": {
        "core": ["Derivatives Pricing (Black-Scholes)", "Stochastic Modeling",
                 "Risk Management (VaR, CVaR)", "Bloomberg Terminal",
                 "Reuters Eikon", "Quantitative Trading",
                 "Monte Carlo Simulation", "Fixed Income Analysis",
                 "Economics of Financial Risk Management", "Behavioral Finance"],
        "adjacent": ["Python (Pandas, NumPy, Statsmodels)", "Excel (Advanced: Solver, VBA, Power Query)",
                     "Analytical Thinking", "Adaptability", "Attention to Detail"],
    },
    "Credit Analyst": {
        "core": ["Credit Analysis", "Financial Statement Analysis",
                 "Financial Modeling", "Excel (Advanced: Solver, VBA, Power Query)",
                 "Bloomberg Terminal", "Risk Management (VaR, CVaR)",
                 "Capital Budgeting", "Regression Analysis",
                 "Economics of Money and Banking", "Attention to Detail"],
        "adjacent": ["Valuation (DCF, Comps)", "Stata", "Communication",
                     "Report Writing", "Problem Solving"],
    },
    "ESG Analyst": {
        "core": ["Environmental Economics", "Social Impact Evaluation",
                 "Sustainability Reporting", "Policy Brief Writing",
                 "Cost-Benefit Analysis (CBA)", "Research Design",
                 "Data Visualization", "Stata",
                 "Economics of Natural Resources and Public Policy",
                 "Regression Analysis"],
        "adjacent": ["Bloomberg Terminal", "Survey Design & Analysis",
                     "Communication", "Report Writing", "Cross-cultural Communication"],
    },
    "Actuarial Analyst": {
        "core": ["Stochastic Modeling", "Monte Carlo Simulation",
                 "Probability & Statistics", "Risk Management (VaR, CVaR)",
                 "Excel (Advanced: Solver, VBA, Power Query)",
                 "Regression Analysis", "Time Series Forecasting",
                 "R (ggplot2, dplyr, tidyr)", "MATLAB (Economic Modeling)",
                 "Mathematical Economics"],
        "adjacent": ["Python (Pandas, NumPy, Statsmodels)", "Fixed Income Analysis",
                     "Attention to Detail", "Analytical Thinking"],
    },
    "Corporate Finance Analyst": {
        "core": ["Financial Modeling", "Capital Budgeting",
                 "Valuation (DCF, Comps)", "Financial Statement Analysis",
                 "Excel (Advanced: Solver, VBA, Power Query)",
                 "Cost-Benefit Analysis (CBA)", "Bloomberg Terminal",
                 "Investment Analysis", "Negotiation", "Presentation Skills"],
        "adjacent": ["Power BI", "Tableau", "Communication",
                     "Leadership", "Project Management"],
    },
    "Economic Development Consultant": {
        "core": ["Development Economics", "Cost-Benefit Analysis (CBA)",
                 "Policy Brief Writing", "Survey Design & Analysis",
                 "Poverty Analysis", "Stata", "Research Methods in Economics",
                 "Causal Inference (DiD, RDD, IV)", "National Accounts Analysis",
                 "Economic Development and International Trade"],
        "adjacent": ["R (ggplot2, dplyr, tidyr)", "Project Management",
                     "Communication", "Report Writing", "Stakeholder Management"],
    },
    "Regulatory Economist": {
        "core": ["Regulatory Economics", "Industrial Organization Analysis",
                 "Cost-Benefit Analysis (CBA)", "Game Theory",
                 "Econometrics", "Policy Brief Writing",
                 "Stata", "Research Design",
                 "Economics of Industrial Organization", "Report Writing"],
        "adjacent": ["R (ggplot2, dplyr, tidyr)", "Academic Paper Writing",
                     "Communication", "Analytical Thinking", "Stakeholder Management"],
    },
}

# ── NEW TRENDING CAREERS: Skill Maps ─────────────────────────────────────────
CAREER_SKILL_MAP.update({

    # ── CPE New ──────────────────────────────────────────────────────────────
    "MLOps Engineer": {
        "core": ["Model Deployment (MLOps)", "Docker", "Kubernetes", "Airflow",
                 "Python", "MLflow / Weights & Biases", "CI/CD Pipelines",
                 "AWS (EC2, S3, Lambda)", "GCP (BigQuery, GKE)",
                 "Feature Engineering", "dbt (Data Build Tool)", "Prometheus & Grafana"],
        "adjacent": ["TensorFlow", "PyTorch", "Linux System Admin",
                     "Technical Writing", "Problem Solving"],
    },
    "AI Platform Engineer": {
        "core": ["Python", "LangChain", "LLM Fine-tuning", "Vector Databases (Pinecone/Weaviate)",
                 "Hugging Face Transformers", "Model Deployment (MLOps)",
                 "Docker", "Kubernetes", "AWS (EC2, S3, Lambda)",
                 "RAG (Retrieval-Augmented Generation)", "Prompt Engineering",
                 "CI/CD Pipelines"],
        "adjacent": ["PyTorch", "Redis", "Technical Writing",
                     "Communication", "Problem Solving"],
    },
    "Platform Engineer": {
        "core": ["Kubernetes", "Terraform", "CI/CD Pipelines", "Docker",
                 "GitHub Actions", "Internal Developer Platforms (IDP)",
                 "AWS (EC2, S3, Lambda)", "GCP (BigQuery, GKE)",
                 "Linux System Admin", "Bash/Shell Scripting",
                 "Prometheus & Grafana", "Service Mesh (Istio)"],
        "adjacent": ["Go", "Python", "Ansible",
                     "Technical Writing", "Communication"],
    },
    "Security Engineer (AppSec)": {
        "core": ["OWASP Top 10", "SAST / DAST Tools", "Penetration Testing",
                 "Python", "Cryptography", "Vulnerability Assessment",
                 "Secure Code Review", "Network Security",
                 "Burp Suite", "SIEM Tools", "Bash/Shell Scripting",
                 "Cloud Security (AWS / GCP)"],
        "adjacent": ["Docker", "Linux System Admin", "Incident Response",
                     "Technical Writing", "Problem Solving"],
    },
    "Blockchain / Web3 Developer": {
        "core": ["Solidity", "Ethereum / EVM", "Web3.js / Ethers.js",
                 "Smart Contract Development", "Hardhat / Foundry",
                 "Python", "JavaScript / TypeScript",
                 "DeFi Protocols", "IPFS / Decentralized Storage",
                 "Cryptography", "Git / Version Control"],
        "adjacent": ["Rust", "Zero-Knowledge Proofs (ZKP)",
                     "Node.js", "Agile / Scrum Methodology", "Problem Solving"],
    },
    "AR/VR Developer": {
        "core": ["Unity 3D", "Unreal Engine", "C#", "C++",
                 "WebXR / WebGL", "3D Modeling (Blender)",
                 "Spatial Computing (Meta Quest / Apple Vision Pro)",
                 "Shader Programming", "Computer Graphics",
                 "Digital Image Processing", "Git / Version Control"],
        "adjacent": ["Python", "OpenCV", "Machine Learning",
                     "Creativity & Innovation", "Problem Solving"],
    },
    "Site Reliability Engineer": {
        "core": ["SLO / SLA / SLI Design", "Prometheus & Grafana", "Kubernetes",
                 "Docker", "Linux System Admin", "Python", "Go",
                 "Bash/Shell Scripting", "Chaos Engineering (Chaos Monkey)",
                 "Incident Management", "AWS (EC2, S3, Lambda)",
                 "CI/CD Pipelines"],
        "adjacent": ["Terraform", "Elasticsearch", "Nginx",
                     "Technical Writing", "Communication"],
    },
    "FinTech Software Engineer": {
        "core": ["Java", "Python", "Spring Boot", "RESTful APIs",
                 "SQL", "PostgreSQL", "Docker", "Kubernetes",
                 "Payment Systems (ISO 20022, SWIFT)", "PCI-DSS Compliance",
                 "Microservices Architecture", "AWS (EC2, S3, Lambda)"],
        "adjacent": ["Kafka", "Redis", "Cryptography",
                     "Agile / Scrum Methodology", "Technical Writing"],
    },

    # ── ECON New ─────────────────────────────────────────────────────────────
    "FinTech Product Manager": {
        "core": ["Product Roadmapping", "Agile / Scrum Methodology",
                 "User Research", "Data Analytics",
                 "Payment Systems Knowledge", "Open Banking / API Finance",
                 "SQL (Data Querying)", "A/B Testing",
                 "Financial Modeling", "Stakeholder Management",
                 "Communication", "Presentation Skills"],
        "adjacent": ["Python (Pandas, NumPy, Statsmodels)", "Tableau",
                     "Behavioral Economics", "Leadership", "Negotiation"],
    },
    "Crypto / Digital Asset Analyst": {
        "core": ["On-Chain Data Analysis (Dune Analytics, Glassnode)",
                 "DeFi Protocol Analysis", "Tokenomics Modeling",
                 "Python (Pandas, NumPy, Statsmodels)",
                 "Derivatives Pricing (Black-Scholes)",
                 "Risk Management (VaR, CVaR)",
                 "Bloomberg Terminal", "Quantitative Trading",
                 "Time Series Forecasting", "Behavioral Finance"],
        "adjacent": ["SQL (Data Querying)", "R (ggplot2, dplyr, tidyr)",
                     "Stochastic Modeling", "Research Skills", "Adaptability"],
    },
    "Wealth Manager": {
        "core": ["Portfolio Management", "Financial Planning",
                 "Valuation (DCF, Comps)", "Tax Planning",
                 "Excel (Advanced: Solver, VBA, Power Query)",
                 "Bloomberg Terminal", "Fixed Income Analysis",
                 "Estate Planning", "Risk Management (VaR, CVaR)",
                 "Client Relationship Management",
                 "Investment Analysis", "Communication"],
        "adjacent": ["Behavioral Finance", "Reuters Eikon",
                     "Negotiation", "Presentation Skills", "Attention to Detail"],
    },
    "FP&A Analyst": {
        "core": ["Financial Modeling", "Budgeting & Forecasting",
                 "Excel (Advanced: Solver, VBA, Power Query)",
                 "Power BI", "Tableau",
                 "Financial Statement Analysis", "SQL (Data Querying)",
                 "Variance Analysis", "Capital Budgeting",
                 "Stakeholder Management", "Report Writing"],
        "adjacent": ["Python (Pandas, NumPy, Statsmodels)", "SAP / Oracle ERP",
                     "Communication", "Presentation Skills", "Attention to Detail"],
    },
    "Compliance Officer (RegTech)": {
        "core": ["AML / KYC Compliance", "Regulatory Frameworks (Basel III, MiFID II)",
                 "Risk Management (VaR, CVaR)", "Policy Brief Writing",
                 "RegTech Tools (ComplyAdvantage)", "SQL (Data Querying)",
                 "Data Analytics", "Report Writing",
                 "Financial Statement Analysis", "Attention to Detail"],
        "adjacent": ["Python (Pandas, NumPy, Statsmodels)", "Excel (Advanced: Solver, VBA, Power Query)",
                     "Stakeholder Management", "Communication", "Research Skills"],
    },
    "Supply Chain Economist": {
        "core": ["Supply Chain Modeling", "Input-Output Analysis",
                 "Operations Research for Economic Applications",
                 "Cost-Benefit Analysis (CBA)", "Regression Analysis",
                 "Python (Pandas, NumPy, Statsmodels)", "Stata",
                 "Econometrics", "Excel (Advanced: Solver, VBA, Power Query)",
                 "Survey Design & Analysis", "Data Visualization"],
        "adjacent": ["Power BI", "Tableau", "R (ggplot2, dplyr, tidyr)",
                     "Report Writing", "Communication"],
    },
    "Sustainability / ESG Finance Analyst": {
        "core": ["ESG Reporting Frameworks (GRI, TCFD, ISSB)",
                 "Green Bond / Sustainable Finance Analysis",
                 "Environmental Economics",
                 "Cost-Benefit Analysis (CBA)", "Social Impact Evaluation",
                 "Bloomberg Terminal", "Data Visualization",
                 "Regression Analysis", "Stata",
                 "Economics of Natural Resources and Public Policy",
                 "Report Writing"],
        "adjacent": ["Python (Pandas, NumPy, Statsmodels)", "Survey Design & Analysis",
                     "Stakeholder Management", "Communication", "Research Skills"],
    },
    "Behavioral Economist": {
        "core": ["Behavioural Economics", "Experimental Economics",
                 "Survey Design & Analysis", "Causal Inference (DiD, RDD, IV)",
                 "Regression Analysis", "R (ggplot2, dplyr, tidyr)",
                 "Stata", "Academic Paper Writing",
                 "Research Methods in Economics", "Nudge Theory",
                 "Hypothesis Testing"],
        "adjacent": ["Python (Pandas, NumPy, Statsmodels)", "Data Visualization",
                     "Policy Brief Writing", "Communication", "Research Skills"],
    },
})

# Career → most relevant activities (index into the activity template lists)
CPE_CAREER_ACTIVITY_MAP = {
    # Existing
    "Software Engineer":            [1, 2, 9, 13, 14, 17],
    "Data Scientist":               [2, 9, 13, 16, 7],
    "AI/ML Engineer":               [2, 8, 9, 13, 16],
    "Data Engineer":                [2, 7, 9, 13, 16],
    "DevOps / SRE Engineer":        [9, 10, 13, 16, 4],
    "Cloud Architect":              [9, 10, 13, 16, 4],
    "Cybersecurity Engineer":       [5, 13, 4, 16, 3],
    "Backend Engineer":             [1, 9, 13, 16, 4],
    "Full-Stack Developer":         [0, 1, 4, 13, 17],
    "Embedded Systems Engineer":    [11, 13, 16, 3, 15],
    "Computer Vision Engineer":     [12, 2, 8, 13, 16],
    "NLP Engineer":                 [12, 2, 8, 13, 16],
    "Quantitative Developer":       [2, 7, 9, 13, 16],
    "Game Developer":               [19, 13, 16, 17, 4],
    "Product Manager (Technical)":  [0, 15, 13, 4, 17],
    "Robotics Engineer":            [11, 12, 13, 16, 3],
    # New trending (indices 20-27 = new templates added above)
    "MLOps Engineer":               [20, 2, 8, 13, 16],
    "AI Platform Engineer":         [21, 2, 8, 16, 13],
    "Platform Engineer":            [24, 9, 10, 13, 16],
    "Security Engineer (AppSec)":   [25, 5, 13, 4, 16],
    "Blockchain / Web3 Developer":  [22, 18, 13, 16, 4],
    "AR/VR Developer":              [23, 19, 13, 16, 12],
    "Site Reliability Engineer":    [27, 9, 10, 13, 16],
    "FinTech Software Engineer":    [26, 1, 9, 13, 16],
}

ECON_CAREER_ACTIVITY_MAP = {
    # Existing
    "Quantitative Researcher":      [3, 7, 18, 1, 9],
    "Financial Analyst":            [1, 3, 4, 6, 9],
    "Investment Banker":            [6, 3, 4, 9, 19],
    "Risk Manager":                 [1, 11, 6, 3, 9],
    "Policy Analyst":               [0, 9, 8, 7, 18],
    "Data Analyst (Finance)":       [8, 3, 1, 9, 7],
    "Portfolio Manager":            [4, 1, 6, 3, 19],
    "Equity Research Analyst":      [1, 6, 3, 4, 9],
    "Economist":                    [0, 7, 18, 8, 9],
    "Derivatives Trader":           [13, 1, 6, 4, 3],
    "Credit Analyst":               [10, 1, 6, 3, 9],
    "ESG Analyst":                  [14, 7, 9, 18, 8],
    "Actuarial Analyst":            [3, 7, 1, 6, 18],
    "Corporate Finance Analyst":    [5, 6, 1, 4, 9],
    "Economic Development Consultant": [9, 7, 0, 18, 8],
    "Regulatory Economist":         [0, 9, 7, 18, 16],
    # New trending (indices 20-27 = new templates added above)
    "FinTech Product Manager":      [19, 20, 8, 9, 1],
    "Crypto / Digital Asset Analyst": [20, 21, 13, 3, 1],
    "Wealth Manager":               [22, 4, 1, 6, 9],
    "FP&A Analyst":                 [23, 5, 1, 8, 9],
    "Compliance Officer (RegTech)": [24, 9, 0, 7, 16],
    "Supply Chain Economist":       [25, 9, 0, 8, 7],
    "Sustainability / ESG Finance Analyst": [26, 14, 9, 7, 0],
    "Behavioral Economist":         [27, 18, 7, 0, 9],
}

def _language_skills(career: str) -> list:
    """Return language skill entries to append into skills lists, based on career group."""
    # Thai = Native เสมอ
    # English level ตาม career group
    if career in CAREER_ENG_HIGH:
        eng_pool = ["Advanced", "Advanced", "Intermediate"]
    elif career in CAREER_ENG_MID:
        eng_pool = ["Intermediate", "Intermediate", "Advanced", "Beginner"]
    else:
        eng_pool = ["Beginner", "Intermediate", "Intermediate"]

    langs = [
        {"name": "Thai",    "level": "Native"},
        {"name": "English", "level": random.choice(eng_pool)},
    ]
    # ~50% chance ภาษาที่ 3
    optional_pool = [
        ("Japanese", random.choice(["Beginner", "Intermediate"])),
        ("Chinese",  random.choice(["Beginner", "Intermediate"])),
        ("Korean",   "Beginner"),
        ("German",   "Beginner"),
        ("French",   "Beginner"),
    ]
    if random.random() < 0.5:
        extra = random.choice(optional_pool)
        langs.append({"name": extra[0], "level": extra[1]})
    return langs


def gen_career_skills(career: str, year: int = 4, entry_level: bool = False) -> str:
    """Generate skills biased toward a specific career's core skill set,
    with language skills appended at the end."""
    mapping = CAREER_SKILL_MAP.get(career)
    if mapping is None:
        fac = "Computer Engineering" if career in CPE_CAREERS else "Economics"
        return gen_skills(fac, year)

    core     = mapping["core"]
    adjacent = mapping["adjacent"]
    level_pool = skill_level_bias(year)

    n_core = min(random.randint(5, 9), len(core))
    n_adj  = min(random.randint(2, 5), len(adjacent))

    selected_core = random.sample(core, n_core)
    selected_adj  = random.sample(adjacent, n_adj)

    core_level_pool = (
        ["Intermediate"] * 4 + ["Advanced"] + ["Beginner"] * 2
        if entry_level else
        ["Intermediate"] * 3 + ["Advanced"] * 3 + ["Beginner"]
    )
    adj_level_pool = (
        ["Beginner"] * 3 + ["Intermediate"] * 3 + ["Advanced"]
        if entry_level else
        level_pool
    )

    result = []
    for s in selected_core:
        lvl = random.choice(core_level_pool)
        result.append({"name": s, "level": lvl})
    for s in selected_adj:
        lvl = random.choice(adj_level_pool)
        result.append({"name": s, "level": lvl})

    # เพิ่ม language skills ท้าย (Alumni + Market)
    result += _language_skills(career)

    return json.dumps(result)

def gen_career_activities(career: str, faculty: str, year: int = 4) -> str:
    """Generate activities relevant to the specific career path."""
    if faculty == "Computer Engineering":
        templates   = CPE_ACTIVITY_TEMPLATES
        career_map  = CPE_CAREER_ACTIVITY_MAP
    else:
        templates   = ECON_ACTIVITY_TEMPLATES
        career_map  = ECON_CAREER_ACTIVITY_MAP

    preferred_indices = career_map.get(career, list(range(len(templates))))
    valid_idx = [i for i in preferred_indices if i < len(templates)]

    # ปีที่ 1 สามารถมีกิจกรรมได้สูงสุด 2 รายการ (เพิ่งเข้ามหาวิทยาลัย)
    max_acts = {1: 2, 2: 3, 3: 4, 4: 4}.get(year, 4)
    n = min(random.randint(2, max_acts), len(valid_idx))

    # Lock first index (most career-specific), randomly pick the rest
    must = valid_idx[:1]
    optional = valid_idx[1:]
    extra = random.sample(optional, min(n - len(must), len(optional)))
    chosen_idx = must + extra

    # ปีที่ 1 มีกิจกรรมได้ตั้งแต่ปีที่เข้ามหาวิทยาลัยเท่านั้น ไม่ใช่ตอนมัธยม
    min_year = {1: 2024, 2: 2023, 3: 2022, 4: 2022}.get(year, 2022)
    year_tag = random.randint(min_year, 2025)

    return " | ".join(
        [f"[{templates[i][0]}] at [{templates[i][1]} {year_tag}]" for i in chosen_idx]
    )


def gen_course_grades(faculty: str, year: int) -> str:
    """Generate 10-15 courses with grades appropriate to year and GPA tendency."""
    if faculty == "Computer Engineering":
        core_pool = CPE_CORE_COURSES
        elec_pool = CPE_ELECTIVE_COURSES
    else:
        core_pool = ECON_CORE_COURSES
        elec_pool = ECON_ELECTIVE_COURSES

    # Pick core courses based on year progression
    core_per_year = max(1, len(core_pool) // 4)
    core_slice    = core_pool[:core_per_year * year]
    n_core = min(random.randint(6, 10), len(core_slice))
    selected_core = random.sample(core_slice, n_core)

    # ปีที่ 1-2 ยังเรียน core วิชาพื้นฐาน ไม่มีวิชาเลือกสาขา
    # ปีที่ 3 เริ่มเลือก 1-3 วิชา, ปีที่ 4 เลือก 2-5 วิชา
    if year <= 2:
        n_elec = 0
    elif year == 3:
        n_elec = random.randint(1, 3)
    else:
        n_elec = random.randint(2, 5)
    selected_elec = random.sample(elec_pool, min(n_elec, len(elec_pool)))

    all_selected = selected_core + selected_elec
    # Simulate grade distribution: later years tend to be more stable
    grade_pool = (["A"] * 3 + ["B+"] * 3 + ["B"] * 3 + ["C+"] * 2 + ["C"] * 1
                  if year >= 3 else
                  ["A"] * 2 + ["B+"] * 3 + ["B"] * 3 + ["C+"] * 2 + ["C"] * 2 + ["D+"] * 1)

    return json.dumps([
        {"course_id": cid, "course_name": cname, "grade": random.choice(grade_pool)}
        for cid, cname in all_selected
    ])


# ─────────────────────────────────────────────
# 5c. CAREER SALARY RANGES  (THB/month, realistic Thai market 2025)
# ─────────────────────────────────────────────
CAREER_SALARY_RANGE = {
    # CPE — Technology  (เงินเดือนงานแรก fresh graduate ตลาดไทย 2025)
    "Software Engineer":            (30_000,  70_000),
    "Backend Engineer":             (30_000,  70_000),
    "Full-Stack Developer":         (28_000,  65_000),
    "Data Engineer":                (35_000,  80_000),
    "Data Scientist":               (38_000,  85_000),
    "AI/ML Engineer":               (42_000,  95_000),
    "NLP Engineer":                 (42_000,  95_000),
    "Computer Vision Engineer":     (42_000,  95_000),
    "MLOps Engineer":               (40_000,  90_000),
    "AI Platform Engineer":         (45_000, 100_000),
    "DevOps / SRE Engineer":        (35_000,  80_000),
    "Site Reliability Engineer":    (38_000,  85_000),
    "Cloud Architect":              (40_000,  90_000),
    "Platform Engineer":            (38_000,  82_000),
    "Cybersecurity Engineer":       (38_000,  85_000),
    "Security Engineer (AppSec)":   (38_000,  85_000),
    "Embedded Systems Engineer":    (28_000,  65_000),
    "Robotics Engineer":            (32_000,  72_000),
    "Quantitative Developer":       (45_000, 105_000),
    "FinTech Software Engineer":    (38_000,  85_000),
    "Blockchain / Web3 Developer":  (40_000,  92_000),
    "AR/VR Developer":              (32_000,  75_000),
    "Game Developer":               (25_000,  62_000),
    "Product Manager (Technical)":  (40_000,  90_000),
    # ECON — Finance / Policy  (เงินเดือนงานแรก fresh graduate ตลาดไทย 2025)
    "Investment Banker":            (45_000, 100_000),
    "Derivatives Trader":           (42_000,  95_000),
    "Portfolio Manager":            (38_000,  88_000),
    "Quantitative Researcher":      (48_000, 110_000),
    "Equity Research Analyst":      (35_000,  80_000),
    "Financial Analyst":            (28_000,  68_000),
    "Risk Manager":                 (35_000,  82_000),
    "Credit Analyst":               (28_000,  65_000),
    "Actuarial Analyst":            (38_000,  88_000),
    "Data Analyst (Finance)":       (28_000,  68_000),
    "Corporate Finance Analyst":    (32_000,  75_000),
    "Wealth Manager":               (38_000,  88_000),
    "FP&A Analyst":                 (28_000,  65_000),
    "ESG Analyst":                  (28_000,  65_000),
    "Sustainability / ESG Finance Analyst": (28_000, 65_000),
    "Compliance Officer (RegTech)": (32_000,  78_000),
    "FinTech Product Manager":      (38_000,  88_000),
    "Crypto / Digital Asset Analyst": (35_000, 88_000),
    "Economist":                    (30_000,  72_000),
    "Policy Analyst":               (28_000,  62_000),
    "Regulatory Economist":         (30_000,  70_000),
    "Economic Development Consultant": (30_000, 70_000),
    "Supply Chain Economist":       (28_000,  65_000),
    "Behavioral Economist":         (28_000,  65_000),
}

def career_salary(career: str, success_score: int) -> int:
    """Salary correlated with career range and success score (higher score → higher salary)."""
    lo, hi = CAREER_SALARY_RANGE.get(career, (30_000, 80_000))
    # success_score 65-99 maps linearly onto [lo, hi] with ±10% noise
    ratio  = (success_score - 65) / (99 - 65)          # 0.0 – 1.0
    base   = lo + ratio * (hi - lo)
    noise  = random.gauss(0, (hi - lo) * 0.08)
    return int(max(lo, min(hi, base + noise)))


# careers ที่ต้องการ GPA สูง (competitive entry)
CAREER_GPA_HIGH = {
    "Investment Banker", "Quantitative Researcher", "Derivatives Trader",
    "AI Platform Engineer", "Portfolio Manager", "Equity Research Analyst",
    "Actuarial Analyst", "Blockchain / Web3 Developer", "Computer Vision Engineer",
    "NLP Engineer", "Quantitative Developer", "Robotics Engineer",
}
CAREER_GPA_MID = {
    "Data Scientist", "AI/ML Engineer", "MLOps Engineer", "Risk Manager",
    "Cloud Architect", "Cybersecurity Engineer", "Platform Engineer",
    "Security Engineer (AppSec)", "Site Reliability Engineer",
    "Financial Analyst", "Corporate Finance Analyst", "Wealth Manager",
    "Compliance Officer (RegTech)", "FinTech Product Manager",
    "Crypto / Digital Asset Analyst", "FinTech Software Engineer",
}
# remaining careers = GPA ทั่วไป

def career_gpa(career: str) -> float:
    """GPA biased by career prestige with realistic distribution."""
    if career in CAREER_GPA_HIGH:
        gpa = random.gauss(3.4, 0.3)
    elif career in CAREER_GPA_MID:
        gpa = random.gauss(3.1, 0.35)
    else:
        gpa = random.gauss(2.9, 0.4)
    return round(max(2.0, min(4.0, gpa)), 2)

def gpa_skill_level_bias(year: int, gpa: float) -> list:
    """Skill level pool biased by both year and GPA."""
    # base from year
    if year <= 2:
        base_adv, base_int, base_beg = 0, 4, 6
    elif year == 3:
        base_adv, base_int, base_beg = 2, 5, 3
    else:
        base_adv, base_int, base_beg = 4, 4, 2
    # GPA bonus: every 0.5 above 3.0 adds +1 Advanced, -1 Beginner
    gpa_bonus = int((gpa - 3.0) / 0.5)
    adv = max(0, base_adv + gpa_bonus)
    beg = max(0, base_beg - gpa_bonus)
    return ["Advanced"] * adv + ["Intermediate"] * base_int + ["Beginner"] * beg or ["Intermediate"]

def gen_student_skills(career: str, faculty: str, year: int, gpa: float) -> str:
    """60% career-specific core skills + 40% faculty-wide — with GPA-biased levels."""
    mapping = CAREER_SKILL_MAP.get(career)
    level_pool = gpa_skill_level_bias(year, gpa)

    if mapping is None:
        pool = CPE_ALL_SKILLS if faculty == "Computer Engineering" else ECON_ALL_SKILLS
        selected = random.sample(pool, min(random.randint(8, 13), len(pool)))
        return json.dumps([{"name": s, "level": random.choice(level_pool)} for s in selected])

    core     = mapping["core"]
    adjacent = mapping["adjacent"]
    fac_pool = CPE_ALL_SKILLS if faculty == "Computer Engineering" else ECON_ALL_SKILLS

    # Year 1-2: เริ่มสะสม career skills; Year 3-4: เชี่ยวชาญ career จริงจัง
    if year <= 2:
        career_ratio = 0.75
    elif year == 3:
        career_ratio = 0.85
    else:
        career_ratio = 0.90

    total = random.randint(8, 13)
    n_career = max(2, int(total * career_ratio))
    n_fac    = total - n_career

    career_pool = core + adjacent
    selected_career = random.sample(career_pool, min(n_career, len(career_pool)))
    # faculty pool minus already selected
    remaining_fac = [s for s in fac_pool if s not in selected_career]
    selected_fac  = random.sample(remaining_fac, min(n_fac, len(remaining_fac)))

    # ปีที่ 1: cap ทุก skill ไว้ที่ Intermediate (ยังไม่มีเวลาเชี่ยวชาญจริงๆ)
    if year == 1:
        level_pool = [l if l != "Advanced" else "Intermediate" for l in level_pool]

    result = []
    for s in selected_career:
        # core skills ได้ level สูงกว่า adjacent เล็กน้อย แต่ยังถูก cap ด้วย year
        if s in core:
            # core skills: Beginner → Intermediate เท่านั้น (ไม่กระโดดข้าม Intermediate → Advanced)
            bumped = [{"Beginner": "Intermediate"}.get(l, l) for l in level_pool]
            lvl_pool = bumped
        else:
            lvl_pool = level_pool
        result.append({"name": s, "level": random.choice(lvl_pool)})
    for s in selected_fac:
        result.append({"name": s, "level": random.choice(level_pool)})

    return json.dumps(result)

# ─────────────────────────────────────────────
# 6. DATASET GENERATION
# ─────────────────────────────────────────────

N_ROWS   = 500
FACULTIES = ["Computer Engineering", "Economics"]

# --- 6.1  Student Profiles (stratified: equal per career) ---
# Fix 5: Career balance — สุ่มแบบ stratified ให้แต่ละ career ใกล้เคียงกัน
ALL_CAREERS = CPE_CAREERS + ECON_CAREERS
CPE_SET = set(CPE_CAREERS)
N_PER_CAREER = max(1, N_ROWS // len(ALL_CAREERS))
career_pool_expanded = (ALL_CAREERS * (N_PER_CAREER + 1))[:N_ROWS]
random.shuffle(career_pool_expanded)

students = []
for i in range(N_ROWS):
    target  = career_pool_expanded[i]
    fac     = "Computer Engineering" if target in CPE_SET else "Economics"
    sid     = f"661040{i:04d}"
    yr      = year_from_id(sid)
    gpa     = career_gpa(target)              # Fix 4: GPA biased by career prestige

    students.append({
        "student_id":        sid,
        "name":              f"Student_{i:04d}",
        "faculty":           fac,
        "year":              yr,
        "gpa":               gpa,
        "skills":            gen_student_skills(target, fac, yr, gpa),
        "languages":         gen_languages(target),
        "activities":        gen_career_activities(target, fac, yr),
        "key_course_grades": gen_course_grades(fac, yr),
        "target_career":     target,
    })

df_students = pd.DataFrame(students)

# --- 6.2  Alumni Career Data (career-aware, correlated salary/score) ---
# stratified: same career balance as student dataset
alumni_career_pool = (ALL_CAREERS * (N_PER_CAREER + 1))[:N_ROWS]
random.shuffle(alumni_career_pool)

alumni = []
for i in range(N_ROWS):
    career = alumni_career_pool[i]
    fac    = "Computer Engineering" if career in CPE_SET else "Economics"
    yr     = 4
    # Fix 2: success_score first, then derive correlated outcomes
    success_score      = int(np.clip(np.random.normal(80, 8), 60, 99))
    # Fix 3: salary from per-career range, correlated with success
    salary             = career_salary(career, success_score)
    # Fix 2: years_to_promotion negatively correlated with success (high score → promote fast)
    promo_base         = 5 - int((success_score - 60) / (99 - 60) * 4)  # 5→1
    years_to_promotion = int(np.clip(promo_base + random.randint(-1, 1), 1, 5))
    # GPA at graduation also correlated with career prestige
    gpa_grad           = career_gpa(career)

    alumni.append({
        "alumni_id":             f"ALUM_{i:04d}",
        "faculty":               fac,
        "first_job_title":       career,
        "gpa_at_graduation":     gpa_grad,
        "skills_at_graduation":  gen_career_skills(career, yr),
        "activities_in_college": gen_career_activities(career, fac),
        "key_course_grades":     gen_course_grades(fac, yr),
        "salary_start":          salary,
        "years_to_promotion":    years_to_promotion,
        "success_score":         success_score,
    })

df_alumni = pd.DataFrame(alumni)

# --- 6.3  Labor Market (career-aware, realistic salary range) ---
ALL_JOBS = list(set(CPE_CAREERS + ECON_CAREERS))
market   = []
for job in ALL_JOBS:
    fac_hint = "Computer Engineering" if job in CPE_CAREERS else "Economics"
    lo, hi   = CAREER_SALARY_RANGE.get(job, (30_000, 100_000))
    for _ in range(10):
        # min_salary around lower 40% of range, max around upper 60%-100%
        min_sal = int(lo + random.uniform(0, 0.4) * (hi - lo))
        max_sal = int(lo + random.uniform(0.6, 1.0) * (hi - lo))
        market.append({
            "job_id":           f"JOB_{len(market):04d}",
            "job_title":        job,
            "industry":         "Technology" if fac_hint == "Computer Engineering" else "Finance / Policy",
            "required_skills":      gen_career_skills(job, year=4, entry_level=True),
            "min_salary":           min(min_sal, max_sal - 5_000),
            "max_salary":           max_sal,
            "growth_rate":          f"{random.randint(5, 30)}%",
            "experience_required":  "0-1 years (Fresh Graduate)",
        })

df_market = pd.DataFrame(market).iloc[:500]

# ─────────────────────────────────────────────
# 7. SAVE TO CSV
# ─────────────────────────────────────────────

out_students = os.getenv("DATA_PATH_STUDENTS", "data/synthetic_student_dataset_500_clean.csv")
out_alumni   = os.getenv("DATA_PATH_ALUMNI",   "data/alumni_dataset_500.csv")
out_market   = os.getenv("DATA_PATH_LABOR",    "data/labor_market_dataset_with_salary.csv")

df_students.to_csv(out_students, index=False, encoding="utf-8-sig")
df_alumni.to_csv(  out_alumni,   index=False, encoding="utf-8-sig")
df_market.to_csv(  out_market,   index=False, encoding="utf-8-sig")

print("Generated 3 datasets successfully!")
print(f"    Students  : {len(df_students)} rows  | columns: {list(df_students.columns)}")
print(f"    Alumni    : {len(df_alumni)} rows  | columns: {list(df_alumni.columns)}")
print(f"    Market    : {len(df_market)} rows  | columns: {list(df_market.columns)}")

# --- Quick sanity checks ---
sample = df_students.sample(1).iloc[0]
print(f"\n📋  Sample student: {sample['student_id']} | {sample['faculty']} | Year {sample['year']} | GPA {sample['gpa']}")
courses = json.loads(sample["key_course_grades"])
print(f"    Courses enrolled : {len(courses)} (e.g. {courses[0]['course_name']} → {courses[0]['grade']})")
skills  = json.loads(sample["skills"])
print(f"    Skills           : {len(skills)} (e.g. {skills[0]['name']} [{skills[0]['level']}])")
print(f"    Target career    : {sample['target_career']}")
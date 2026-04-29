import csv
import json
import random

def update_row(row, category, idx):
    if category == 'NEEDS':
        # Bronze: OVR < 65
        gpa = round(random.uniform(2.0, 2.5), 2)
        base_skills = [
            [{"name": "Microsoft Word", "level": "Beginner"}],
            [{"name": "Excel", "level": "Beginner"}],
            [{"name": "HTML", "level": "Beginner"}],
            [{"name": "PowerPoint", "level": "Beginner"}],
            [{"name": "Python", "level": "Beginner"}],
        ]
        row['gpa'] = str(gpa)
        row['skills'] = json.dumps(base_skills[idx], ensure_ascii=False)
        row['languages'] = json.dumps([{"name": "Thai", "level": "Native"}], ensure_ascii=False)
        row['activities'] = ""

    elif category == 'DEV':
        # Silver: OVR 65-79
        gpa = round(random.uniform(2.8, 3.2), 2)
        base_skills = [
            [{"name": "Python", "level": "Intermediate"}, {"name": "SQL", "level": "Beginner"}],
            [{"name": "Java", "level": "Intermediate"}, {"name": "HTML/CSS", "level": "Intermediate"}],
            [{"name": "Data Analysis", "level": "Beginner"}, {"name": "Tableau", "level": "Intermediate"}],
            [{"name": "C++", "level": "Intermediate"}, {"name": "Git", "level": "Intermediate"}],
            [{"name": "JavaScript", "level": "Intermediate"}, {"name": "React", "level": "Beginner"}],
        ]
        acts = [
            "[Member] at [Coding Club]",
            "[Coordinator] at [KU Tech Event]",
            "[Member] at [Data Science Club]",
            "[Volunteer] at [Tech Camp]",
            "[Member] at [Web Dev Society]"
        ]
        row['gpa'] = str(gpa)
        row['skills'] = json.dumps(base_skills[idx], ensure_ascii=False)
        row['languages'] = json.dumps([{"name": "Thai", "level": "Native"}, {"name": "English", "level": "Intermediate"}], ensure_ascii=False)
        row['activities'] = acts[idx]

    elif category == 'HIGH':
        # Gold: OVR >= 80
        # To get Gold, we need high TEC, ANA, COM, COL, EXP, ACD
        # ACD = GPA/4 * 99 -> 3.9/4 * 99 = 96
        # TEC, ANA -> Advanced/Native -> 92-99
        # COM -> need languages + COM roles ('president', 'speaker')
        # COL -> need COL roles ('lead', 'team', 'committee', 'manager')
        # EXP -> need many roles total
        gpa = round(random.uniform(3.8, 4.0), 2)
        base_skills = [
            [{"name": "Python", "level": "Native"}, {"name": "Machine Learning", "level": "Advanced"}, {"name": "SQL", "level": "Advanced"}],
            [{"name": "React", "level": "Native"}, {"name": "Node.js", "level": "Advanced"}, {"name": "AWS", "level": "Advanced"}],
            [{"name": "C++", "level": "Native"}, {"name": "System Design", "level": "Advanced"}, {"name": "Kubernetes", "level": "Advanced"}],
            [{"name": "Data Analytics", "level": "Native"}, {"name": "Tableau", "level": "Advanced"}, {"name": "Statistics", "level": "Advanced"}],
            [{"name": "Go", "level": "Native"}, {"name": "PostgreSQL", "level": "Advanced"}, {"name": "Microservices", "level": "Advanced"}],
        ]
        langs = [
            [{"name": "Thai", "level": "Native"}, {"name": "English", "level": "Advanced"}],
            [{"name": "Thai", "level": "Native"}, {"name": "English", "level": "Native"}],
            [{"name": "Thai", "level": "Native"}, {"name": "English", "level": "Advanced"}],
            [{"name": "Thai", "level": "Native"}, {"name": "English", "level": "Native"}],
            [{"name": "Thai", "level": "Native"}, {"name": "English", "level": "Advanced"}],
        ]
        
        acts = [
            "[President] at [Computer Engineering Club] | [Lead Backend] at [Hackathon] | [Committee] at [KU Tech Event] | [Speaker] at [AI Summit] | [Manager] at [Startup Camp]",
            "[Host] at [Tech Meetup] | [Head of Dev] at [KU Startup] | [Lead] at [Web Society] | [Team Member] at [Datathon] | [Speaker] at [React BKK]",
            "[President] at [Data Society] | [Lead Researcher] at [AI Lab] | [Manager] at [Internship] | [Committee] at [Engineering Club] | [Writer] at [Tech Blog]",
            "[Speaker] at [Data Conf] | [Director] at [Consulting Club] | [Lead Analyst] at [Datathon 2023] | [Committee] at [BizCamp] | [President] at [Econ Society]",
            "[Founder] at [Tech Community] | [Senior Developer] at [Internship] | [Lead] at [Open Source Project] | [Speaker] at [DevFest] | [Manager] at [Hackathon]"
        ]
        
        row['gpa'] = str(gpa)
        row['skills'] = json.dumps(base_skills[idx], ensure_ascii=False)
        row['languages'] = json.dumps(langs[idx], ensure_ascii=False)
        row['activities'] = acts[idx]

    return row

needs_ids = ['6610400000', '6610400003', '6610400004', '6610400007', '6610400010']
dev_ids = ['6610400013', '6610400015', '6610400017', '6610400018', '6610400019']
high_ids = ['6610400020', '6610400022', '6610400023', '6610400024', '6610400026']

rows = []
with open('data/synthetic_student_dataset_500_clean.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        sid = row['student_id']
        if sid in needs_ids:
            row = update_row(row, 'NEEDS', needs_ids.index(sid))
        elif sid in dev_ids:
            row = update_row(row, 'DEV', dev_ids.index(sid))
        elif sid in high_ids:
            row = update_row(row, 'HIGH', high_ids.index(sid))
        rows.append(row)

with open('data/synthetic_student_dataset_500_clean.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Dataset updated successfully with realistic and Gold-tier profiles.")

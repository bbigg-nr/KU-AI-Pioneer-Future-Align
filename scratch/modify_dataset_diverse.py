import csv
import json
import random

def update_row(row, category, idx):
    if category == 'NEEDS':
        # Scores 30-49
        gpa = round(random.uniform(2.0, 2.5), 2)
        base_skills = [
            [{"name": "Microsoft Word", "level": "Beginner"}],
            [{"name": "Excel", "level": "Beginner"}, {"name": "Communication", "level": "Beginner"}],
            [{"name": "HTML", "level": "Beginner"}],
            [{"name": "PowerPoint", "level": "Intermediate"}, {"name": "Teamwork", "level": "Beginner"}],
            [{"name": "Python", "level": "Beginner"}],
        ]
        row['gpa'] = str(gpa)
        row['skills'] = json.dumps(base_skills[idx], ensure_ascii=False)
        row['languages'] = json.dumps([{"name": "Thai", "level": "Native"}, {"name": "English", "level": "Beginner"}], ensure_ascii=False)
        row['activities'] = ""

    elif category == 'DEV':
        # Scores 50-74
        gpa = round(random.uniform(2.8, 3.2), 2)
        base_skills = [
            [{"name": "Python", "level": "Intermediate"}, {"name": "SQL", "level": "Beginner"}, {"name": "Communication", "level": "Intermediate"}],
            [{"name": "Java", "level": "Intermediate"}, {"name": "Teamwork", "level": "Intermediate"}, {"name": "HTML/CSS", "level": "Advanced"}],
            [{"name": "Data Analysis", "level": "Beginner"}, {"name": "Python", "level": "Advanced"}, {"name": "Tableau", "level": "Beginner"}],
            [{"name": "C++", "level": "Intermediate"}, {"name": "Problem Solving", "level": "Advanced"}, {"name": "Git", "level": "Intermediate"}],
            [{"name": "JavaScript", "level": "Intermediate"}, {"name": "React", "level": "Beginner"}, {"name": "Node.js", "level": "Beginner"}],
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
        # Scores 75+
        gpa = round(random.uniform(3.6, 4.0), 2)
        base_skills = [
            [{"name": "Python", "level": "Advanced"}, {"name": "Machine Learning", "level": "Advanced"}, {"name": "SQL", "level": "Advanced"}, {"name": "Docker", "level": "Intermediate"}],
            [{"name": "React", "level": "Advanced"}, {"name": "Node.js", "level": "Advanced"}, {"name": "TypeScript", "level": "Advanced"}, {"name": "AWS", "level": "Intermediate"}],
            [{"name": "C++", "level": "Native"}, {"name": "Data Structures", "level": "Advanced"}, {"name": "System Design", "level": "Advanced"}, {"name": "Kubernetes", "level": "Beginner"}],
            [{"name": "Data Analytics", "level": "Advanced"}, {"name": "Python", "level": "Advanced"}, {"name": "Tableau", "level": "Advanced"}, {"name": "Statistics", "level": "Advanced"}],
            [{"name": "Go", "level": "Advanced"}, {"name": "Microservices", "level": "Advanced"}, {"name": "Kafka", "level": "Intermediate"}, {"name": "PostgreSQL", "level": "Advanced"}],
        ]
        # Add soft skills
        soft_skills = [{"name": "Leadership", "level": "Advanced"}, {"name": "Communication", "level": "Advanced"}]
        for s in base_skills:
            s.extend(soft_skills)

        langs = [
            [{"name": "Thai", "level": "Native"}, {"name": "English", "level": "Native"}, {"name": "Japanese", "level": "Intermediate"}],
            [{"name": "Thai", "level": "Native"}, {"name": "English", "level": "Advanced"}],
            [{"name": "Thai", "level": "Native"}, {"name": "English", "level": "Native"}, {"name": "Chinese", "level": "Intermediate"}],
            [{"name": "Thai", "level": "Native"}, {"name": "English", "level": "Advanced"}, {"name": "German", "level": "Beginner"}],
            [{"name": "Thai", "level": "Native"}, {"name": "English", "level": "Native"}],
        ]
        
        acts = [
            "[President] at [Computer Engineering Club] | [Lead Backend] at [Hackathon]",
            "[Head of Dev] at [KU Startup] | [Speaker] at [Tech Meetup]",
            "[Lead Researcher] at [AI Lab] | [Vice President] at [Data Society]",
            "[Project Manager] at [Consulting Club] | [Winner] at [Datathon 2023]",
            "[Founder] at [Tech Community] | [Senior Developer] at [Internship]"
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

print("Dataset updated successfully with diverse profiles.")

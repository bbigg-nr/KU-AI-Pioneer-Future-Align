import csv

def get_target_career(idx, category):
    if category == 'HIGH':
        return [
            "Machine Learning Engineer",
            "Software Engineer",
            "Backend Engineer",
            "Data Analyst",
            "Backend Engineer"
        ][idx]
    elif category == 'DEV':
        return [
            "Data Analyst",
            "Software Engineer",
            "Data Analyst",
            "Software Engineer",
            "Frontend Engineer"
        ][idx]
    elif category == 'NEEDS':
        return [
            "Admin Assistant", # generic
            "Business Analyst",
            "Web Developer",
            "Consultant",
            "Software Engineer"
        ][idx]
    return ""

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
            row['target_career'] = get_target_career(needs_ids.index(sid), 'NEEDS')
        elif sid in dev_ids:
            row['target_career'] = get_target_career(dev_ids.index(sid), 'DEV')
        elif sid in high_ids:
            row['target_career'] = get_target_career(high_ids.index(sid), 'HIGH')
        rows.append(row)

with open('data/synthetic_student_dataset_500_clean.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Updated target_careers")

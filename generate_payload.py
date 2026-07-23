import json
import csv

def generate_json():
    rows = []
    with open('gre_errors_2026-04-24.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "starred": row['Starred'] == 'Y',
                "topic": row['Topic'],
                "subtopic": row['Subtopic'],
                "qnum": row['Q#'].strip(),
                "etype": row['Error Type'],
                "did": row['What I Did'],
                "should": row['What I Should Have Done'],
                "root": row['Root Cause'],
                "review": row['Review'],
                "image": None
            })
    
    with open('payload.json', 'w', encoding='utf-8') as f:
        json.dump(rows, f)

if __name__ == "__main__":
    generate_json()

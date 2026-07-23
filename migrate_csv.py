import json
import urllib.request
import csv

SUPABASE_URL = 'https://lfxpoxxwvhkkllywikuk.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxmeHBveHh3dmhra2x5d3lpa3VrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2NDA5NDQsImV4cCI6MjA5MzIxNjk0NH0.0gG0_wXaPsOScR4w2BdQ3DXUWOKe17d_8VYpPdTaKBo'

def migrate():
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

    url = f"{SUPABASE_URL}/rest/v1/errors"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    req = urllib.request.Request(url, data=json.dumps(rows).encode(), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Successfully migrated {len(rows)} rows.")
    except Exception as e:
        print(f"Error migrating: {e}")

if __name__ == "__main__":
    migrate()

import sqlite3

conn = sqlite3.connect("data/jobs.db")
conn.row_factory = sqlite3.Row

kept = conn.execute("""
    SELECT c.name, COUNT(*) as kept_count
    FROM postings p
    JOIN companies c ON c.id = p.company_id
    WHERE p.hard_filter_verdict = 'keep' AND p.closed_at IS NULL
    GROUP BY c.id, c.name
    ORDER BY kept_count DESC
""").fetchall()

any_posts = conn.execute("""
    SELECT COUNT(DISTINCT company_id) FROM postings WHERE closed_at IS NULL
""").fetchone()[0]

print(f"Companies with any open posting (any role): {any_posts}")
print(f"Companies with kept PM posting: {len(kept)}")
print()
print("--- Companies with kept PM roles ---")
for r in kept:
    print(f"  {r['name']}: {r['kept_count']} role(s)")

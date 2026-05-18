import json
seeds = json.load(open("seeds/companies.json"))
existing_slugs = {c["ats_slug"] for c in seeds}
existing_names = {c["name"].lower() for c in seeds}
probe = json.load(open("data/full_gap_probe.json"))
all_found = probe["greenhouse"] + probe["lever"]
dupes = [r for r in all_found if r["ats_slug"] in existing_slugs or r["name"].lower() in existing_names]
clean = [r for r in all_found if r["ats_slug"] not in existing_slugs and r["name"].lower() not in existing_names]
print(f"Clean new: {len(clean)}, Already in seeds: {len(dupes)}")
for d in dupes:
    print(f"  DUP: {d['name']} {d['ats_slug']}")

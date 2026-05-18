"""Add the 28 new companies from full_gap_probe.json to seeds/companies.json."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
seeds_path = ROOT / "seeds" / "companies.json"
probe_path = ROOT / "data" / "full_gap_probe.json"

seeds = json.load(seeds_path.open())
existing_slugs = {c["ats_slug"] for c in seeds}
existing_names = {c["name"].lower() for c in seeds}

probe = json.load(probe_path.open())
all_found = probe["greenhouse"] + probe["lever"]
new = [r for r in all_found if r["ats_slug"] not in existing_slugs and r["name"].lower() not in existing_names]

BIO_RE = re.compile(r"therapeutics|biosciences|bio$|pharma|medicine|medical|health|genomics|oncology|genetic", re.I)
FINTECH_RE = re.compile(r"capital|financial|finance|asset|wealth|insurance|trading|invest", re.I)
DEVTOOLS_RE = re.compile(r"software|platform|cloud|security|cyber|tech|data|ai|ml|intelligence", re.I)
ENERGY_RE = re.compile(r"energy|solar|wind|battery|power|grid|electric", re.I)

def guess_tags(name: str) -> list[str]:
    if BIO_RE.search(name):
        return ["health_bio"]
    if ENERGY_RE.search(name):
        return ["climate_energy"]
    if FINTECH_RE.search(name):
        return ["fintech"]
    if DEVTOOLS_RE.search(name):
        return ["saas"]
    return []

def guess_size(name: str) -> str:
    return "unknown"

for r in new:
    seeds.append({
        "name": r["name"],
        "ats_provider": r["ats"],
        "ats_slug": r["ats_slug"],
        "careers_url": f"https://www.builtinboston.com/company/{r['bib_slug']}",
        "sector_tags": guess_tags(r["name"]),
        "size_band": "unknown",
    })
    print(f"  + {r['name']} ({r['ats']}:{r['ats_slug']})")

seeds_path.write_text(json.dumps(seeds, indent=2))
print(f"\nAdded {len(new)} companies. Total: {len(seeds)}")

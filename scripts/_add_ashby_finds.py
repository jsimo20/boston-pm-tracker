"""Add 41 Ashby companies from the full gap probe to seeds/companies.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
seeds_path = ROOT / "seeds" / "companies.json"

seeds = json.load(seeds_path.open())
existing_slugs = {c["ats_slug"] for c in seeds}

NEW_ASHBY = [
    {"name": "OnRamp", "ats_slug": "onramp", "sector_tags": ["fintech", "consumer_at_scale"], "size_band": "51-200"},
    {"name": "Overjet", "ats_slug": "overjet", "sector_tags": ["ai_agentic", "health_bio"], "size_band": "51-200"},
    {"name": "Vend Park", "ats_slug": "vend-park", "sector_tags": ["saas"], "size_band": "1-50"},
    {"name": "Paddle", "ats_slug": "paddle", "sector_tags": ["fintech", "developer_platform", "saas"], "size_band": "201-500"},
    {"name": "VitVio", "ats_slug": "vitvio", "sector_tags": ["health_bio"], "size_band": "1-50"},
    {"name": "Volition Capital", "ats_slug": "volition-capital", "sector_tags": ["venture"], "size_band": "1-50"},
    {"name": "Own Up", "ats_slug": "ownup", "sector_tags": ["fintech"], "size_band": "51-200"},
    {"name": "Wistia", "ats_slug": "wistia", "sector_tags": ["saas", "martech"], "size_band": "51-200"},
    {"name": "GridUnity", "ats_slug": "gridunity", "sector_tags": ["cleantech", "saas"], "size_band": "1-50"},
    {"name": "ZOE", "ats_slug": "zoe", "sector_tags": ["health_bio", "consumer_at_scale"], "size_band": "51-200"},
    {"name": "Help Scout", "ats_slug": "helpscout", "sector_tags": ["saas"], "size_band": "51-200"},
    {"name": "Posh AI", "ats_slug": "posh-ai", "sector_tags": ["ai_agentic", "fintech"], "size_band": "51-200"},
    {"name": "Hologram Sciences", "ats_slug": "hologramsciences", "sector_tags": ["health_bio", "consumer_at_scale"], "size_band": "51-200"},
    {"name": "Progress Partners", "ats_slug": "progress-partners", "sector_tags": ["consulting"], "size_band": "1-50"},
    {"name": "billups", "ats_slug": "billups", "sector_tags": ["adtech", "saas"], "size_band": "201-500"},
    {"name": "connectRN", "ats_slug": "connectrn", "sector_tags": ["health_bio", "marketplace"], "size_band": "51-200"},
    {"name": "Industrious", "ats_slug": "industrious", "sector_tags": ["proptech"], "size_band": "201-500"},
    {"name": "Jellyfish", "ats_slug": "jellyfish", "sector_tags": ["developer_platform", "saas"], "size_band": "51-200"},
    {"name": "Catena Labs", "ats_slug": "catena-labs", "sector_tags": ["ai_agentic", "fintech"], "size_band": "1-50"},
    {"name": "Keragon", "ats_slug": "keragon", "sector_tags": ["health_bio", "saas"], "size_band": "1-50"},
    {"name": "Clarion", "ats_slug": "clarion", "sector_tags": ["ai_agentic", "construction_tech"], "size_band": "1-50"},
    {"name": "Clasp", "ats_slug": "clasp", "sector_tags": ["fintech", "edtech"], "size_band": "1-50"},
    {"name": "CloudZero", "ats_slug": "cloudzero", "sector_tags": ["developer_platform", "saas"], "size_band": "51-200"},
    {"name": "Compa", "ats_slug": "compa", "sector_tags": ["hr_saas", "saas"], "size_band": "1-50"},
    {"name": "Armanino", "ats_slug": "companyname", "sector_tags": ["consulting"], "size_band": "500+"},
    {"name": "Semgrep", "ats_slug": "semgrep", "sector_tags": ["developer_platform", "security"], "size_band": "51-200"},
    {"name": "M Squared", "ats_slug": "msquared", "sector_tags": ["consulting"], "size_band": "1-50"},
    {"name": "Mainstay", "ats_slug": "mainstay", "sector_tags": ["ai_agentic", "edtech"], "size_band": "51-200"},
    {"name": "Cyvl", "ats_slug": "cyvl", "sector_tags": ["ai_agentic", "construction_tech"], "size_band": "1-50"},
    {"name": "Snowflake", "ats_slug": "snowflake", "sector_tags": ["developer_platform", "saas"], "size_band": "500+"},
    {"name": "Smartleaf", "ats_slug": "smartleaf", "sector_tags": ["fintech"], "size_band": "51-200"},
    {"name": "Snyk", "ats_slug": "snyk", "sector_tags": ["developer_platform", "security"], "size_band": "500+"},
    {"name": "Maven AGI", "ats_slug": "maven-agi", "sector_tags": ["ai_agentic", "saas"], "size_band": "51-200"},
    {"name": "Maxima Consulting", "ats_slug": "maxima-consulting", "sector_tags": ["consulting"], "size_band": "51-200"},
    {"name": "Metalenz", "ats_slug": "metalenz", "sector_tags": ["silicon", "iot_edge"], "size_band": "51-200"},
    {"name": "Bynder", "ats_slug": "bynder", "sector_tags": ["saas", "martech"], "size_band": "201-500"},
    {"name": "Eight Sleep", "ats_slug": "eightsleep", "sector_tags": ["consumer_at_scale", "iot_edge"], "size_band": "201-500"},
    {"name": "CATALOG", "ats_slug": "catalog", "sector_tags": ["biotech", "silicon"], "size_band": "51-200"},
    {"name": "Newfront", "ats_slug": "newfront", "sector_tags": ["fintech", "insurtech"], "size_band": "201-500"},
    {"name": "Nexxen", "ats_slug": "nexxen", "sector_tags": ["adtech"], "size_band": "500+"},
    {"name": "Topologic", "ats_slug": "topologic", "sector_tags": ["saas"], "size_band": "1-50"},
]

added = 0
skipped = 0
for c in NEW_ASHBY:
    if c["ats_slug"] in existing_slugs:
        print(f"  SKIP (already in seeds): {c['name']} -> {c['ats_slug']}")
        skipped += 1
        continue
    seeds.append({
        "name": c["name"],
        "ats_provider": "ashby",
        "ats_slug": c["ats_slug"],
        "careers_url": f"https://jobs.ashbyhq.com/{c['ats_slug']}",
        "sector_tags": c["sector_tags"],
        "size_band": c["size_band"],
    })
    print(f"  + {c['name']} (ashby:{c['ats_slug']})")
    added += 1

seeds_path.write_text(json.dumps(seeds, indent=2))
print(f"\nAdded {added}, skipped {skipped}. Total: {len(seeds)}")

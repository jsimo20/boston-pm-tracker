"""For a sample of not-found companies, probe multiple ATSs to understand the gap.

Checks: Greenhouse (extra slug variants), Lever (extra variants), Ashby, Workday,
SmartRecruiters, Rippling, and Jobvite — just enough to categorise the distribution.
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

TIMEOUT = 10.0
CONCURRENCY = 30


def slug_variants(bib_slug: str, name: str) -> list[str]:
    variants = {bib_slug}
    # lowercase name, spaces -> hyphens
    h = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    variants.add(h)
    # no separators at all
    variants.add(re.sub(r"[^a-z0-9]+", "", name.lower()))
    # drop common suffixes
    for suffix in ["-inc", "-llc", "-corp", "-co", "-technologies", "-tech", "-software"]:
        if bib_slug.endswith(suffix):
            variants.add(bib_slug[: -len(suffix)])
    return list(variants)


async def probe_greenhouse(slug: str, client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(f"https://api.greenhouse.io/v1/boards/{slug}/jobs", timeout=TIMEOUT)
        return r.status_code == 200 and "jobs" in r.json()
    except Exception:
        return False


async def probe_lever(slug: str, client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(f"https://api.lever.co/v0/postings/{slug}?mode=json", timeout=TIMEOUT)
        return r.status_code == 200 and isinstance(r.json(), list)
    except Exception:
        return False


async def probe_ashby(slug: str, client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(f"https://jobs.ashbyhq.com/{slug}", timeout=TIMEOUT)
        return r.status_code == 200 and "ashbyhq" in r.text.lower()
    except Exception:
        return False


async def probe_workday(name: str, client: httpx.AsyncClient) -> bool:
    # Workday careers pages follow myworkdayjobs.com — probe via Google-like pattern check
    slug = re.sub(r"[^a-z0-9]+", "", name.lower())
    for domain in [f"https://{slug}.wd1.myworkdayjobs.com", f"https://{slug}.wd5.myworkdayjobs.com"]:
        try:
            r = await client.get(domain, timeout=TIMEOUT)
            if r.status_code < 400:
                return True
        except Exception:
            pass
    return False


async def probe_smartrecruiters(slug: str, client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(f"https://careers.smartrecruiters.com/{slug}", timeout=TIMEOUT)
        return r.status_code == 200
    except Exception:
        return False


async def probe_company(company: dict, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> dict:
    name = company["name"]
    bib_slug = company["bib_slug"]
    variants = slug_variants(bib_slug, name)

    result = {"name": name, "bib_slug": bib_slug, "ats": "unknown"}

    async with sem:
        # Try Greenhouse with all variants
        for s in variants:
            if await probe_greenhouse(s, client):
                result["ats"] = "greenhouse"
                result["ats_slug"] = s
                return result

        # Try Lever with all variants
        for s in variants:
            if await probe_lever(s, client):
                result["ats"] = "lever"
                result["ats_slug"] = s
                return result

        # Try Ashby
        for s in variants:
            if await probe_ashby(s, client):
                result["ats"] = "ashby"
                result["ats_slug"] = s
                return result

        # Try SmartRecruiters
        for s in variants:
            if await probe_smartrecruiters(s, client):
                result["ats"] = "smartrecruiters"
                result["ats_slug"] = s
                return result

        # Try Workday (slower, do last)
        if await probe_workday(name, client):
            result["ats"] = "workday"

    return result


async def main() -> None:
    not_found = json.loads((DATA_DIR / "ats_discovered.json").read_text())["not_found"]
    # Sample: first 300 for speed, spread across alphabet
    sample = not_found[:300]

    print(f"Probing {len(sample)} not-found companies across 5 ATSs...", flush=True)
    sem = asyncio.Semaphore(CONCURRENCY)
    results = []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [probe_company(c, client, sem) for c in sample]
        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            r = await coro
            results.append(r)
            if i % 50 == 0:
                print(f"  {i}/{len(sample)}", flush=True)

    # Tally
    from collections import Counter
    tally = Counter(r["ats"] for r in results)
    found_elsewhere = [r for r in results if r["ats"] != "unknown"]

    print("\n--- ATS distribution (sample of 300 not-found) ---")
    for ats, count in tally.most_common():
        print(f"  {ats}: {count}")

    print(f"\nFound on non-GH/Lever ATS: {len(found_elsewhere)}")
    for r in sorted(found_elsewhere, key=lambda x: x["ats"]):
        print(f"  [{r['ats']}] {r['name']}")

    out = {"sample_size": len(sample), "tally": dict(tally), "found_elsewhere": found_elsewhere}
    (DATA_DIR / "ats_gap_analysis.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

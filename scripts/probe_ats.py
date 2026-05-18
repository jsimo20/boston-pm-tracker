"""Probe Greenhouse and Lever APIs for all BIB companies to discover ATS provider + slug.

Usage:
    python scripts/probe_ats.py

Writes results to data/ats_discovered.json.
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
INPUT = DATA_DIR / "builtinboston_companies_with_slugs.json"
OUTPUT = DATA_DIR / "ats_discovered.json"

GREENHOUSE_URL = "https://api.greenhouse.io/v1/boards/{slug}/jobs"
LEVER_URL = "https://api.lever.co/v0/postings/{slug}?mode=json"

CONCURRENCY = 40
TIMEOUT = 15.0


def candidate_slugs(bib_slug: str, name: str) -> list[str]:
    """Generate candidate ATS slugs from BIB slug and company name."""
    candidates = [bib_slug]
    # Also try name-derived slug: lowercase, replace spaces/special chars with hyphens
    name_slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if name_slug != bib_slug:
        candidates.append(name_slug)
    # Also try without hyphens (common Greenhouse pattern)
    no_hyphen = bib_slug.replace("-", "")
    if no_hyphen not in candidates:
        candidates.append(no_hyphen)
    return candidates


async def probe_greenhouse(slug: str, client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(GREENHOUSE_URL.format(slug=slug), timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            return isinstance(data, dict) and "jobs" in data
    except Exception:
        pass
    return False


async def probe_lever(slug: str, client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(LEVER_URL.format(slug=slug), timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            return isinstance(data, list)
    except Exception:
        pass
    return False


async def probe_company(company: dict, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> dict | None:
    name = company["name"]
    bib_slug = company["bib_slug"]
    slugs = candidate_slugs(bib_slug, name)

    async with sem:
        for slug in slugs:
            if await probe_greenhouse(slug, client):
                return {**company, "ats_provider": "greenhouse", "ats_slug": slug}
            if await probe_lever(slug, client):
                return {**company, "ats_provider": "lever", "ats_slug": slug}
    return None


async def main() -> None:
    companies = json.loads(INPUT.read_text(encoding="utf-8"))["companies"]
    print(f"Probing {len(companies)} companies (concurrency={CONCURRENCY})...", flush=True)

    sem = asyncio.Semaphore(CONCURRENCY)
    found: list[dict] = []
    not_found: list[dict] = []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [probe_company(c, client, sem) for c in companies]
        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            result = await coro
            if result:
                found.append(result)
            else:
                not_found.append(companies[i - 1])
            if i % 100 == 0 or i == len(companies):
                print(f"  {i}/{len(companies)}  found={len(found)}", flush=True)

    output = {
        "found_count": len(found),
        "not_found_count": len(not_found),
        "found": sorted(found, key=lambda x: x["name"]),
        "not_found": sorted(not_found, key=lambda x: x["name"]),
    }
    OUTPUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nDone. {len(found)} companies discovered → {OUTPUT}")


if __name__ == "__main__":
    asyncio.run(main())

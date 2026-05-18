"""Probe the full not-found tail (companies 301–1950) for GH and Lever.

Skips SmartRecruiters (known false positive) and companies already in seeds.
Writes actionable finds to data/full_gap_probe.json.
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SEEDS_PATH = Path(__file__).resolve().parents[1] / "seeds" / "companies.json"

TIMEOUT = 10.0
CONCURRENCY = 40


def slug_variants(bib_slug: str, name: str) -> list[str]:
    variants: set[str] = {bib_slug}
    h = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    variants.add(h)
    variants.add(re.sub(r"[^a-z0-9]+", "", name.lower()))
    for suffix in ["-inc", "-llc", "-corp", "-co", "-technologies", "-tech", "-software", "-labs", "-health", "-bio"]:
        if bib_slug.endswith(suffix):
            variants.add(bib_slug[: -len(suffix)])
    # try dropping leading numbers/articles
    name_words = re.sub(r"[^a-z0-9\s]+", "", name.lower()).split()
    if name_words and name_words[0] in {"the", "a", "an"}:
        variants.add("-".join(name_words[1:]))
        variants.add("".join(name_words[1:]))
    return list(variants)


async def probe_greenhouse(slug: str, client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(
            f"https://api.greenhouse.io/v1/boards/{slug}/jobs", timeout=TIMEOUT
        )
        return r.status_code == 200 and "jobs" in r.json()
    except Exception:
        return False


async def probe_lever(slug: str, client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(
            f"https://api.lever.co/v0/postings/{slug}?mode=json", timeout=TIMEOUT
        )
        return r.status_code == 200 and isinstance(r.json(), list)
    except Exception:
        return False


async def probe_company(
    company: dict, client: httpx.AsyncClient, sem: asyncio.Semaphore
) -> dict | None:
    name = company["name"]
    bib_slug = company["bib_slug"]
    variants = slug_variants(bib_slug, name)

    async with sem:
        for s in variants:
            if await probe_greenhouse(s, client):
                return {"name": name, "bib_slug": bib_slug, "ats": "greenhouse", "ats_slug": s}
        for s in variants:
            if await probe_lever(s, client):
                return {"name": name, "bib_slug": bib_slug, "ats": "lever", "ats_slug": s}

    return None


async def main() -> None:
    not_found = json.loads((DATA_DIR / "ats_discovered.json").read_text())["not_found"]
    existing_slugs = {c["ats_slug"] for c in json.loads(SEEDS_PATH.read_text())}

    # Skip the first 300 (already sampled) and any already in seeds
    tail = [c for c in not_found[300:] if c["bib_slug"] not in existing_slugs]
    print(f"Probing {len(tail)} companies (GH + Lever only)...", flush=True)

    sem = asyncio.Semaphore(CONCURRENCY)
    found: list[dict] = []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [probe_company(c, client, sem) for c in tail]
        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            result = await coro
            if result:
                found.append(result)
                print(f"  [{result['ats']}] {result['name']} -> {result['ats_slug']}", flush=True)
            if i % 100 == 0:
                print(f"  progress: {i}/{len(tail)} ({len(found)} found so far)", flush=True)

    gh = [r for r in found if r["ats"] == "greenhouse"]
    lv = [r for r in found if r["ats"] == "lever"]
    print(f"\nDone. Found {len(gh)} Greenhouse + {len(lv)} Lever across {len(tail)} probed.")

    out = {"probed": len(tail), "greenhouse": gh, "lever": lv}
    (DATA_DIR / "full_gap_probe.json").write_text(json.dumps(out, indent=2))
    print(f"Wrote data/full_gap_probe.json")


if __name__ == "__main__":
    asyncio.run(main())

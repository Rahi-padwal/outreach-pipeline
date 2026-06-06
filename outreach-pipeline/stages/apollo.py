"""
Stage 1 — Find lookalike companies using Apollo.io.

Flow:
  1. Enrich the seed domain -> get industry, size, keywords.
  2. Search Apollo for companies sharing those attributes.
  3. Return up to `limit` primary domains, excluding the seed itself.

Apollo REST docs: https://docs.apollo.io/
Authentication: X-Api-Key header (query-param auth was deprecated).
Base URL: https://api.apollo.io/api/v1  (note: /api/v1 not /v1)
"""

import time
import requests
from config import APOLLO_API_KEY
from utils.logger import info, success, warning, error

BASE_URL = "https://api.apollo.io/api/v1"

# Apollo now requires the key in the X-Api-Key header, not as a query param.
HEADERS = {
    "X-Api-Key": APOLLO_API_KEY,
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
}


def _employee_range(n: int) -> str:
    """Map a headcount to Apollo's comma-separated range format."""
    if n <= 10:
        return "1,10"
    if n <= 50:
        return "11,50"
    if n <= 200:
        return "51,200"
    if n <= 1000:
        return "201,1000"
    if n <= 5000:
        return "1001,5000"
    return "5001,10000"


def _enrich_company(domain: str) -> dict | None:
    """Fetch structured metadata for a company from Apollo's enrich endpoint."""
    try:
        resp = requests.get(
            f"{BASE_URL}/organizations/enrich",
            headers=HEADERS,
            params={"domain": domain},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("organization") or {}
    except requests.exceptions.HTTPError as e:
        error(f"Apollo enrich failed ({e.response.status_code}): {e.response.text[:300]}")
        return None
    except requests.exceptions.RequestException as e:
        error(f"Apollo enrich request error: {e}")
        return None


def find_lookalike_companies(seed_domain: str, limit: int = 10) -> list[str]:
    """
    Return up to `limit` company domains similar to seed_domain.

    Strategy:
      - Enrich seed to get industry, headcount, keywords.
      - Search Apollo for orgs sharing those keyword tags + same size tier.
      - Fall back to a keyword-only search if the first pass is thin.
    """
    info(f"Enriching seed company: {seed_domain}")
    seed = _enrich_company(seed_domain)

    if not seed:
        error("Could not retrieve seed company data from Apollo.")
        return []

    seed_name = seed.get("name") or seed_domain
    success(f"Seed company: {seed_name}")
    info(f"  Industry : {seed.get('industry') or 'unknown'}")
    info(f"  Employees: {seed.get('estimated_num_employees') or 'unknown'}")

    headcount = seed.get("estimated_num_employees") or 100
    keywords = (seed.get("keywords") or [])[:6]
    industry = seed.get("industry") or ""

    # Prepend the industry string as an extra keyword tag.
    if industry and industry.lower() not in [k.lower() for k in keywords]:
        keywords.insert(0, industry)

    emp_range = _employee_range(headcount)
    info(f"Searching lookalikes (size: {emp_range}, tags: {keywords[:4]})...")

    payload: dict = {
        "page": 1,
        "per_page": limit + 10,
        "organization_num_employees_ranges": [emp_range],
    }
    if keywords:
        payload["q_organization_keyword_tags"] = keywords

    domains = _run_org_search(payload, seed_domain, seed_name, limit)

    # Widen the net if the first pass didn't yield enough.
    if len(domains) < limit:
        info("Relaxing size filter for more results...")
        payload.pop("organization_num_employees_ranges", None)
        payload["per_page"] = (limit - len(domains)) + 10
        extra = _run_org_search(payload, seed_domain, seed_name, limit - len(domains))
        seen = set(domains)
        for d in extra:
            if d not in seen:
                domains.append(d)
                seen.add(d)

    return domains[:limit]


def _run_org_search(payload: dict, seed_domain: str, seed_name: str, limit: int) -> list[str]:
    """Execute one Apollo /mixed_companies/search POST and return a domain list."""
    try:
        resp = requests.post(
            f"{BASE_URL}/organizations/search",
            json=payload,
            headers=HEADERS,
            timeout=20,
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        error(f"Apollo search failed ({e.response.status_code}): {e.response.text[:300]}")
        return []
    except requests.exceptions.RequestException as e:
        error(f"Apollo search request error: {e}")
        return []

    orgs = resp.json().get("organizations") or []

    domains: list[str] = []
    for org in orgs:
        domain = (org.get("primary_domain") or "").strip().lower()
        name = (org.get("name") or "").strip().lower()
        if not domain:
            continue
        if domain == seed_domain.lower() or name == seed_name.lower():
            continue

        domains.append(domain)
        success(f"  Lookalike: {org.get('name', domain)} ({domain})")

        if len(domains) >= limit:
            break

    time.sleep(0.5)
    return domains

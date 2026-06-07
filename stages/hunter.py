"""
Stages 2 & 3 — Decision-maker discovery + verified emails via Hunter.io.

Hunter's /v2/domain-search returns names, job titles, and verified work
emails in a single call, so there is no separate LinkedIn lookup step.

Hunter docs: https://hunter.io/api-documentation
Auth: api_key query parameter.
"""

import time
import requests
from config import HUNTER_API_KEY
from utils.logger import info, warning, error

BASE_URL = "https://api.hunter.io/v2"

SENIOR_KEYWORDS = (
    "ceo", "cto", "cmo", "cfo", "coo", "cpo", "ciso",
    "chief", "founder", "co-founder", "cofounder",
    "president", "owner",
    "vp ", "v.p.", "vice president",
    "director", "head of", "head,",
    "managing partner", "general manager",
)


def _is_senior(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in SENIOR_KEYWORDS)


def find_contacts(domain: str, max_per_domain: int = 5) -> list[dict]:
    """
    Stages 2 & 3 combined — fetch verified contacts at `domain` from
    Hunter's domain-search endpoint and filter to senior titles only.

    Returns a list of dicts with: first_name, last_name, title,
    company, domain, email.
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/domain-search",
            params={
                "domain": domain,
                "api_key": HUNTER_API_KEY,
                "limit": 10,       # free plan cap; paid plans allow more
                "type": "personal",
            },
            timeout=15,
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        error(f"Hunter domain-search failed ({e.response.status_code}) for {domain}: {e.response.text[:200]}")
        return []
    except requests.exceptions.RequestException as e:
        error(f"Hunter request error for {domain}: {e}")
        return []

    data = resp.json()
    emails = (data.get("data") or {}).get("emails") or []
    company = (data.get("data") or {}).get("organization") or domain

    if not emails:
        warning(f"  Hunter returned no contacts for {domain}")
        return []

    contacts: list[dict] = []
    for person in emails:
        title = (person.get("position") or person.get("title") or "").strip()

        # Skip if no senior title or no verified email
        if not _is_senior(title):
            continue

        email = (person.get("value") or "").strip()
        if not email:
            continue

        # Hunter marks confidence 0-100; skip low-confidence results
        confidence = person.get("confidence") or 0
        if confidence < 50:
            continue

        first = (person.get("first_name") or "").strip()
        last = (person.get("last_name") or "").strip()

        if not first:
            continue

        contacts.append({
            "first_name": first,
            "last_name": last,
            "title": title,
            "company": company,
            "domain": domain,
            "email": email,
        })

        if len(contacts) >= max_per_domain:
            break

    # Polite delay between Hunter calls (free plan: 25 req/month, paid: more).
    time.sleep(1.0)
    return contacts

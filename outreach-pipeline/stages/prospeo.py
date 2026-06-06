"""
Stages 2 & 3 — Decision-maker discovery + email resolution via Prospeo.

Stage 2  find_decision_makers(domain)
  → POST /domain-search
  → Returns people at that company filtered to senior titles only.
  → Each person dict already contains a linkedin_url if Prospeo has it.

Stage 3  find_email_from_linkedin(linkedin_url)
  → POST /linkedin-email-finder
  → Returns a single verified work email or None.

Prospeo docs: https://prospeo.io/api
Auth: X-KEY header (Bearer-style key).
"""

import time
import requests
from config import PROSPEO_API_KEY
from utils.logger import info, success, warning, error

BASE_URL = "https://api.prospeo.io"

HEADERS = {
    "Content-Type": "application/json",
    "X-KEY": PROSPEO_API_KEY,
}

# Title substrings that indicate a decision-making seniority level.
SENIOR_KEYWORDS = (
    "ceo", "cto", "cmo", "cfo", "coo", "cpo", "ciso",
    "chief", "founder", "co-founder", "cofounder",
    "president", "owner",
    "vp ", "v.p.", "vice president",
    "director", "head of", "head,",
    "managing partner", "general manager",
)


def _is_senior(title: str) -> bool:
    """Return True if the title suggests a decision-maker."""
    t = title.lower()
    return any(kw in t for kw in SENIOR_KEYWORDS)


def find_decision_makers(domain: str, max_per_domain: int = 5) -> list[dict]:
    """
    Stage 2 — Find senior contacts at `domain`.

    Calls Prospeo's domain-search endpoint, filters to C-suite / VP /
    Director / Head-of titles, and returns structured contact dicts.
    Each dict has: first_name, last_name, title, company, domain,
                   linkedin_url, email (may be None).
    """
    try:
        resp = requests.post(
            f"{BASE_URL}/domain-search",
            json={"company": domain, "limit": 20},   # fetch more, then filter
            headers=HEADERS,
            timeout=20,
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        error(f"Prospeo domain-search failed ({e.response.status_code}) for {domain}: {e.response.text[:200]}")
        return []
    except requests.exceptions.RequestException as e:
        error(f"Prospeo domain-search request error for {domain}: {e}")
        return []

    data = resp.json()

    # Prospeo wraps the list under "response" key.
    people = data.get("response") or data.get("data") or []
    if not isinstance(people, list):
        warning(f"Unexpected Prospeo response shape for {domain}")
        return []

    contacts: list[dict] = []
    for person in people:
        title = (
            person.get("job_title")
            or person.get("position")
            or person.get("title")
            or ""
        )
        if not _is_senior(title):
            continue

        # Normalize the LinkedIn URL field — Prospeo may call it 'linkedin'
        # or 'linkedin_url' depending on the endpoint version.
        linkedin = (
            person.get("linkedin_url")
            or person.get("linkedin")
            or ""
        )

        # Email may be a string OR a nested object {"value": "...", "verification_status": "..."}
        raw_email = person.get("email")
        if isinstance(raw_email, dict):
            email = raw_email.get("value") if raw_email.get("verification_status") != "invalid" else None
        else:
            email = raw_email or None

        first = (person.get("first_name") or "").strip()
        last = (person.get("last_name") or "").strip()

        if not first:
            # Some endpoints return a single "full_name" field.
            full = (person.get("full_name") or person.get("name") or "").strip()
            parts = full.split(" ", 1)
            first = parts[0]
            last = parts[1] if len(parts) > 1 else ""

        if not first:
            continue   # Can't personalise an email without a name

        contacts.append({
            "first_name": first,
            "last_name": last,
            "title": title,
            "company": person.get("company") or person.get("organization") or domain,
            "domain": domain,
            "linkedin_url": linkedin,
            "email": email,
        })

        if len(contacts) >= max_per_domain:
            break

    # Polite delay between domain-search calls.
    time.sleep(1.0)
    return contacts


def find_email_from_linkedin(linkedin_url: str) -> str | None:
    """
    Stage 3 — Resolve a LinkedIn profile URL to a verified work email.

    Returns the email string on success, None if Prospeo can't find it
    or returns an invalid/risky classification.
    """
    if not linkedin_url:
        return None

    try:
        resp = requests.post(
            f"{BASE_URL}/linkedin-email-finder",
            json={"url": linkedin_url},
            headers=HEADERS,
            timeout=20,
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # 404 / 402 (out of credits) are not crash-worthy, just skip.
        if e.response.status_code in (404, 402, 422):
            return None
        error(f"Prospeo email-finder failed ({e.response.status_code}): {e.response.text[:200]}")
        return None
    except requests.exceptions.RequestException as e:
        error(f"Prospeo email-finder request error: {e}")
        return None

    data = resp.json()

    # Response shape: {"response": {"email": "...", "verification_status": "valid"}}
    inner = data.get("response") or data.get("data") or data
    if isinstance(inner, dict):
        status = inner.get("verification_status") or inner.get("status") or "unknown"
        if status in ("invalid", "risky"):
            return None
        email = inner.get("email") or inner.get("value")
        if email:
            # Polite delay between email-finder calls (credits are precious).
            time.sleep(1.5)
            return email.strip()

    return None

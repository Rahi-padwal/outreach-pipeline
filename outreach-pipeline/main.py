"""
Cold Outreach Pipeline
======================
Usage:  python main.py

Pipeline stages:
  1. Apollo    — find 10 lookalike companies from a seed domain
  2. Prospeo   — discover senior decision-makers at each company
  3. Prospeo   — resolve LinkedIn profiles → verified work emails
  4. Brevo     — checkpoint review → send personalised outreach emails
"""

import sys
import config                                 # validate keys before anything else

from stages.apollo import find_lookalike_companies
from stages.prospeo import find_decision_makers, find_email_from_linkedin
from stages.brevo import send_outreach_emails
from utils.logger import banner, stage, info, success, warning, error
from utils.checkpoint import review_contacts


def get_seed_domain() -> str:
    raw = input("  Enter seed domain (e.g. stripe.com): ").strip()
    if not raw:
        error("No domain entered. Exiting.")
        sys.exit(1)
    # Strip any accidental protocol prefix users might paste.
    return raw.replace("https://", "").replace("http://", "").rstrip("/").lower()


def resolve_emails(contacts: list[dict]) -> list[dict]:
    """
    Stage 3 inline pass: for contacts that already have an email from
    the domain-search response, keep it as-is; for the rest, call the
    LinkedIn email-finder. Contacts that end up with no email are dropped.
    """
    resolved: list[dict] = []
    for c in contacts:
        if c.get("email"):
            resolved.append(c)
            continue

        if c.get("linkedin_url"):
            info(f"    Resolving email for {c['first_name']} {c.get('last_name', '')} via LinkedIn…")
            email = find_email_from_linkedin(c["linkedin_url"])
            if email:
                c["email"] = email
                resolved.append(c)
                success(f"    Found: {email}")
            else:
                warning(f"    No email found — skipping {c['first_name']} {c.get('last_name', '')}")
        else:
            warning(f"    No LinkedIn URL for {c['first_name']} {c.get('last_name', '')} — skipping")

    return resolved


def main():
    banner()
    config.validate()

    # ── Seed domain ───────────────────────────────────────────────────────────
    seed_domain = get_seed_domain()
    print()

    # ── Stage 1 — Lookalike companies ─────────────────────────────────────────
    stage(1, "Finding Lookalike Companies  ·  Apollo.io")
    lookalike_domains = find_lookalike_companies(seed_domain, limit=10)

    if not lookalike_domains:
        error("No lookalike companies found. Check your Apollo key or try a different domain.")
        sys.exit(1)

    success(f"\n{len(lookalike_domains)} lookalike domain(s) identified.\n")

    # ── Stages 2 & 3 — Decision makers + emails ───────────────────────────────
    stage(2, "Finding Decision Makers + Emails  ·  Prospeo")

    all_contacts: list[dict] = []

    for domain in lookalike_domains:
        info(f"\nProcessing {domain}…")

        # Stage 2: domain search → senior people
        people = find_decision_makers(domain, max_per_domain=5)

        if not people:
            warning(f"  No senior contacts found at {domain}")
            continue

        info(f"  {len(people)} senior contact(s) — resolving emails…")

        # Stage 3: fill in missing emails
        with_emails = resolve_emails(people)

        if not with_emails:
            warning(f"  No verified emails for any contact at {domain}")
            continue

        all_contacts.extend(with_emails)
        success(f"  {len(with_emails)} contact(s) ready from {domain}")

    if not all_contacts:
        error("\nNo contacts with verified emails. Nothing to send. Exiting.")
        sys.exit(1)

    success(f"\n{len(all_contacts)} total contact(s) with verified emails across all companies.")

    # ── Stage 4 — Safety checkpoint + send ───────────────────────────────────
    stage(4, "Personalised Outreach  ·  Brevo")

    if not review_contacts(all_contacts):
        info("\nEmail sending cancelled. No messages were sent.")
        sys.exit(0)

    print()
    send_outreach_emails(all_contacts)
    success("\nPipeline complete.")


if __name__ == "__main__":
    main()

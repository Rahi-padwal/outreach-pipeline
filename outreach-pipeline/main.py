"""
Cold Outreach Pipeline

Pipeline stages:
  1. Apollo   -- find 10 lookalike companies from a seed domain
  2+3. Hunter -- discover senior decision-makers + verified emails in one call
  4. Brevo    -- checkpoint review -> send personalised outreach emails
"""

import sys
import config

from stages.apollo import find_lookalike_companies
from stages.hunter import find_contacts
from stages.brevo import send_outreach_emails
from utils.logger import banner, stage, info, success, warning, error
from utils.checkpoint import review_contacts


def get_seed_domain() -> str:
    raw = input("  Enter seed domain (e.g. stripe.com): ").strip()
    if not raw:
        error("No domain entered. Exiting.")
        sys.exit(1)
    return raw.replace("https://", "").replace("http://", "").rstrip("/").lower()


def main():
    banner()
    config.validate()

    seed_domain = get_seed_domain()
    print()

    # -- Stage 1: Lookalike companies -----------------------------------------
    stage(1, "Finding Lookalike Companies  -  Apollo.io")
    lookalike_domains = find_lookalike_companies(seed_domain, limit=10)

    if not lookalike_domains:
        error("No lookalike companies found. Check your Apollo key or try a different domain.")
        sys.exit(1)

    success(f"\n{len(lookalike_domains)} lookalike domain(s) identified.\n")

    # -- Stages 2 & 3: Decision makers + verified emails (Hunter) -------------
    stage(2, "Finding Decision Makers + Emails  -  Hunter.io")

    all_contacts: list[dict] = []

    for domain in lookalike_domains:
        info(f"\nProcessing {domain}...")
        contacts = find_contacts(domain, max_per_domain=5)

        if not contacts:
            warning(f"  No senior contacts with verified emails at {domain}")
            continue

        for c in contacts:
            info(f"  {c['first_name']} {c['last_name']} | {c['title']} | {c['email']}")

        all_contacts.extend(contacts)
        success(f"  {len(contacts)} contact(s) ready from {domain}")

    if not all_contacts:
        error("\nNo contacts with verified emails found. Nothing to send. Exiting.")
        sys.exit(1)

    success(f"\n{len(all_contacts)} total contact(s) with verified emails across all companies.")

    # -- Stage 4: Safety checkpoint + send ------------------------------------
    stage(4, "Personalised Outreach  -  Brevo")

    if not review_contacts(all_contacts):
        info("\nEmail sending cancelled. No messages were sent.")
        sys.exit(0)

    print()
    send_outreach_emails(all_contacts)
    success("\nPipeline complete.")


if __name__ == "__main__":
    main()

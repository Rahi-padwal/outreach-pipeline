"""
Stage 4 — Send personalised outreach emails via Brevo (transactional API).

Brevo docs: https://developers.brevo.com/reference/sendtransacemail
Auth: api-key header.

The email copy is intentionally concise and human — first-name greeting,
one-line company callout, a soft ask. No HTML blast aesthetic.
"""

import time
import requests
from config import BREVO_API_KEY, SENDER_EMAIL, SENDER_NAME
from utils.logger import info, success, warning, error

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"

HEADERS = {
    "api-key": BREVO_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def _build_email(contact: dict) -> dict:
    """
    Compose a personalised plain-text email for one contact.
    References their first name, company, and role so it never
    reads like a generic blast.
    """
    first = contact["first_name"]
    company = contact.get("company") or contact.get("domain") or "your company"
    title = contact.get("title") or "your role"

    subject = f"Quick thought for {company}"

    # Keep the copy short — two paragraphs, a soft ask, done.
    text_body = f"""Hi {first},

I came across {company} and was genuinely impressed by what you're building. Given your role as {title}, I thought it was worth reaching out directly.

I'm {SENDER_NAME}. I work with growth-stage companies on improving their outbound and customer acquisition — and based on what I've seen from teams like yours, there might be a real opportunity to explore together.

Not looking to pitch anything cold. Just wondering if a 20-minute call would make sense to see if there's a fit.

Would any time next week work for you?

Best,
{SENDER_NAME}
"""

    # Brevo also accepts htmlContent; we send a minimal HTML wrapper
    # so the plain text still renders cleanly in HTML-only email clients.
    html_body = text_body.replace("\n", "<br>")

    return {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": contact["email"], "name": f"{first} {contact.get('last_name', '')}".strip()}],
        "subject": subject,
        "textContent": text_body,
        "htmlContent": f"<p>{html_body}</p>",
    }


def send_outreach_emails(contacts: list[dict]) -> int:
    """
    Send one personalised email to each contact in the list.
    Skips contacts missing an email address.
    Returns the count of successfully delivered messages.
    """
    sent = 0
    failed = 0

    for contact in contacts:
        email = contact.get("email")
        if not email:
            warning(f"Skipping {contact.get('first_name', '?')} {contact.get('last_name', '')} — no email")
            continue

        payload = _build_email(contact)
        name_str = f"{contact['first_name']} {contact.get('last_name', '')}".strip()

        try:
            resp = requests.post(BREVO_SEND_URL, json=payload, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            success(f"Sent → {name_str} <{email}> ({contact.get('company', '')})")
            sent += 1
        except requests.exceptions.HTTPError as e:
            error(f"Brevo rejected {email} ({e.response.status_code}): {e.response.text[:200]}")
            failed += 1
        except requests.exceptions.RequestException as e:
            error(f"Brevo request error for {email}: {e}")
            failed += 1

        # Small delay to avoid hitting Brevo's burst limit (no more than ~10 req/s).
        time.sleep(0.3)

    info(f"\nEmail summary: {sent} sent, {failed} failed out of {len(contacts)} contacts.")
    return sent

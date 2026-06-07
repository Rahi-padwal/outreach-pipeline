# Outreach Pipeline

A fully automated cold-outreach CLI. Give it one company domain — it finds 10 lookalike companies, pulls verified decision-maker emails, and sends personalised outreach. All in under 2 minutes.

```
python main.py
Enter seed domain: stripe.com
```

---

## How it works

```
seed domain
    │
    ▼
Stage 1 — Apollo.io
    Enrich seed company → find 10 lookalike companies by industry, size, keywords
    │
    ▼
Stage 2+3 — Hunter.io
    For each company → find C-suite / VP / Director contacts with verified emails
    │
    ▼
Checkpoint
    Review every contact before anything sends
    │
    ▼
Stage 4 — Brevo
    Send personalised email to each contact (name, company, title)
```

---

## Stack

| Stage | API | What it does |
|-------|-----|-------------|
| 1 | Apollo.io | Finds lookalike companies from a seed domain |
| 2+3 | Hunter.io | Finds decision makers + verified work emails |
| 4 | Brevo | Sends personalised transactional emails |

---

## Setup

**1. Clone and install**
```bash
git clone https://github.com/yourusername/outreach-pipeline
cd outreach-pipeline
pip install -r requirements.txt
```

**2. Add your API keys**
```bash
cp .env.example .env
```

Fill in `.env`:
```
APOLLO_API_KEY=your_key
HUNTER_API_KEY=your_key
BREVO_API_KEY=your_key
SENDER_EMAIL=you@yourdomain.com
SENDER_NAME=Your Name
```

**3. Run**
```bash
python main.py
```

---

## Project structure

```
outreach-pipeline/
├── main.py              # Orchestrates all 4 stages
├── config.py            # Loads and validates env vars
├── stages/
│   ├── apollo.py        # Stage 1: lookalike company discovery
│   ├── hunter.py        # Stage 2+3: contacts + verified emails
│   └── brevo.py         # Stage 4: personalised email sending
├── utils/
│   ├── logger.py        # Coloured terminal output
│   └── checkpoint.py    # Safety review before emails fire
├── .env.example
└── requirements.txt
```

---

## Safety

A checkpoint table is shown before any email is sent — listing every contact's name, title, company, and email. Nothing fires until you explicitly type `yes`.

```
  #    Name              Title                  Company    Email
  1    John Smith        Chief Executive Officer  Acme     john@acme.com
  2    Jane Doe          VP of Engineering        Acme     jane@acme.com
  ...

  Proceed? Type 'yes' to send:
```

---

## API keys

| Service | Free tier |
|---------|-----------|
| [Apollo.io](https://apollo.io) | Organization search + enrich |
| [Hunter.io](https://hunter.io) | 25 domain searches/month |
| [Brevo](https://brevo.com) | 300 emails/day |

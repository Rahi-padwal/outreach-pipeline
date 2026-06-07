# outreach-pipeline

I built this to scratch my own itch. Cold outreach manually is painful — finding similar companies, tracking down who to email, copy-pasting names into templates. This CLI does all of that in one run.

You give it one domain. It figures out the rest.

```
python main.py
Enter seed domain: stripe.com
```

---

## What actually happens

**Step 1** — Apollo.io gets asked about your seed company. Industry, size, keywords. Then it finds 10 companies in the same space.

**Step 2** — For each of those 10 companies, Hunter.io pulls the senior people there — CEOs, VPs, Directors — along with their verified work emails. No LinkedIn needed.

**Step 3** — Before anything sends, you see a full table of every contact. You have to type `yes` to proceed. Nothing fires automatically.

**Step 4** — Brevo sends a personalised email to each person. Different subject, their name, their company, their title.

The whole thing runs in about 2 minutes.

---

## Setup

```bash
git clone https://github.com/Rahi-padwal/outreach-pipeline
cd outreach-pipeline
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with your keys:
```
APOLLO_API_KEY=
HUNTER_API_KEY=
BREVO_API_KEY=
SENDER_EMAIL=
SENDER_NAME=
```

Then just run it:
```bash
python main.py
```

---

## APIs used

- **Apollo.io** — company discovery (free tier works)
- **Hunter.io** — email finding (25 searches/month free)
- **Brevo** — email sending (300/day free)

---

## Structure

```
├── main.py          — runs the pipeline start to finish
├── config.py        — loads env vars, validates keys on startup
├── stages/
│   ├── apollo.py    — finds lookalike companies
│   ├── hunter.py    — finds contacts + emails
│   └── brevo.py     — sends the emails
└── utils/
    ├── logger.py    — coloured terminal output
    └── checkpoint.py — the "are you sure?" gate
```

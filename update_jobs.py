#!/usr/bin/env python3
"""
Auto-refresh Nihal's job listings — runs in GitHub Actions (no laptop needed).

What it does each run:
  1. Downloads the two dentalilan.com category pages (clinic coordinator + health tourism).
  2. Strips them to plain text.
  3. Asks the Gemini API (free tier) to EXTRACT the current Istanbul roles and SCORE
     each one against Nihal's CV, returning JSON in the exact jobs.json schema.
  4. Writes uploads/jobs.json.

Safety: if anything fails (site down, blocked, bad AI output), it exits WITHOUT
touching jobs.json, so the live site keeps the last good listings.

Needs one environment variable: GEMINI_API_KEY (set as a GitHub Actions secret).
No third-party packages required — standard library only.
"""

import os
import re
import sys
import json
import datetime
import urllib.request

# ---- Config ---------------------------------------------------------------
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash"  # free-tier model
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "uploads", "jobs.json")

SOURCE_PAGES = [
    "https://dentalilan.com/isveren-ilanlari/klinik-yoneticisi-koordinatoru-araniyor",
    "https://dentalilan.com/isveren-ilanlari/saglik-turizmi-tercumani-araniyor",
]

# Fixed metadata (kept the same every run)
TITLE = "Nihal's Opportunities"
SUBTITLE = ("Real, current openings for patient coordinator, clinic coordinator and "
            "health-tourism roles in Istanbul — pulled from the boards, screened against "
            "Nihal's CV, and shown so she doesn't have to dig.")
SOURCE = "dentalilan.com"
CANDIDATE = {
    "name": "Nihal Kocaman",
    "headline": "International Sales Manager & Clinic Coordinator",
    "experience": "~2.5 years in Istanbul dental tourism (Ekiz Dental, Swedish Clinic, MayClinik)",
    "languages": ["English", "Turkish"],
    "strengths": [
        "international patient management", "English medical interpretation",
        "CRM & reporting", "pricing/sales", "team leadership & recruitment",
        "influencer/celebrity patient relations",
    ],
}

# Candidate context the AI uses to score fit
CV_CONTEXT = """Nihal Kocaman — International Sales Manager & Clinic Coordinator.
~2.5 years in Istanbul DENTAL tourism: Ekiz Dental (Sarıyer, Nov2023-Sep2025, intl sales
consultant / clinic coordinator / interpreter), Swedish Clinic (Mecidiyeköy, intl patient
coordinator / sales team leader), MayClinik (Levent, intl patient coordinator). Earlier:
English teacher 2019-2022. Languages: English (fluent) + Turkish (native). NO Russian/
German/other. Strengths: end-to-end international patient management, English medical
interpretation, CRM & reporting, pricing/sales, team leadership & recruitment, influencer/
celebrity patient relations, marketing/social content. She is a Turkish citizen.
Her past workplaces are on the European side / central (Sarıyer, Şişli, Mecidiyeköy, Levent),
so central/European-side roles are a more convenient commute than far Asian-side or western
districts (Tuzla, Pendik, Sancaktepe, Esenyurt, Başakşehir) — note commute in 'why' but do
not exclude on that basis."""

PROMPT_TEMPLATE = """You are screening Turkish dental job listings for one candidate.

CANDIDATE:
{cv}

Below is the plain text of two dentalilan.com category pages (clinic coordinator/manager,
and health-tourism translator/specialist). Extract every CURRENTLY-LISTED job whose location
is İSTANBUL and whose role is relevant to the candidate: patient coordinator, clinic
coordinator, clinic manager/müdür, health-tourism specialist/coordinator, international
patient coordinator, English-speaking patient/sales coordinator, or health-tourism
sales/translator. IGNORE non-Istanbul roles and irrelevant roles (dentist, assistant,
technician, cleaner, accountant-only, etc.).

For each kept job produce an object with EXACTLY these keys:
- "title": the listing title (keep Turkish if that's how it appears)
- "clinic": clinic/company name if shown, else a short descriptor like "Dental clinic — <district>"
- "district": "<District>, İstanbul"
- "posted": date in YYYY-MM-DD (convert from the DD/MM/YYYY on the page)
- "lang": language requirement if stated (e.g. "English", "Russian + English"), else ""
- "fit": one of "strong" | "good" | "maybe"
- "why": 1-2 sentences, addressed about her, explaining the fit and any tradeoff
         (reference her real CV: dental tourism, coordinator/interpreter, sales/CRM,
         management/recruitment, English; flag if it needs a language she lacks, is a step
         down, or is a far commute).
- "url": the absolute https://dentalilan.com/... link to the listing

Scoring guide:
- "strong": role + seniority + language all align AND ideally central/European-side.
- "good": solid match with one tradeoff (far commute, or general-management vs international).
- "maybe": a stretch — needs a language she lacks (e.g. Russian-priority) or a step down
           (pure interpreter, below her manager/coordinator level).

Return ONLY valid JSON, no markdown, of the form:
{{"jobs": [ {{...}}, {{...}} ]}}
Sort best-fit first (strong, then good, then maybe; within a tier, newest first).
Include at most 12 jobs. If you find none, return {{"jobs": []}}.

PAGE 1 (clinic coordinator / manager):
{page1}

PAGE 2 (health tourism):
{page2}
"""


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        "Accept-Language": "tr,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def strip_html(html):
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def call_gemini(prompt):
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={GEMINI_KEY}")
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.2},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["candidates"][0]["content"]["parts"][0]["text"]


def main():
    if not GEMINI_KEY:
        sys.exit("ERROR: GEMINI_API_KEY is not set.")

    pages = []
    for u in SOURCE_PAGES:
        try:
            pages.append(strip_html(fetch(u))[:18000])
            print(f"fetched {u}")
        except Exception as e:
            print(f"WARN: could not fetch {u}: {e}")
    if not pages:
        sys.exit("ERROR: no pages fetched — keeping existing jobs.json unchanged.")
    while len(pages) < 2:
        pages.append("(page unavailable)")

    today = datetime.date.today().isoformat()
    prompt = PROMPT_TEMPLATE.format(cv=CV_CONTEXT, page1=pages[0], page2=pages[1])

    try:
        raw = call_gemini(prompt)
        parsed = json.loads(raw)
    except Exception as e:
        print("RAW MODEL OUTPUT (for debugging):")
        print(locals().get("raw", "<none>")[:2000])
        sys.exit(f"ERROR: Gemini call/parse failed: {e} — keeping existing jobs.json.")

    joblist = parsed.get("jobs", parsed) if isinstance(parsed, dict) else parsed
    if not isinstance(joblist, list) or not joblist:
        sys.exit("ERROR: no jobs returned — keeping existing jobs.json unchanged.")

    # Light validation: every job needs a title and url
    clean = [j for j in joblist if isinstance(j, dict) and j.get("title") and j.get("url")]
    if not clean:
        sys.exit("ERROR: jobs failed validation — keeping existing jobs.json unchanged.")

    out = {
        "title": TITLE,
        "subtitle": SUBTITLE,
        "candidate": CANDIDATE,
        "snapshot_date": today,
        "source": SOURCE,
        "fit_tiers": ["strong", "good", "maybe"],
        "jobs": clean,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"OK: wrote {len(clean)} jobs to {OUT_PATH} (snapshot {today}).")


if __name__ == "__main__":
    main()

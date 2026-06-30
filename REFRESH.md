# Refresh procedure — Nihal's job listings

This is the canonical procedure for refreshing `uploads/jobs.json`. Both Claude Code (via `~/.claude/skills/refresh-nihal-jobs/`) and Codex (via `AGENTS.md`) read it. Update this file rather than editing either tool-specific wrapper.

The output is always one file: `uploads/jobs.json`. Nothing else changes during a refresh.

---

## 1. Prerequisites

- The user must be at their Mac with **Chrome already open** and signed in to LinkedIn (LinkedIn results vary a lot without a session). Dentalilan also requires real Chrome — every headless fetcher we tried (urllib, Playwright, Patchright with and without `--headless`, GitHub Actions runners) was blocked by Cloudflare. Don't reattempt.
- `gh` CLI authenticated as `pefisu`.
- Repo at `~/code/ripe-jobs/` cloned and on `main`.

If any prereq is missing, stop and ask the user — don't half-refresh.

---

## 2. Sources to check

Four boards. On each, look at the candidate roles listed below; keep only Istanbul listings.

| Board | Where to look |
|------|------|
| **Dentalilan** | Categories `klinik-yoneticisi-koordinatoru-araniyor` and `saglik-turizmi-tercumani-araniyor` (https://dentalilan.com/isveren-ilanlari/...) |
| **LinkedIn** | Jobs search `site:tr.linkedin.com/jobs` — search for: "patient coordinator istanbul", "international patient coordinator istanbul", "uluslararası hasta koordinatörü istanbul", "sağlık turizmi uzmanı istanbul" |
| **Kariyer.net** | Jobs search — keywords: "sağlık turizmi uzmanı", "uluslararası hasta", "klinik koordinatörü", "patient coordinator", filtered to İstanbul |
| **Eleman.net** | Search the same keywords; often returns fewer relevant hits, OK to skip if nothing matches |

Pages from Dentalilan and LinkedIn lazy-load — scroll and re-read the accessibility tree until you have absolute URLs for every kept listing. Never invent or guess URLs; if you can't extract a working absolute href, skip that listing.

---

## 3. Filter — keep / drop

**Keep** (any of these role types):
- Patient coordinator / international patient coordinator / hasta koordinatörü
- Clinic coordinator / clinic manager / klinik müdürü / klinik yöneticisi
- Health-tourism specialist / sağlık turizmi uzmanı / sağlık turizmi yöneticisi
- English-speaking sales / customer success / international patient consultant
- Health-tourism translator/coordinator if English-only is acceptable

**Drop**:
- Dentist, dental assistant, technician, anesthesia, radiology, sterilization, hygiene, cleaning, kitchen, accountant-only roles
- Listings outside İstanbul (Antalya, İzmir, Adana etc. — note that "İstanbul(Asya)" still counts as İstanbul)
- Listings whose primary language requirement is one Nihal doesn't have (Russian, Persian, Polish, German, Bulgarian, Romanian) — these go in "maybe" tier only, not dropped, unless Russian/etc. is explicitly the only option

---

## 4. Candidate context

**Nihal Kocaman** — International Sales Manager & Clinic Coordinator.

- ~2.5 years Istanbul dental tourism: Ekiz Dental (Sarıyer), Swedish Clinic (Mecidiyeköy), MayClinik (Levent).
- **Languages: English (fluent) + Turkish (native). No others** — Russian/Persian/German/Polish/Bulgarian/Romanian roles are at best "maybe".
- Strengths: international patient management, English medical interpretation, CRM & reporting, pricing/sales, team leadership & recruitment, influencer/celebrity patient relations, marketing/social.
- Past workplaces European-side/central. Asian-side / far districts (Tuzla, Pendik, Sancaktepe, Esenyurt, Başakşehir, Kadıköy) are an inconvenient commute — mention in `why` but don't exclude.

---

## 5. Scoring tiers

- **strong** — role + seniority + language all align, ideally central/European-side
- **good** — solid match with one tradeoff (far commute, or general-management vs international focus)
- **maybe** — stretch: needs a language she lacks, or is a step down (pure interpreter, below her coordinator/manager level)

Sort jobs strong → good → maybe; within tier, newest first. Cap at ~12 jobs total.

---

## 6. Voice

The whole site is addressed **directly to Nihal in second person** ("you", "your"), not third person ("she", "her CV"), and not addressed to the owner about her.

This applies to:
- `subtitle`
- Every `why` field

`candidate.name`, `candidate.headline`, `candidate.experience`, `candidate.strengths` are bio facts shown in a sidebar — they stay as-is.

Examples:
- ✅ "Bullseye — literally your job title. You did exactly this at Ekiz Dental…"
- ❌ "Bullseye — literally her job title. She did exactly this at Ekiz Dental…"
- ✅ "Your CV shows operations, team leadership, recruitment and pricing."
- ❌ "Nihal's CV shows operations, team leadership, recruitment and pricing."

---

## 7. Output schema — `uploads/jobs.json`

Top-level fields, preserve exactly:
- `title` — `"Your Opportunities"`
- `subtitle` — second-person, describes what the page is
- `candidate` — Nihal's bio (name, headline, experience, languages, strengths)
- `snapshot_date` — today, `YYYY-MM-DD`
- `source` — comma-separated list of boards actually used this run, e.g. `"LinkedIn, Kariyer.net, Dentalilan, Eleman.net"`
- `fit_tiers` — `["strong", "good", "maybe"]`
- `jobs` — array of job objects (see below)

Each job object:
- `title` — listing title (Turkish if that's the source)
- `clinic` — clinic/company name, or `"Dental clinic — <district>"` if unstated
- `district` — `"<District>, İstanbul"` (or `"İstanbul"` if district unstated)
- `posted` — `YYYY-MM-DD` (convert from `DD/MM/YYYY` on the page)
- `lang` — language requirement (`"English"`, `"Russian + English"`, `"English likely"` if implied, `""` if unstated)
- `mode` — `"Remote"` / `"Hybrid"` / `"On-site"` if stated, else omit the field
- `fit` — `"strong"` / `"good"` / `"maybe"`
- `why` — 1–2 sentences addressed TO Nihal, mentioning the fit + any tradeoff
- `url` — absolute https URL to the listing

---

## 8. Commit + push

```bash
cd ~/code/ripe-jobs && \
  git pull --rebase origin main && \
  git add uploads/jobs.json && \
  git -c user.name="ripe-jobs-refresh" -c user.email="pedro.fds.sousa+ripebot@gmail.com" \
    commit -m "Refresh listings ($(date +%F))" && \
  git push origin main
```

Netlify rebuilds in ~1–2 min and the live site updates at https://ripe-jobs.netlify.app/.

---

## 9. Safety rules

- **Never push if any source returned a Cloudflare challenge or login wall.** Stop and tell the user — do not invent listings.
- **Never invent URLs.** Skip the listing rather than guess.
- **Don't touch `index.html`, `support.js`, or any other file in a refresh.** Only `uploads/jobs.json` may change.
- **Always pull --rebase before pushing**, in case the other tool (Codex if you're Claude, or vice versa) updated the repo in the meantime.

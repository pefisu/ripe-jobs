# Agent guide — ripe-jobs

This repo powers https://ripe-jobs.netlify.app/ — a personalised job-listing site for Nihal Kocaman, showing fit-scored Istanbul dental/medical-tourism roles.

## What the site is

- Built for one person (Nihal); not a multi-tenant board.
- Data is driven entirely by `uploads/jobs.json`. Edit that file → push → Netlify auto-deploys.
- Frontend (`index.html`, `support.js`) is hand-tuned and stable. Don't edit unless explicitly asked.

## The one job you'll be asked to do: refresh the listings

When the user asks to "refresh listings" / "update Nihal's jobs" / similar:

**Follow [`REFRESH.md`](./REFRESH.md) — it's the canonical procedure.**

That doc covers: the 4 source boards to check, filter rules, candidate context, scoring tiers, voice (second-person, addressed to Nihal), the JSON schema, and the git commit/push commands. Don't paraphrase it from memory — read the file each time, the user updates it.

## Why a real browser is required

`dentalilan.com` is behind Cloudflare with an aggressive bot challenge. Headless fetchers (curl, urllib, Playwright, Patchright stealth, GitHub Actions runners) all get 403. The only way through is the user's own signed-in Chrome session. The same is broadly true for LinkedIn (login wall).

If you don't have access to a real browser session for these sources, stop and ask — don't fall back to guessing listings.

## Don't touch

- `update_jobs.py` and `.github/workflows/refresh-listings.yml` — leftovers from the abandoned Cloudflare-blocked automation. Kept for reference; not part of the live flow.
- The frontend (`index.html`, `support.js`) unless the user explicitly asks for design changes.

## Other notes

- Commit author: `ripe-jobs-refresh <pedro.fds.sousa+ripebot@gmail.com>` for automated refreshes.
- Live site: https://ripe-jobs.netlify.app/
- GitHub Actions are intentionally disabled for scheduled runs — don't re-enable.

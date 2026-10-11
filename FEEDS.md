# Data connections

Public company sources are configured in scripts/sync_jobs.py, scripts/workday.py, and scripts/career_sites.py.

| Company | Public career source |
| --- | --- |
| Amgen, Gilead Sciences, Eli Lilly | Workday |
| Genentech / Roche, Merck / MSD, Bristol Myers Squibb | Workday |
| Pfizer, Novartis, Neurocrine Biosciences | Workday |
| Denali Therapeutics | Workday: Discovery, Development, Technical Operations |
| AbbVie | SmartRecruiters |
| BioMarin | Jobvite public job pages |
| Ionis Pharmaceuticals | UKG public board |
| Arrowhead Pharmaceuticals | Greenhouse |
| Vir, Glyphic, Kardigan, Alnylam, Praxis, Tessera, Element, Lila | Greenhouse |
| BioAgilytix, KCAS Bio, Convergent Research | Lever |

Company web endpoints are site-specific and can change or fail. Connection status comes from each actual synchronization result, not from merely configuring a URL. Workday coverage uses mass spectrometry, proteomics, oligonucleotide, analytical, and bioanalytical searches. Other boards retrieve public listings and screen scientific titles and descriptions. This is not a guarantee of every opening or candidate qualification.

Synchronization runs once daily at 15:17 UTC through GitHub Actions and can be started manually in Actions. The interface displays per-source results, last scan, active jobs, and first-seen dates. New means first discovered within 7 days, not necessarily newly posted. Missing jobs are marked closed only after a successful scan; failures and partial detail responses retain existing records as stale. Job IDs and canonical URLs remove duplicate listings.

## Authorized platform feeds

LinkedIn, Indeed, Glassdoor, and Handshake are **not connected** without an explicitly licensed feed. Signing into the consumer website does not supply job retrieval API permission. A partner publishing API is not a job-search API.

This repository accepts a normalized HTTPS JSON feed from an approved integration provider. It does not claim direct native-platform API integration. Repository Actions secrets: `<PLATFORM>_FEED_URL` and optionally `<PLATFORM>_FEED_TOKEN` (Bearer token). Platforms are LINKEDIN, INDEED, GLASSDOOR, HANDSHAKE. Never put credentials in app.js or send them in chat. Feed authorization must permit publishing the provided job fields on this public site.

Required JSON shape:

```json
{"jobs":[{"id":"external-id","title":"Scientist, LC-MS","company":"Example","url":"https://example.com/job/1","description":"Mass spectrometry and RNA characterization","city":"San Francisco","state":"CA","location":"San Francisco, CA","salary":"See listing","temporary":false,"postedAt":null}]}
```

An API response with a different schema requires a provider-specific adapter before it can be connected. No feed URL or credentials have been supplied yet. The UI therefore reports Authorization required for these four platforms.

## GitHub deployment

Choose Settings → Pages → Source → GitHub Actions for this scheduled publishing workflow. It publishes only the static site and public job records. Initial API availability can be confirmed only after the Actions run. Source failures are reported independently; there is no guaranteed job count or comprehensive market coverage.

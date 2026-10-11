# Data connections

Public company sources: 8 Greenhouse boards and 3 Lever boards, configured in scripts/sync_jobs.py. Synchronization runs once daily through GitHub Actions and can be started manually in Actions. The interface displays per-source success/failure, last scan, active jobs, and first-seen dates. New means first discovered within 7 days, not necessarily newly posted. Missing jobs are marked closed only after a successful scan; failures preserve stale records.

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

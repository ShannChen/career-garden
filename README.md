# Career Garden

English job discovery site for mass spectrometry, proteomics, oligonucleotide/RNA analysis, analytical development, bioanalysis, and MS applications.

Website: https://shannchen.github.io/career-garden/

## Live company feeds

The GitHub Actions workflow synchronizes configured public Greenhouse and Lever boards every six hours, deduplicates URLs, preserves first-seen dates, and publishes the updated website. Newly discovered means first seen in the last seven days; it is not necessarily a new posting. Missing roles are marked closed only after a successful scan. Failed sources retain last-known records with a stale marker.

Scientific relevance is automatic keyword screening, not a complete qualification review. The default California filter can show fewer jobs than the total feed. See Search sources for connection results and the last synchronization time.

## Platform authorization

LinkedIn, Indeed, Glassdoor, and Handshake are not connected without a licensed job feed. Search links do not retrieve platform data. The authorized normalized-feed adapter is implemented; the repository owner must provide a licensed endpoint and any token through Actions secrets. See [FEEDS.md](FEEDS.md) for required schema and setup. Consumer logins and job-posting API access are not job-search API authorization.

## Features

Location, scientific focus, career level, source review, temporary-role filters, saved roles, application tracking, and manual job entry. Browser storage is local to each device. No automatic applications or email alerts.

## Local preview

Run `python3 -m http.server 8000` from the repository root. Data is loaded from data/jobs.json; run `python3 scripts/sync_jobs.py` where public API access is available to refresh it.

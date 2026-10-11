# Career Garden

English static website for mass spectrometry, proteomics, oligonucleotide/RNA analysis, analytical development, bioanalysis, and MS applications.

## Publish with GitHub Pages

1. Create a public repository named `career-garden`.
2. Upload the contents of this folder into the repository root: `index.html`, `app.js`, `.nojekyll`, and this README. Do not upload the original CV.
3. Open Settings → Pages → Build and deployment.
4. Set Source to Deploy from a branch, select `main` and `/ (root)`, then Save.
5. Wait for deployment and use the URL shown by GitHub Pages. For ShannChen this normally is https://shannchen.github.io/career-garden/ . This URL is not live until deployment succeeds.

## Features

Location and scientific-focus filters, source-review and career-level filters, saved jobs, application tracking, manual job entry, source search links, mobile layout. Saved data is local to the browser and not shared across devices.

## Data limitations

Four source-backed sample records from the October 10, 2026 review. Posting dates are unknown. Two official descriptions were retrieved; two are search leads requiring verification. No live synchronization, scraping, alerts, or automatic applications are enabled. RNA biology is not represented as direct oligonucleotide LC-MS experience. GitHub Pages hosts the static interface; recurring data ingestion needs a separate approved feed or workflow.

## Local preview

Run `python3 -m http.server 8000` in this folder, then open http://localhost:8000 . No build or dependencies required.

"""Read public company career-search responses; no candidate login is used.

These are site-specific web endpoints, not a guaranteed Workday partner API.
Failures are surfaced rather than bypassing access controls.
"""
import json
import time
import urllib.request
from urllib.parse import urlsplit

SOURCES = [
    ('Amgen', 'amgen.wd1.myworkdayjobs.com', 'amgen', 'Careers'),
    ('Gilead Sciences', 'gilead.wd1.myworkdayjobs.com', 'gilead', 'gileadcareers'),
    ('Eli Lilly', 'lilly.wd115.myworkdayjobs.com', 'lilly', 'LLY'),
    ('Genentech / Roche', 'roche.wd3.myworkdayjobs.com', 'roche', 'ROG-A2O-GENE'),
    ('Merck / MSD', 'msd.wd5.myworkdayjobs.com', 'msd', 'SearchJobs'),
    ('Bristol Myers Squibb', 'bristolmyerssquibb.wd5.myworkdayjobs.com', 'bristolmyerssquibb', 'BMS'),
    ('Pfizer', 'pfizer.wd1.myworkdayjobs.com', 'pfizer', 'PfizerCareers'),
    ('Novartis', 'novartis.wd3.myworkdayjobs.com', 'novartis', 'Novartis_Careers'),
    ('Denali Therapeutics · Discovery', 'dnli.wd1.myworkdayjobs.com', 'dnli', 'Discovery'),
    ('Denali Therapeutics · Development', 'dnli.wd1.myworkdayjobs.com', 'dnli', 'Development'),
    ('Denali Therapeutics · Technical Operations', 'dnli.wd1.myworkdayjobs.com', 'dnli', 'Technical_Operations_Manufacturing'),
    ('Neurocrine Biosciences', 'neurocrine.wd5.myworkdayjobs.com', 'neurocrine', 'Neurocrinecareers'),
]
QUERIES = ['mass spectrometry', 'proteomics', 'oligonucleotide', 'analytical', 'bioanalytical']

def request_json(url, payload=None):
    headers = {'Accept': 'application/json', 'User-Agent': 'CareerGarden/1.0'}
    body = None
    if payload is not None:
        body = json.dumps(payload).encode()
        headers['Content-Type'] = 'application/json'
        headers['Origin'] = 'https://' + urlsplit(url).netloc
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def fetch_workday(source, now, normalize):
    company, host, tenant, board = source
    key = 'workday:' + tenant + (':' + board if tenant == 'dnli' else '')
    base = f'https://{host}/wday/cxs/{tenant}/{board}'
    found, jobs, failures = {}, [], 0
    try:
        for query in QUERIES:
            offset = 0
            while True:
                data = request_json(base + '/jobs', dict(appliedFacets={}, limit=20, offset=offset, searchText=query))
                if not isinstance(data.get('jobPostings'), list) or 'total' not in data:
                    raise ValueError('Unexpected search response')
                rows = data['jobPostings']
                for row in rows:
                    found[row['externalPath']] = row
                offset += len(rows)
                if offset >= int(data['total']):
                    break
                if not rows or offset >= 500:
                    raise ValueError('Incomplete search result; no closure inference')
                time.sleep(0.2)
        for path, listing in found.items():
            # Sales/operational jobs can mention the keyword but are not scientific roles.
            import re
            if not re.search(r'scientist|research associate|chemist|analyst|researcher|research engineer', listing.get('title', ''), re.I):
                continue
            try:
                info = request_json(base + path)['jobPostingInfo']
                location = info.get('location') or listing.get('locationsText') or ''
                url = info.get('externalUrl') or f'https://{host}/en-US/{board}{path}'
                raw = dict(id=info.get('jobReqId') or path, title=info.get('title') or listing['title'],
                           content=info.get('jobDescription', ''), location={'name': location}, absolute_url=url)
                job = normalize(company, 'greenhouse', tenant, raw, now)
                if job:
                    if ' - ' in location:
                        job['city'] = location.split(' - ')[-1].strip()
                    for state_name, abbreviation in [('California','CA'),('Massachusetts','MA'),('Indiana','IN'),('North Carolina','NC'),('New Jersey','NJ'),('Pennsylvania','PA'),('Texas','TX')]:
                        if state_name in location:
                            job['state'] = abbreviation
                    job.update(id=f'{key}:{raw["id"]}', sourceKey=key,
                               sourceLabel='Company careers · Workday',
                               postedAt=None, postedRelative=listing.get('postedOn'))
                    jobs.append(job)
            except Exception:
                failures += 1
            time.sleep(0.2)
        return jobs, dict(key=key, name=company, provider='workday', status='partial' if failures else 'connected',
                          checkedAt=now, scanned=len(found), matched=len(jobs), detailFailures=failures,
                          message='Some job details unavailable; existing records retained' if failures else 'Public career search synchronized')
    except Exception as exc:
        return jobs, dict(key=key, name=company, provider='workday', status='partial' if jobs else 'error',
                          checkedAt=now, matched=len(jobs), message=type(exc).__name__ + ': public careers source unavailable')

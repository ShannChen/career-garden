"""Fetch public ATS boards and explicitly authorized normalized partner feeds."""
import concurrent.futures
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import urllib.request
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ('Vir Biotechnology', 'greenhouse', 'virbiotechnologyinc'),
    ('Glyphic Biotechnologies', 'greenhouse', 'glyphicbiotechnologies'),
    ('Kardigan', 'greenhouse', 'kardigan'),
    ('Alnylam Pharmaceuticals', 'greenhouse', 'alnylampharmaceuticals'),
    ('Praxis Precision Medicines', 'greenhouse', 'praxisprecisionmedicines'),
    ('Tessera Therapeutics', 'greenhouse', 'tesseratherapeutics'),
    ('Element Biosciences', 'greenhouse', 'elementbiosciences'),
    ('Lila Sciences', 'greenhouse', 'lila'),
    ('Arrowhead Pharmaceuticals', 'greenhouse', 'arrowheadpharmacareers'),
    ('BioAgilytix', 'lever', 'bioagilytix'),
    ('KCAS Bio', 'lever', 'kcasbio'),
    ('Convergent Research', 'lever', 'convergentresearch'),
]
PLATFORMS = ['LinkedIn', 'Indeed', 'Glassdoor', 'Handshake']
PATTERNS = {
    'proteomics': r'proteomic|protein characteri|peptide mapping|histone|post.translational',
    'oligo': r'oligonucleotide|\bRNA\b|nucleic acid|antisense|\bsiRNA\b',
    'analytical': r'analytical development|analytical characteri|method development|protein chemistry',
    'bioanalysis': r'bioanalyt|pharmacokinetic|\bDMPK\b',
    'applications': r'application[s]? scientist|field application',
    'assay': r'assay development|reagent characteri|reagent development',
}
MS = r'mass spectrometr|\bLC[ -/]?MS|\bLC[ -/]?MS/MS|Orbitrap|proteomic'

def plain(s):
    return re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', html.unescape(str(s or '')))).strip()

def canonical(url):
    p = urlsplit(url)
    if p.scheme not in ('http', 'https') or not p.netloc:
        raise ValueError('Invalid job URL')
    query = [(k, v) for k, v in parse_qsl(p.query) if not k.startswith('utm_') and k not in ('gh_src', 'source', 'trackingId')]
    return urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip('/'), urlencode(sorted(query)), ''))

def classify(title, text):
    content = title + ' ' + text
    fields = [k for k, pattern in PATTERNS.items() if re.search(pattern, content, re.I)]
    # Keep scientific roles only; oligo/RNA roles need an analytical connection.
    role = re.search(r'scientist|research associate|chemist|analyst|researcher|research engineer|biologist|research specialist|protein engineer', title, re.I)
    related = re.search(MS, content, re.I) or ('oligo' in fields and re.search(r'analytical development|analytical characteri|analytical methods?|analytical chemistry|chromatograph|\b[HU]PLC\b|capillary electrophoresis', content, re.I))
    if not role or not related:
        return None
    if re.search(r'principal|staff|director|senior|\bsr\.?\b', title, re.I):
        level = 'senior'
    elif re.search('associate', title, re.I):
        level = 'associate'
    else:
        level = 'scientist'
    return fields or ['analytical'], level

def normalize(company, provider, board, raw, now):
    title = raw.get('title', '') if provider != 'lever' else raw.get('text', '')
    text = plain(raw.get('content', '') if provider == 'greenhouse' else raw.get('descriptionPlain', '') + ' ' + ' '.join(plain(x.get('content', '')) for x in raw.get('lists', [])))
    found = classify(title, text)
    if not found:
        return None
    fields, level = found
    location = raw.get('location', {}).get('name', '') if provider == 'greenhouse' else raw.get('categories', {}).get('location', '')
    url = canonical(raw.get('absolute_url', '') if provider == 'greenhouse' else raw.get('hostedUrl', ''))
    city = location.split(',')[0].strip()
    state_match = re.search(r'\b(CA|MA|WA|NJ|NY|NC|PA|TX|CO|MO|KS)\b', location)
    state = state_match.group(1) if state_match else ('CA' if 'California' in location else '')
    if not state and re.search(r'\b(South San Francisco|San Francisco|San Diego|Carlsbad|La Jolla|San Rafael|Novato|Foster City|Thousand Oaks|Redwood City|Pasadena|Irvine|San Carlos|Santa Monica|Emeryville|Berkeley|Davis|Sacramento)\b', location, re.I):
        state = 'CA'
    if 'Bay Area' in location and not state:
        state = 'CA'
    tags = [k.upper() if k == 'oligo' else k.title() for k in fields]
    return dict(id=f'{provider}:{board}:{raw["id"]}', company=company, title=title,
                city=city, state=state, location=location, level=level, fields=fields,
                verified=False, apiVerified=True, temp=bool(re.search('temporary|contract', title, re.I)),
                rank=len(fields) + (3 if re.search(MS, title, re.I) else 0),
                salary='See original listing for compensation', tags=tags,
                fit='Keyword overlap: ' + ', '.join(tags) + '. Automated relevance screening; qualifications have not been individually reviewed.',
                gap='Confirm required experience, direct MS methods, work authorization, and job level in the full description. RNA biology does not imply oligonucleotide LC-MS experience.',
                url=url, sourceLabel='Company careers · ' + provider.title(), sourceKey=f'{provider}:{board}',
                firstSeen=now, lastSeen=now, postedAt=None, updatedAt=raw.get('updated_at'), active=True)

def get_json(url, token=None):
    headers = {'User-Agent': 'CareerGarden/1.0', 'Accept': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as res:
        return json.load(res)

def fetch_source(source, now):
    company, provider, board = source
    key = f'{provider}:{board}'
    try:
        url = f'https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true' if provider == 'greenhouse' else f'https://api.lever.co/v0/postings/{board}?mode=json'
        data = get_json(url)
        rows = data['jobs'] if provider == 'greenhouse' else data
        if not isinstance(rows, list):
            raise ValueError('Unexpected feed format')
        jobs = [j for r in rows if (j := normalize(company, provider, board, r, now))]
        return jobs, dict(key=key, name=company, provider=provider, status='connected', checkedAt=now, scanned=len(rows), matched=len(jobs))
    except Exception as exc:
        return [], dict(key=key, name=company, provider=provider, status='error', checkedAt=now, message=type(exc).__name__ + ': source could not be synchronized')

def partner_source(name, now):
    # Only use a licensed feed URL explicitly configured by the repository owner.
    key = 'partner:' + name.lower()
    url = os.getenv(name.upper() + '_FEED_URL')
    if not url:
        return [], dict(key=key, name=name, status='authorization_required', message='No authorized job feed configured')
    try:
        if urlsplit(url).scheme != 'https':
            raise ValueError('Feed must use HTTPS')
        data = get_json(url, os.getenv(name.upper() + '_FEED_TOKEN'))
        rows = data['jobs']
        if not isinstance(rows, list):
            raise ValueError('Expected jobs array')
        jobs = []
        for row in rows:
            title, text = str(row['title']), plain(row.get('description', ''))
            found = classify(title, text)
            if not found:
                continue
            fields, level = found
            url = canonical(row['url'])
            jobs.append(dict(id=key + ':' + str(row['id']), company=str(row['company']), title=title,
                 city=str(row.get('city', '')), state=str(row.get('state', '')), location=str(row.get('location', '')),
                 fields=fields, level=level, verified=False, apiVerified=True, temp=bool(row.get('temporary', False)),
                 rank=len(fields), salary=str(row.get('salary') or 'See original listing'), tags=[name],
                 fit='Authorized feed · automated keyword screening; review full requirements.',
                 gap='Confirm qualifications and current availability on the original listing.', url=url,
                 sourceLabel=name + ' · Authorized feed', sourceKey=key, firstSeen=now,lastSeen=now,postedAt=row.get('postedAt'),active=True))
        return jobs, dict(key=key,name=name,status='connected',checkedAt=now,scanned=len(rows),matched=len(jobs))
    except Exception as exc:
        return [], dict(key=key,name=name,status='error',checkedAt=now,message=type(exc).__name__ + ': authorized feed unavailable')

def merge(old_jobs, batches, now):
    old = {j['id']: j for j in old_jobs}
    out, urls, statuses = {}, set(), []
    for rows, status in batches:
        statuses.append(status)
        if status['status'] in ('connected', 'partial', 'authorization_required'):
            for j in rows:
                prior = old.get(j['id']) or next((x for x in old_jobs if canonical(x['url']) == j['url']), None)
                if prior:
                    j['firstSeen'] = prior['firstSeen']
                if j['url'] not in urls:
                    out[j['id']] = j
                    urls.add(j['url'])
            # Confirm missing only after a successful source scan.
            if status['status'] == 'connected':
                ids = {j['id'] for j in rows}
                for j in old_jobs:
                    if j.get('sourceKey') == status['key'] and j['id'] not in ids:
                        out.setdefault(j['id'], {**j, 'active': False, 'closedAt': j.get('closedAt') or now})
        if status['status'] in ('error', 'partial', 'needs_review'):
            for j in old_jobs:
                if j.get('sourceKey') == status['key'] and j['url'] not in urls:
                    out.setdefault(j['id'], {**j, 'stale': True})
                    urls.add(j['url'])
    return list(out.values()), statuses

def main():
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    path = ROOT / 'data/jobs.json'
    prior = json.loads(path.read_text()) if path.exists() else {'jobs': []}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        batches = list(pool.map(lambda s: fetch_source(s, now), SOURCES))
    from company_registry import load_companies, fetch_company, coverage_directory
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        batches += list(pool.map(lambda c: fetch_company(c,now,get_json,normalize),load_companies()))
    from workday import SOURCES as WORKDAY_SOURCES, fetch_workday
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        batches += list(pool.map(lambda s: fetch_workday(s, now, normalize), WORKDAY_SOURCES))
    from career_sites import smartrecruiters, jobvite, ukg
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        batches += list(pool.map(lambda f: f(now, normalize), [smartrecruiters, jobvite, ukg]))
    batches += [partner_source(n, now) for n in PLATFORMS]
    jobs, statuses = merge(prior.get('jobs', []), batches, now)
    from locations import annotate_location
    jobs=[annotate_location(j) for j in jobs]
    path.parent.mkdir(exist_ok=True)
    coverage=coverage_directory(statuses,jobs,now)
    path.write_text(json.dumps(dict(generatedAt=now, jobs=jobs, sources=statuses, coverage=coverage), ensure_ascii=False, indent=2))
    print(f'Synchronized {sum(s["status"] == "connected" for s in statuses)} sources; {sum(j["active"] for j in jobs)} active relevant roles')

if __name__ == '__main__':
    main()

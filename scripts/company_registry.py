"""Expand curated company coverage with public boards and identity validation.

Candidate board names are not data connections. Unverified boards never publish
jobs; empty verified boards are distinguished from missing or mismatched sources.
"""
import json
import html
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def compact(value):
    return re.sub(r'[^a-z0-9]','',str(value).lower())

def identity_matches(company,value):
    actual=compact(value)
    return any(compact(a) and compact(a) in actual for a in company.get('aliases',[company['name']]))

def board_url(provider,board):
    if provider=='greenhouse':return 'https://job-boards.greenhouse.io/'+board
    if provider=='lever':return 'https://jobs.lever.co/'+board
    if provider=='ashby':return 'https://jobs.ashbyhq.com/'+board
    return ''

def load_companies(prior_sources=None):
    data=json.loads((ROOT/'config/companies.json').read_text())['companies']
    assert len({c['id'] for c in data})==len(data),'Duplicate company IDs'
    prior={s.get('companyId'):s for s in (prior_sources or []) if s.get('identityVerified') and s.get('board')}
    for company in data:
        company['configuredProvider']=company['provider']
        if company['id'] in prior:
            source=prior[company['id']]
            company['provider']=source['provider']
            company['boards']=list(dict.fromkeys([source['board']]+company['boards']))
    return data

def confirm_board_identity(company,evidence,provider,board):
    if identity_matches(company,evidence):return True
    # A public board title can verify a real company even when it has no postings.
    req=urllib.request.Request(board_url(provider,board),headers={'User-Agent':'CareerGarden/1.0'})
    with urllib.request.urlopen(req,timeout=15) as response:page=response.read().decode('utf-8','replace')
    title=re.search(r'<title[^>]*>(.*?)</title>',page,re.S|re.I)
    return bool(title and identity_matches(company,html.unescape(title.group(1))))

def fetch_company(company,now,get_json,normalize,discover=True,started=None):
    started=started or time.monotonic()
    key=company.get('legacyKey') or 'company:'+company['id'];provider=company['provider']
    base=dict(key=key,name=company['name'],companyId=company['id'],provider=provider,checkedAt=now,portfolio=company.get('portfolio',False))
    failures=[]
    for board in company['boards']:
        if time.monotonic()-started>60:break
        try:
            if not re.fullmatch(r'[A-Za-z0-9_-]+',board):raise ValueError('Invalid public board name')
            if provider=='greenhouse':
                metadata=get_json(f'https://boards-api.greenhouse.io/v1/boards/{board}')
                if not identity_matches(company,metadata.get('name','')):raise ValueError('Company identity mismatch')
                data=get_json(f'https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true')
                rows=data['jobs'];label=metadata['name']
            elif provider=='lever':
                rows=get_json(f'https://api.lever.co/v0/postings/{board}?mode=json')
                if not isinstance(rows,list):raise ValueError('Unexpected board schema')
                evidence=' '.join(str(r.get('descriptionPlain','')) for r in rows)
                if not confirm_board_identity(company,evidence,provider,board):raise ValueError('Company identity not confirmed in public postings')
                label=company['name']
            elif provider=='ashby':
                data=get_json(f'https://api.ashbyhq.com/posting-api/job-board/{board}')
                rows=data['jobs']
                evidence=' '.join(str(r.get('descriptionPlain') or r.get('descriptionHtml') or '') for r in rows)
                if not confirm_board_identity(company,evidence,provider,board):raise ValueError('Company identity not confirmed in public postings')
                label=company['name']
            else:raise ValueError('Unsupported public board provider')
            if not isinstance(rows,list):raise ValueError('Unexpected board schema')
            jobs=[]
            for row in rows:
                if provider=='ashby':
                    if row.get('isListed') is False:continue
                    url=row['jobUrl'];job_id=row.get('id') or url.rstrip('/').split('/')[-1]
                    raw=dict(id=job_id,title=row['title'],content=row.get('descriptionHtml') or row.get('descriptionPlain',''),location={'name':row.get('location','')},absolute_url=url)
                    job=normalize(company['name'],'greenhouse',board,raw,now)
                    if job:
                        address=(row.get('address') or {}).get('postalAddress') or {}
                        job.update(postedAt=row.get('publishedAt'),temp=row.get('employmentType') in ('Contract','Temporary'),workplaceType=row.get('workplaceType'))
                        if address.get('addressLocality'):job['city']=address['addressLocality']
                        if address.get('addressRegion'):job['state']=address['addressRegion']
                        country=str(address.get('addressCountry') or '').upper()
                        if country:job['country']='US' if country in ('US','USA','UNITED STATES') else country
                else:
                    job=normalize(company['name'],provider,board,row,now)
                if job:
                    job.update(id=key+':'+str(row.get('id') or job_id),sourceKey=key,sourceLabel=('Portfolio careers' if company.get('portfolio') else 'Company careers')+' · '+provider.title())
                    if company.get('portfolio'):
                        job['gap']='Shared portfolio recruiting board: confirm the hiring company on the original listing. '+job['gap']
                    jobs.append(job)
            return jobs,dict(base,status='connected',identityVerified=True,board=board,sourceUrl=board_url(provider,board),boardName=label,scanned=len(rows),matched=len(jobs),message='Public company identity and job response verified'+(' · shared portfolio board' if company.get('portfolio') else ''))
        except urllib.error.HTTPError as exc:
            failures.append('HTTP '+str(exc.code))
        except Exception as exc:
            failures.append(str(exc) if isinstance(exc,ValueError) else type(exc).__name__)
    if discover:
        # Check public ATS migrations; every response still needs company identity
        # verification. A successful candidate is preferred on the next daily run.
        name=company['name'].split(' (')[0]
        short=re.sub(r'[^a-z0-9]','',name.split()[0].lower())
        case_name=re.sub(r'[^A-Za-z0-9]','',name)
        boards=list(dict.fromkeys(company['boards']+[compact(name),case_name,short,company['id']]))[:6]
        providers=list(dict.fromkeys([company.get('configuredProvider',provider),'greenhouse','lever','ashby']))
        for alternative in providers:
            candidates=[b for b in boards if alternative!=provider or b not in company['boards']]
            if not candidates or time.monotonic()-started>60:continue
            jobs,source=fetch_company({**company,'provider':alternative,'boards':candidates},now,get_json,normalize,False,started)
            if source['status']=='connected':return jobs,source
    return [],dict(base,status='needs_review',identityVerified=False,message='Public recruiting source could not be verified. Existing records retained; no new jobs published.')

def coverage_directory(statuses,jobs,now):
    groups={}
    for source in statuses:
        if source['key'].startswith('partner:'):continue
        name=source['name'].split(' · ')[0]
        company_id=source.get('companyId') or compact(name)
        company=groups.setdefault(company_id,dict(id=company_id,name=name,sources=[],active=0,usActive=0,states=[]))
        company['sources'].append(source)
        matches=[j for j in jobs if j.get('active') and j.get('sourceKey')==source['key']]
        company['active']+=len(matches)
        company['usActive']+=sum(j.get('country')=='US' for j in matches)
        company['states']=sorted(set(company['states'])|{j['state'] for j in matches if j.get('country')=='US' and j.get('state')})
    for company in groups.values():
        states=[s['status'] for s in company['sources']]
        company['status']='connected' if all(s=='connected' for s in states) else 'partial' if any(s in ('connected','partial') for s in states) else 'needs_review'
    companies=sorted(groups.values(),key=lambda c:c['name'].lower())
    return dict(generatedAt=now,scope='Curated US biotech and life-science coverage, including smaller companies and shared portfolio boards. Not every US biotech company is covered.',companies=companies,totalCompanies=len(companies),connectedCompanies=sum(c['status']=='connected' for c in companies),partialCompanies=sum(c['status']=='partial' for c in companies),reviewRequired=sum(c['status']=='needs_review' for c in companies))

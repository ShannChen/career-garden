"""Adapters for public SmartRecruiters and Jobvite company boards."""
import concurrent.futures
from html.parser import HTMLParser
import json
import re
import time
import urllib.request
from urllib.parse import urljoin

SCIENCE_TITLE = re.compile(r'scientist|research associate|chemist|analyst|researcher|research engineer', re.I)

def request(url, payload=None):
    headers = {'User-Agent':'CareerGarden/1.0','Accept':'application/json,text/html'}
    if payload is not None:
        headers['Content-Type']='application/json'
    req=urllib.request.Request(url, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    with urllib.request.urlopen(req,timeout=30) as res:
        return res.read().decode('utf-8','replace')

def status(key,name,provider,now,scanned,jobs,failures):
    return dict(key=key,name=name,provider=provider,checkedAt=now,scanned=scanned,matched=len(jobs),
                status='partial' if failures else 'connected',detailFailures=failures)

def convert(normalize,company,key,provider,title,description,location,url,job_id,now):
    raw=dict(id=job_id,title=title,content=description,location={'name':location},absolute_url=url)
    job=normalize(company,'greenhouse',key,raw,now)
    if job:
        job.update(id=key+':'+str(job_id),sourceKey=key,sourceLabel='Company careers · '+provider)
    return job

def smartrecruiters(now,normalize):
    key,name='smartrecruiters:abbvie','AbbVie'
    try:
        offset,rows=0,[]
        while True:
            data=json.loads(request(f'https://api.smartrecruiters.com/v1/companies/AbbVie/postings?limit=100&offset={offset}'))
            batch=data['content'];rows.extend(batch);offset+=len(batch)
            if offset>=data['totalFound']:break
            if not batch or offset>=10000:raise ValueError('Incomplete listing')
            time.sleep(.2)
        candidates=[r for r in rows if SCIENCE_TITLE.search(r.get('name','')) and r.get('location',{}).get('country','').lower() in ('us','usa','united states')]
        def detail(r):
            try:
                data=json.loads(request(f'https://api.smartrecruiters.com/v1/companies/AbbVie/postings/{r["id"]}'))
                sections=data.get('jobAd',{}).get('sections',{})
                desc=' '.join(s.get('text','') for s in sections.values() if isinstance(s,dict))
                loc=data.get('location',r.get('location',{}));region=loc.get('region','')
                location=', '.join(x for x in [loc.get('city',''),region,loc.get('country','')] if x)
                url=data.get('postingUrl') or f'https://jobs.smartrecruiters.com/AbbVie/{r["id"]}'
                job=convert(normalize,name,key,'SmartRecruiters',data.get('name',r['name']),desc,location,url,r['id'],now)
                if job:job['postedAt']=data.get('releasedDate');job['city']=loc.get('city','')
                time.sleep(.2)
                return job,False
            except Exception:return None,True
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(detail,candidates))
        jobs=[j for j,error in results if j];failures=sum(error for j,error in results)
        return jobs,status(key,name,'smartrecruiters',now,len(rows),jobs,failures)
    except Exception as exc:return [],dict(key=key,name=name,provider='smartrecruiters',status='error',checkedAt=now,message=type(exc).__name__+': public board unavailable')

class JobviteRows(HTMLParser):
    def __init__(self):
        super().__init__();self.rows=[];self.row=None;self.cell=None;self.anchor=None
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='tr':self.row={'cells':[],'links':[]}
        if tag=='td' and self.row is not None:self.cell=[]
        if tag=='a' and self.row is not None:self.anchor=attrs.get('href')
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag=='a' and self.anchor and self.row is not None:self.row['links'].append(self.anchor);self.anchor=None
        if tag=='td' and self.cell is not None and self.row is not None:self.row['cells'].append(' '.join(self.cell).strip());self.cell=None
        if tag=='tr' and self.row is not None:self.rows.append(self.row);self.row=None

def jobvite(now,normalize):
    name,key='BioMarin','jobvite:biomarin';base='https://jobs.jobvite.com/biomarin/jobs'
    try:
        parser=JobviteRows();parser.feed(request(base));rows=[r for r in parser.rows if len(r['cells'])>=2 and r['links']]
        if not rows:raise ValueError('No job table found')
        jobs,failures=[],0
        for row in rows:
            title,location=row['cells'][:2]
            if not SCIENCE_TITLE.search(title):continue
            url=urljoin(base,row['links'][0])
            if not url.startswith('https://jobs.jobvite.com/biomarin/job/'):continue
            try:
                page=request(url);description=page
                for block in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',page,re.S|re.I):
                    obj=json.loads(block)
                    for item in (obj if isinstance(obj,list) else [obj]):
                        if isinstance(item,dict) and item.get('@type')=='JobPosting':description=item.get('description',page)
                job=convert(normalize,name,key,'Jobvite',title,description,location,url,url.split('/job/')[-1],now)
                if job:jobs.append(job)
            except Exception:failures+=1
            time.sleep(.2)
        return jobs,status(key,name,'jobvite',now,len(rows),jobs,failures)
    except Exception as exc:return [],dict(key=key,name=name,provider='jobvite',status='error',checkedAt=now,message=type(exc).__name__+': public board unavailable')

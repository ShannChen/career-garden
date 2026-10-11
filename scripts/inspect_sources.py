"""Inspect only public career-page structure to configure source adapters."""
import json
import re
import urllib.request
from urllib.parse import urljoin

PAGES = {
 'ionis': 'https://recruiting.ultipro.com/ISI1000ISIS/JobBoard/14a66400-68fa-4847-8593-af776328cfd2/',
 'denali': 'https://www.denalitherapeutics.com/careers/',
 'biomarin': 'https://jobs.jobvite.com/biomarin/jobs',
}
def text(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CareerGarden/1.0'}),timeout=30) as r:
  return r.read().decode('utf-8','replace')
for name,url in PAGES.items():
 try:
  page=text(url)
  scripts=[urljoin(url,x) for x in re.findall(r'<script[^>]+src=["\']([^"\']+)',page,re.I)]
  print(json.dumps({'source':name,'scripts':scripts,'links':re.findall(r'(?:href|src)=["\']([^"\']*(?:greenhouse|ashbyhq|lever|jobvite|Opportunity|JobBoard|career|position|opening)[^"\']*)',page,re.I)[:20]}))
  print(json.dumps({'source':name,'page_snippets':[page[max(0,m.start()-900):m.end()+900] for m in list(re.finditer(r'loadUrl:|pageSize:|currentQuery:|greenhouse|ashbyhq|open.positions|data-url',page,re.I))[:12]]}))
  if name in ('ionis','denali'):
   for script in scripts:
    if not ('ultipro.com' in script or 'denalitherapeutics.com' in script):continue
    js=text(script)
    snippets=[]
    for m in re.finditer(r'opportunityQuery=new|opportunityQuery=|Candidate.OpportunityQuery|OpportunityQuery=function',js,re.I):
     snippets.append(js[max(0,m.start()-400):m.end()+1800])
     if len(snippets)>=35:break
    if snippets:print(json.dumps({'script':script,'snippets':snippets}))
 except Exception as e:print(json.dumps({'source':name,'error':type(e).__name__}))

try:
 url=PAGES['ionis']+'JobBoardView/LoadSearchResults'
 payload={'opportunitySearch':{'Top':50,'Skip':0,'QueryString':'','OrderBy':[{'PropertyName':'PostedDate','Ascending':False}],'Filters':[]}}
 req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','User-Agent':'CareerGarden/1.0'})
 with urllib.request.urlopen(req,timeout=30) as res: data=json.load(res)
 print(json.dumps({'ionis_response_keys':list(data),'totalCount':data.get('totalCount'),'sample':data.get('opportunities',[])[:1]}))
except Exception as e:print(json.dumps({'ionis_request_error':str(e)}))

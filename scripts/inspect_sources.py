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
  print(json.dumps({'source':name,'page_snippets':[page[max(0,m.start()-100):m.end()+700] for m in list(re.finditer(r'loadSearchResultsUrl|LoadSearchResults|searchOpportunitiesUrl|new US.JobBoard|greenhouse|ashbyhq|open.positions|iframe',page,re.I))[:12]]}))
  if name in ('ionis','denali'):
   for script in scripts:
    if not ('ultipro.com' in script or 'denalitherapeutics.com' in script):continue
    js=text(script)
    snippets=[]
    for m in re.finditer(r'LoadSearchResults|loadSearchResultsUrl|JobBoardView|greenhouse|ashbyhq|jobs\\.|career\\.|open.positions',js,re.I):
     snippets.append(js[max(0,m.start()-200):m.end()+600])
     if len(snippets)>=35:break
    if snippets:print(json.dumps({'script':script,'snippets':snippets}))
 except Exception as e:print(json.dumps({'source':name,'error':type(e).__name__}))

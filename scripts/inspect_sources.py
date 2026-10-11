"""Validate public Ionis descriptions without candidate login."""
import json,re
from career_sites import request,visible_text,SCIENCE_TITLE
base='https://recruiting.ultipro.com/ISI1000ISIS/JobBoard/14a66400-68fa-4847-8593-af776328cfd2/'
payload={'opportunitySearch':{'Top':50,'Skip':0,'QueryString':'','OrderBy':[{'PropertyName':'PostedDate','Ascending':False}],'Filters':[]}}
data=json.loads(request(base+'JobBoardView/LoadSearchResults',payload))
for row in data['opportunities']:
 if not SCIENCE_TITLE.search(row['Title']):continue
 page=request(base+'OpportunityDetail?opportunityId='+row['Id'])
 text=visible_text(page)
 print(json.dumps({'title':row['Title'],'visibleLength':len(text),'titleVisible':row['Title'] in text,'msInPage':bool(re.search('mass spectrometr|LC-MS',page,re.I)),'msVisible':bool(re.search('mass spectrometr|LC-MS',text,re.I)),'snippets':[page[max(0,m.start()-100):m.end()+500] for m in list(re.finditer('LongDescription|mass spectrometr|LC-MS',page,re.I))[:3]]}))

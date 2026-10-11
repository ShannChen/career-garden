"""Offline integrity checks for national company coverage."""
from company_registry import fetch_company, coverage_directory
from locations import annotate_location
from sync_jobs import normalize, merge, classify

def run():
    assert classify('Scientist, RNA Biology','RNA biology and strong analytical thinking') is None
    assert classify('Scientist, Oligonucleotide Analysis','RNA characterization using HPLC')
    company=dict(id='example',name='Example Bio',aliases=['Example Bio'],provider='greenhouse',boards=['wrong','right'])
    def fixture(url):
        if '/wrong' in url:return dict(name='Unrelated Inc')
        if url.endswith('/jobs?content=true'):
            return dict(jobs=[dict(id=1,title='Scientist, Proteomics',content='LC-MS',location=dict(name='Boston, MA'),absolute_url='https://job-boards.greenhouse.io/right/jobs/1')])
        return dict(name='Example Bio')
    jobs,source=fetch_company(company,'now',fixture,normalize)
    assert source['board']=='right' and source['status']=='connected' and len(jobs)==1
    empty,status=fetch_company({**company,'boards':['wrong']},'now',fixture,normalize)
    assert not empty and status['status']=='needs_review' and not status['identityVerified']
    retained,_=merge(jobs,[(empty,status)],'later')
    assert retained[0]['active'] and retained[0]['stale']
    directory=coverage_directory([source],[annotate_location(j) for j in jobs],'now')
    assert directory['connectedCompanies']==1 and directory['companies'][0]['usActive']==1
    def empty_board(url):return {'jobs':[]} if '/jobs?' in url else {'name':'Example Bio'}
    _,zero=fetch_company({**company,'boards':['right']},'now',empty_board,normalize)
    assert zero['status']=='connected' and zero['matched']==0 and zero['identityVerified']
    for loc,country,states in [('Cambridge, MA','US',['MA']),('Cambridge, United Kingdom','GB',[]),('Vancouver, Canada','CA',[]),('Washington, DC','US',['DC']),('Unknown','UNKNOWN',[])]:
        result=annotate_location({'location':loc})
        assert result['country']==country and result['states']==states,loc
    multi=annotate_location({'location':'New York, New York; Salt Lake City, Utah'})
    assert set(multi['states'])=={'NY','UT'}
    ashby=dict(id='ashby',name='Example Bio',aliases=['Example Bio'],provider='ashby',boards=['example'])
    data={'jobs':[dict(title='Scientist, LC-MS',descriptionPlain='Example Bio uses LC-MS for RNA',location='Boston, MA',isListed=True,jobUrl='https://jobs.ashbyhq.com/example/id',address={'postalAddress':{'addressLocality':'Boston','addressRegion':'Massachusetts','addressCountry':'USA'}},employmentType='Contract',publishedAt='2026-10-10'),dict(title='Scientist, Proteomics',descriptionPlain='Example Bio LC-MS',location='Boston',isListed=False,jobUrl='https://jobs.ashbyhq.com/example/unlisted')]}
    rows,status=fetch_company(ashby,'now',lambda url:data,normalize)
    assert len(rows)==1 and rows[0]['temp'] and rows[0]['postedAt']=='2026-10-10'
    assert annotate_location(rows[0])['state']=='MA'
    print('National coverage integrity checks passed')

if __name__=='__main__':run()

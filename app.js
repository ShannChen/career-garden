const $=id=>document.getElementById(id),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function safeURL(s){try{const u=new URL(s);return ['http:','https:'].includes(u.protocol)?u.href:'#'}catch{return '#'}}
const statuses=['Not applied','Preparing','Applied','Interviewing','Offer','Closed'];
let tab='discover',state={saved:[],status:{},custom:[]};
try{const x=JSON.parse(localStorage.getItem('career-garden-v2'));if(x&&Array.isArray(x.saved)&&Array.isArray(x.custom)&&x.status&&typeof x.status==='object')state=x}catch{}
function toast(s){$('toast').textContent=s;$('toast').style.display='block';clearTimeout(window.toastTimer);window.toastTimer=setTimeout(()=>$('toast').style.display='none',2500)}
function persist(){try{localStorage.setItem('career-garden-v2',JSON.stringify(state))}catch{toast('Storage unavailable. Changes remain in this session.')}}
let liveJobs = [], feedInfo = null, coverageQuery = '', coverageStatus = 'all';
const companyName=j=>String(j.company||'').split(' · ')[0];
function jobs(){return [...liveJobs.filter(j => j.active !== false), ...state.custom]}
function filtered(){const q=$('q').value.trim().toLowerCase(),r=$('region').value,f=$('focus').value,l=$('level').value,v=$('review').value,c=$('companyFilter').value;return jobs().filter(j=>{
const bay=['San Francisco','South San Francisco','Berkeley','Emeryville','Foster City','Redwood City','San Mateo','San Carlos','Brisbane','Millbrae','Hayward','Menlo Park','Mountain View','San Leandro','Oakland','Palo Alto','San Jose'].includes(j.city);
return (!q||[j.title,j.company,j.city,j.fit,j.gap,...j.tags].join(' ').toLowerCase().includes(q))&&locationMatches(j,r,bay)&&(c==='all'||companyName(j)===c)&&(f==='all'||j.fields.includes(f))&&(l==='all'||j.level===l)&&(v==='all'||(v==='verified'&&(j.verified||j.apiVerified))||(v==='pending'&&!j.verified&&!j.apiVerified&&!j.manual)||(v==='manual'&&j.manual))&&(!$('exclude').checked||!j.temp)&&(tab!=='saved'||state.saved.includes(j.id))&&(tab!=='tracking'||(state.status[j.id]&&state.status[j.id]!=='Not applied'))
}).sort((a,b)=>$('sort').value==='company'?a.company.localeCompare(b.company):b.rank-a.rank)}
function locationMatches(j,region,bay){
 const states=j.states||[j.state],us=j.country==='US'||(!j.country&&states.some(s=>US_STATES.includes(s)));
 if(region==='global')return true;
 if(!us)return false;
 if(region==='all')return true;
 if(region==='ca')return states.includes('CA');
 if(region==='bay')return states.includes('CA')&&bay;
 if(region==='sf')return states.includes('CA')&&j.city==='San Francisco';
 if(region==='south')return states.includes('CA')&&['Thousand Oaks','San Diego','Carlsbad','La Jolla','Los Angeles','Irvine','Riverside','Pasadena','Santa Monica'].includes(j.city);
 const metro={boston:['MA'],nynj:['NY','NJ'],triangle:['NC'],seattle:['WA'],dmv:['MD','DC','VA'],utah:['UT']}[region];
 return metro?metro.some(s=>states.includes(s)):region.startsWith('state:')&&states.includes(region.slice(6));
}
const US_STATE_NAMES={AL:'Alabama',AK:'Alaska',AZ:'Arizona',AR:'Arkansas',CA:'California',CO:'Colorado',CT:'Connecticut',DE:'Delaware',DC:'District of Columbia',FL:'Florida',GA:'Georgia',HI:'Hawaii',ID:'Idaho',IL:'Illinois',IN:'Indiana',IA:'Iowa',KS:'Kansas',KY:'Kentucky',LA:'Louisiana',ME:'Maine',MD:'Maryland',MA:'Massachusetts',MI:'Michigan',MN:'Minnesota',MS:'Mississippi',MO:'Missouri',MT:'Montana',NE:'Nebraska',NV:'Nevada',NH:'New Hampshire',NJ:'New Jersey',NM:'New Mexico',NY:'New York',NC:'North Carolina',ND:'North Dakota',OH:'Ohio',OK:'Oklahoma',OR:'Oregon',PA:'Pennsylvania',RI:'Rhode Island',SC:'South Carolina',SD:'South Dakota',TN:'Tennessee',TX:'Texas',UT:'Utah',VT:'Vermont',VA:'Virginia',WA:'Washington',WV:'West Virginia',WI:'Wisconsin',WY:'Wyoming'};
const US_STATES=Object.keys(US_STATE_NAMES);
for(const [code,name] of Object.entries(US_STATE_NAMES).sort((a,b)=>a[1].localeCompare(b[1])))$('region').add(new Option(name,'state:'+code));
function companyDirectory(){
 const coverage=feedInfo?.coverage;
 if(!coverage)return '<div class="empty"><h2>Company coverage</h2><p>The nationwide company directory will appear after the next successful synchronization.</p></div>';
 const companies=coverage.companies.filter(c=>(!coverageQuery||c.name.toLowerCase().includes(coverageQuery.toLowerCase()))&&(coverageStatus==='all'||c.status===coverageStatus));
 const label={connected:'Connected',partial:'Partial coverage',needs_review:'Source needs review'};
 const rows=companies.map(c=>'<tr><td><strong>'+esc(c.name)+'</strong><br><button data-company="'+esc(c.name)+'">View US roles</button></td><td>'+esc(label[c.status]||c.status)+'<br><small>'+esc(c.sources.map(s=>s.provider).join(' / '))+'</small></td><td>'+c.usActive+'<br><small>'+esc(c.states.join(', ')||'No matching US roles')+'</small>'+(c.active>c.usActive?'<br><small>'+ (c.active-c.usActive)+' other / unconfirmed locations</small><br><button data-company-all="'+esc(c.name)+'">View all locations</button>':'')+'</td><td>'+c.sources.map(s=>'<div>'+(s.sourceUrl?'<a href="'+esc(safeURL(s.sourceUrl))+'" target="_blank" rel="noopener noreferrer">Public career board ↗</a><br>':'')+'<small>'+esc(s.message||'Last scan: '+(s.checkedAt?new Date(s.checkedAt).toLocaleString():'pending'))+'</small></div>').join('')+'</td></tr>').join('');
 return '<div class="coverage-panel"><h2>Company coverage across the United States</h2><p>'+coverage.totalCompanies+' companies and portfolio boards tracked · '+coverage.connectedCompanies+' connected · '+coverage.partialCompanies+' partially connected · '+coverage.reviewRequired+' need source review.</p><p class="muted">'+esc(coverage.scope)+' A verified source with zero matches is different from an unconnected source. Counts show matching jobs with a confirmed or inferred US location. Shared portfolio boards can include several employers; check the hiring company in each listing.</p><div class="coverage-controls"><input id="coverageSearch" type="search" placeholder="Find a company…" aria-label="Find a covered company" value="'+esc(coverageQuery)+'"><select id="coverageStatus" aria-label="Company connection status"><option value="all">All connection states</option><option value="connected">Connected</option><option value="partial">Partial coverage</option><option value="needs_review">Source needs review</option></select></div><table class="coverage-table"><thead><tr><th>Company / portfolio board</th><th>Connection</th><th>US matching roles</th><th>Source details</th></tr></thead><tbody>'+ (rows||'<tr><td colspan="4">No companies match this directory search.</td></tr>')+'</tbody></table></div>';
}
function populateCompanyFilter(){
 const prior=$('companyFilter').value;
 const names=[...new Set([...(feedInfo?.coverage?.companies||[]).map(c=>c.name),...jobs().map(companyName)])].sort((a,b)=>a.localeCompare(b));
 $('companyFilter').innerHTML='<option value="all">All tracked companies</option>'+names.map(n=>'<option value="'+esc(n)+'">'+esc(n)+'</option>').join('');
 if(names.includes(prior))$('companyFilter').value=prior;
}
function jobSource(j){
  if (j.sourceLabel) return j.sourceLabel;
  if (!j.manual && ['vir','glyphic'].includes(j.id)) return 'Company careers · Greenhouse';
  if (!j.manual && ['amgen','merck'].includes(j.id)) return 'Company careers · Workday';
  try {
    const host = new URL(safeURL(j.url)).hostname.toLowerCase();
    const on = domain => host === domain || host.endsWith('.' + domain);
    if (on('linkedin.com')) return 'LinkedIn';
    if (on('indeed.com')) return 'Indeed';
    if (on('glassdoor.com')) return 'Glassdoor';
    if (on('joinhandshake.com')) return 'Handshake';
    if (on('greenhouse.io')) return 'Greenhouse job board';
    if (on('myworkdayjobs.com')) return 'Workday job board';
    if (on('jobs.lever.co')) return 'Lever job board';
    return host ? 'Website · ' + host : 'Source unavailable';
  } catch { return 'Source unavailable'; }
}
function card(j){const saved=state.saved.includes(j.id);return `<article class="card">${j.firstSeen && !j.stale && Date.now()-Date.parse(j.firstSeen)<7*86400000 ? '<span class="tag">Newly discovered · 7 days</span>' : ''}${j.country==='UNKNOWN'?'<span class="tag">Location country not confirmed</span>':''}${j.stale ? '<span class="tag">Source unavailable · Last known record</span>' : ''}<div class="top"><strong>${esc(j.company)}</strong><button class="save" data-save="${esc(j.id)}" aria-label="${saved?'Unsave':'Save'} ${esc(j.title)}" aria-pressed="${saved}">${saved?'♥':'♡'}</button></div><div><span class="tag">Source: ${esc(jobSource(j))}</span></div><small>${j.manual?'Manual entry · Not verified':j.apiVerified?'Retrieved from API · Requirements not reviewed':j.verified?'Official description reviewed':'Search lead · Verification needed'}</small><h2>${esc(j.title)}</h2><small>⌖ ${esc(j.location || [j.city,j.state].filter(Boolean).join(', '))} ${j.temp?'· Temporary':''}</small><strong>${esc(j.salary)}</strong><div>${j.tags.map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div><div class="fit"><strong>🌱 Why explore it</strong><br>${esc(j.fit)}</div><div class="gap"><strong>Check before applying</strong><br>${esc(j.gap)}</div><small>${j.manual?'Added: '+esc(j.added):j.firstSeen ? 'First discovered: '+esc(new Date(j.firstSeen).toLocaleDateString())+' · Posting date '+(j.postedAt?esc(j.postedAt):'unknown') : 'Sample record · Posting date unknown'}</small><div class="foot"><select data-status="${esc(j.id)}" aria-label="Application status for ${esc(j.title)}">${statuses.map(s=>`<option ${s===(state.status[j.id]||'Not applied')?'selected':''}>${s}</option>`).join('')}</select><a href="${esc(safeURL(j.url))}" target="_blank" rel="noopener noreferrer">Original listing ↗</a></div></article>`}
function sources(){const terms=$('q').value.trim()||{all:'"mass spectrometry" OR proteomics OR "oligonucleotide analysis" OR "RNA characterization"',proteomics:'proteomics "mass spectrometry"',oligo:'oligonucleotide RNA "mass spectrometry"',analytical:'"analytical development" "LC-MS"',bioanalysis:'bioanalytical "LC-MS"',applications:'"applications scientist" "mass spectrometry"',assay:'"reagent characterization" proteins oligonucleotides'}[$('focus').value],loc={all:'United States',global:'All locations',ca:'California',bay:'San Francisco Bay Area',sf:'San Francisco, CA',south:'Southern California',boston:'Boston, Massachusetts',nynj:'New York / New Jersey',triangle:'Research Triangle, North Carolina',seattle:'Seattle, Washington',dmv:'Maryland / DC / Virginia',utah:'Utah'}[$('region').value]||US_STATE_NAMES[$('region').value.slice(6)]||'United States',q=encodeURIComponent(terms),l=encodeURIComponent(loc);
const rows=[['LinkedIn','Search terms and region are included. No automated feed.',`https://www.linkedin.com/jobs/search/?keywords=${q}&location=${l}`],['Indeed','Search terms and region are included. API integration requires appropriate partner access.',`https://www.indeed.com/jobs?q=${q}&l=${l}`],['Glassdoor','Enter the search terms on the platform.','https://www.glassdoor.com/Job/index.htm'],['Handshake','Sign in with your account and search.','https://app.joinhandshake.com/'],['Genentech','Company careers entry point; enter your scientific keywords.','https://careers.gene.com/us/en'],['Greenhouse','Public Job Board API documentation; see company coverage for connected boards.','https://docs.greenhouse.io/job-board.html']];
return connectionPanel() + `<div class="empty"><h2>Your search, beyond proteomics</h2><strong>${esc(terms)}</strong><p>${esc(loc)}</p></div>`+rows.map(([name,note,url])=>`<article class="source"><h2>${name}</h2><p class="muted">${note}</p><a href="${esc(url)}" target="_blank" rel="noopener noreferrer">Explore source ↗</a></article>`).join('')}
function render(){$('savedCount').textContent=state.saved.length;document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));$('sort').style.display=['sources','companies'].includes(tab)?'none':'';if(tab==='companies'){$('count').textContent='Explore company coverage';$('content').innerHTML=companyDirectory();if($('coverageStatus'))$('coverageStatus').value=coverageStatus;return}if(tab==='sources'){$('count').textContent='Follow the sources';$('content').innerHTML=sources();return}const list=filtered();$('count').textContent=`${list.length} ${tab==='saved'?'saved':tab==='tracking'?'tracked':'relevant'} opportunities`;$('content').innerHTML=list.length?list.map(card).join(''):'<div class="empty"><h2>Room for new possibilities</h2><p>No synchronized roles match these filters. Check company coverage or explore the source sites.</p><button id="explore" class="primary">Search this field ↗</button></div>'}
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{tab=b.dataset.tab;render()});
for(const id of ['q','region','companyFilter','focus','level','review','exclude','sort'])$(id).addEventListener(id==='q'?'input':'change',render);
$('reset').onclick=()=>{$('q').value='';$('region').value='all';$('companyFilter').value='all';for(const id of ['focus','level','review'])$(id).value='all';$('exclude').checked=false;render()};
$('content').oninput=e=>{if(e.target.id==='coverageSearch'){const pos=e.target.selectionStart;coverageQuery=e.target.value;render();const input=$('coverageSearch');input.focus();input.setSelectionRange(pos,pos)}};
$('content').onclick=e=>{const companyButton=e.target.closest('[data-company],[data-company-all]');if(companyButton){$('companyFilter').value=companyButton.dataset.company||companyButton.dataset.companyAll;$('region').value=companyButton.dataset.companyAll?'global':'all';$('q').value='';for(const id of ['focus','level','review'])$(id).value='all';$('exclude').checked=false;tab='discover';render();return}const b=e.target.closest('[data-save]');if(b){const id=b.dataset.save;state.saved=state.saved.includes(id)?state.saved.filter(s=>s!==id):[...state.saved,id];persist();render()}if(e.target.id==='explore'){tab='sources';render()}};
$('content').onchange=e=>{if(e.target.id==='coverageStatus'){coverageStatus=e.target.value;render();return}if(e.target.dataset.status){state.status[e.target.dataset.status]=e.target.value;persist();render();toast('Application status updated.')}};
$('skills').innerHTML=['Orbitrap · nanoLC','LC-MS/MS','TMT · LFQ · PRM','Protein interactions · PTM','RNA biology','Skyline · MaxQuant'].map(t=>`<span class="tag">${t}</span>`).join('');
$('newFocus').innerHTML=Array.from($('focus').options).filter(o=>o.value!=='all').map(o=>`<option value="${o.value}">${o.textContent}</option>`).join('');
$('add').onclick=()=>{$('error').textContent='';$('dialog').showModal()};$('cancel').onclick=()=>$('dialog').close();
$('form').onsubmit=e=>{e.preventDefault();const data=new FormData(e.target),url=safeURL(data.get('url'));if(url==='#'){$('error').textContent='Use a valid http or https URL.';return}if(jobs().some(j=>safeURL(j.url)===url)){$('error').textContent='This link is already in your garden.';return}state.custom.push({id:'manual-'+Date.now(),company:data.get('company').trim(),title:data.get('title').trim(),city:data.get('city').trim(),state:data.get('state'),level:data.get('level'),fields:[data.get('focus')],manual:true,verified:false,temp:data.has('temp'),rank:0,salary:'Compensation to verify',tags:['Manual entry'],fit:data.get('note').trim()||'CV-to-role review not completed.',gap:'Check direct MS requirements, education, industry experience, and current availability.',url,added:new Date().toLocaleDateString('en-CA',{timeZone:'America/Los_Angeles'})});persist();$('dialog').close();e.target.reset();populateCompanyFilter();tab='discover';$('q').value='';$('region').value='all';$('companyFilter').value='all';for(const id of ['focus','level','review'])$(id).value='all';$('exclude').checked=false;render();toast('Opportunity added.')};
render();

function connectionPanel(){
 const rows=feedInfo?.sources || ['LinkedIn','Indeed','Glassdoor','Handshake'].map(name=>({name,status:'authorization_required'}));
 return '<div class="empty" style="text-align:left"><h2>Data connections</h2><p class="muted">Company career sources synchronize once daily when the scheduled GitHub workflow is enabled. Search links below are separate from data connections.</p>'+rows.map(s=>'<div style="padding:7px 0;border-bottom:1px solid #dfe3d8"><strong>'+esc(s.name)+'</strong> · '+esc({connected:'Connected',error:'Sync failed',partial:'Partially synchronized',authorization_required:'Authorization required',needs_review:'Source needs review'}[s.status]||'Pending')+(['connected','partial'].includes(s.status)?' · '+s.matched+' matched roles':'')+(s.checkedAt?' · Last checked '+esc(new Date(s.checkedAt).toLocaleString()):'')+(s.message?'<p class="muted" style="margin:3px 0">'+esc(s.message)+'</p>':'')+'</div>').join('')+'<p class="muted">Platform feeds require a licensed endpoint and credentials configured privately in GitHub Actions. No native platform job-search API is connected.</p></div>';
}
async function loadFeed(){
 const note=document.querySelector('.notice');
 note.textContent='Loading synchronized company jobs…';
 try{
  const res=await fetch('./data/jobs.json?t='+Date.now(),{cache:'no-store'});
  if(!res.ok) throw new Error('Feed unavailable');
  const data=await res.json();
  if(!Array.isArray(data.jobs)||!Array.isArray(data.sources))throw new Error('Invalid feed');
  feedInfo=data;liveJobs=data.jobs;populateCompanyFilter();
  const connected=data.sources.filter(s=>s.status==='connected').length;
  const failed=data.sources.filter(s=>['error','partial','needs_review'].includes(s.status)).length;
  const active=liveJobs.filter(j=>j.active!==false).length;
  note.textContent='Last synchronization: '+(data.generatedAt?new Date(data.generatedAt).toLocaleString():'Pending first run')+' · '+connected+' sources connected · '+active+' active relevant roles'+(failed?' · '+failed+' sources need review':'')+(data.coverage?' · '+data.coverage.totalCompanies+' companies / portfolio boards tracked':'')+'. Coverage is curated; not every US biotech is included. New means first discovered in the last 7 days, not the posting date. Platform authorization status is shown in Search sources.';
  render();
 }catch(e){
  note.textContent='Synchronized feed is not available yet. Check the GitHub Actions run. No sample jobs are presented as live results. Manual entries and source searches remain available.';
  render();
 }
}
loadFeed();

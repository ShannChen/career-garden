const seeds=[
{id:'vir',company:'Vir Biotechnology',title:'Scientist I, Analytical Development — Protein Chemistry',city:'San Francisco',state:'CA',level:'scientist',fields:['analytical','proteomics','oligo'],verified:true,temp:true,rank:3,salary:'$56–70 / hour',tags:['Protein & oligonucleotide characterization','Mass spectrometry'],fit:'PhD with 0+ years is listed. Protein MS and troubleshooting overlap with the CV. Oligonucleotide MS experience is a plus.',gap:'Temporary role. Direct oligonucleotide MS, CE-SDS, iCIEF, and CMC experience are not documented in the CV. The listing states visa sponsorship is unavailable.',url:'https://job-boards.greenhouse.io/virbiotechnologyinc/jobs/4734252005'},
{id:'amgen',company:'Amgen',title:'Associate Scientist, Discovery Proteomics',city:'Thousand Oaks',state:'CA',level:'associate',fields:['proteomics'],verified:false,temp:false,rank:4,salary:'Compensation to verify',tags:['TMT','DDA / PRM','LC-MS'],fit:'The search excerpt mentions TMT, label-free DDA, and PRM, aligning with documented skills.',gap:'Full official description was not retrieved. Confirm location, education, experience, compensation, and current availability. DIA is not documented in the CV.',url:'https://amgen.wd1.myworkdayjobs.com/en-US/Careers/job/Associate-Scientist-Discovery-Proteomics_R-252288'},
{id:'merck',company:'Merck / MSD',title:'Scientist, Pharmacokinetics',city:'South San Francisco',state:'CA',level:'scientist',fields:['proteomics','bioanalysis'],verified:false,temp:false,rank:2,salary:'Compensation to verify',tags:['Peptide characterization','Proteomics','Immunogenicity'],fit:'The search excerpt mentions proteomics preparation and peptide characterization. An adjacent MS-based analysis lead.',gap:'Full official description was not retrieved. Verify DMPK / immunogenicity requirements and career-level fit.',url:'https://msd.wd5.myworkdayjobs.com/en-US/SearchJobs/job/Scientist--Pharmacokinetics_R410968-1'},
{id:'glyphic',company:'Glyphic Biotechnologies',title:'Scientist / Senior Scientist, Assay Integration (Reagents)',city:'Berkeley',state:'CA',level:'senior',fields:['assay','oligo','analytical'],verified:true,temp:false,rank:1,salary:'$111,725–161,900 / year',tags:['Oligos & proteins','Reagent characterization','QC'],fit:'Protein biochemistry and RNA biology provide transferable context. This is an exploratory reagent role, not a dedicated MS position.',gap:'Scientist II requires 2+ years of relevant industry experience with a PhD; Senior requires 4+. Reagent stability and QC lot release are not demonstrated in the CV.',url:'https://job-boards.greenhouse.io/glyphicbiotechnologies/jobs/4258096009'}
];
const $=id=>document.getElementById(id),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function safeURL(s){try{const u=new URL(s);return ['http:','https:'].includes(u.protocol)?u.href:'#'}catch{return '#'}}
const statuses=['Not applied','Preparing','Applied','Interviewing','Offer','Closed'];
let tab='discover',state={saved:[],status:{},custom:[]};
try{const x=JSON.parse(localStorage.getItem('career-garden-v2'));if(x&&Array.isArray(x.saved)&&Array.isArray(x.custom)&&x.status&&typeof x.status==='object')state=x}catch{}
function toast(s){$('toast').textContent=s;$('toast').style.display='block';clearTimeout(window.toastTimer);window.toastTimer=setTimeout(()=>$('toast').style.display='none',2500)}
function persist(){try{localStorage.setItem('career-garden-v2',JSON.stringify(state))}catch{toast('Storage unavailable. Changes remain in this session.')}}
let liveJobs = [], feedInfo = null;
function jobs(){return [...liveJobs.filter(j => j.active !== false), ...state.custom]}
function filtered(){const q=$('q').value.trim().toLowerCase(),r=$('region').value,f=$('focus').value,l=$('level').value,v=$('review').value;return jobs().filter(j=>{
const bay=['San Francisco','South San Francisco','Berkeley','Emeryville','Foster City','Redwood City','San Mateo','Oakland','Palo Alto','San Jose'].includes(j.city);
return (!q||[j.title,j.company,j.city,j.fit,j.gap,...j.tags].join(' ').toLowerCase().includes(q))&&(r==='all'||(r==='ca'&&j.state==='CA')||(r==='bay'&&j.state==='CA'&&bay)||(r==='sf'&&j.state==='CA'&&j.city==='San Francisco')||(r==='south'&&j.state==='CA'&&['Thousand Oaks','San Diego','Los Angeles','Irvine','Riverside'].includes(j.city)))&&(f==='all'||j.fields.includes(f))&&(l==='all'||j.level===l)&&(v==='all'||(v==='verified'&&(j.verified||j.apiVerified))||(v==='pending'&&!j.verified&&!j.apiVerified&&!j.manual)||(v==='manual'&&j.manual))&&(!$('exclude').checked||!j.temp)&&(tab!=='saved'||state.saved.includes(j.id))&&(tab!=='tracking'||(state.status[j.id]&&state.status[j.id]!=='Not applied'))
}).sort((a,b)=>$('sort').value==='company'?a.company.localeCompare(b.company):b.rank-a.rank)}
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
function card(j){const saved=state.saved.includes(j.id);return `<article class="card">${j.firstSeen && !j.stale && Date.now()-Date.parse(j.firstSeen)<7*86400000 ? '<span class="tag">Newly discovered · 7 days</span>' : ''}${j.stale ? '<span class="tag">Source unavailable · Last known record</span>' : ''}<div class="top"><strong>${esc(j.company)}</strong><button class="save" data-save="${esc(j.id)}" aria-label="${saved?'Unsave':'Save'} ${esc(j.title)}" aria-pressed="${saved}">${saved?'♥':'♡'}</button></div><div><span class="tag">Source: ${esc(jobSource(j))}</span></div><small>${j.manual?'Manual entry · Not verified':j.apiVerified?'Retrieved from API · Requirements not reviewed':j.verified?'Official description reviewed':'Search lead · Verification needed'}</small><h2>${esc(j.title)}</h2><small>⌖ ${esc(j.location || [j.city,j.state].filter(Boolean).join(', '))}} ${j.temp?'· Temporary':''}</small><strong>${esc(j.salary)}</strong><div>${j.tags.map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div><div class="fit"><strong>🌱 Why explore it</strong><br>${esc(j.fit)}</div><div class="gap"><strong>Check before applying</strong><br>${esc(j.gap)}</div><small>${j.manual?'Added: '+esc(j.added):j.firstSeen ? 'First discovered: '+esc(new Date(j.firstSeen).toLocaleDateString())+' · Posting date '+(j.postedAt?esc(j.postedAt):'unknown') : 'Sample record · Posting date unknown'}</small><div class="foot"><select data-status="${esc(j.id)}" aria-label="Application status for ${esc(j.title)}">${statuses.map(s=>`<option ${s===(state.status[j.id]||'Not applied')?'selected':''}>${s}</option>`).join('')}</select><a href="${esc(safeURL(j.url))}" target="_blank" rel="noopener noreferrer">Original listing ↗</a></div></article>`}
function sources(){const terms=$('q').value.trim()||{all:'"mass spectrometry" OR proteomics OR "oligonucleotide analysis" OR "RNA characterization"',proteomics:'proteomics "mass spectrometry"',oligo:'oligonucleotide RNA "mass spectrometry"',analytical:'"analytical development" "LC-MS"',bioanalysis:'bioanalytical "LC-MS"',applications:'"applications scientist" "mass spectrometry"',assay:'"reagent characterization" proteins oligonucleotides'}[$('focus').value],loc={all:'United States',ca:'California',bay:'San Francisco Bay Area',sf:'San Francisco, CA',south:'Southern California'}[$('region').value],q=encodeURIComponent(terms),l=encodeURIComponent(loc);
const rows=[['LinkedIn','Search terms and region are included. No automated feed.',`https://www.linkedin.com/jobs/search/?keywords=${q}&location=${l}`],['Indeed','Search terms and region are included. API integration requires appropriate partner access.',`https://www.indeed.com/jobs?q=${q}&l=${l}`],['Glassdoor','Enter the search terms on the platform.','https://www.glassdoor.com/Job/index.htm'],['Handshake','Sign in with your account and search.','https://app.joinhandshake.com/'],['Genentech','Company careers entry point; enter your scientific keywords.','https://careers.gene.com/us/en'],['Greenhouse','Public Job Board API documentation for a future feed.','https://docs.greenhouse.io/job-board.html']];
return connectionPanel() + `<div class="empty"><h2>Your search, beyond proteomics</h2><strong>${esc(terms)}</strong><p>${esc(loc)}</p></div>`+rows.map(([name,note,url])=>`<article class="source"><h2>${name}</h2><p class="muted">${note}</p><a href="${esc(url)}" target="_blank" rel="noopener noreferrer">Explore source ↗</a></article>`).join('')}
function render(){$('savedCount').textContent=state.saved.length;document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));$('sort').style.display=tab==='sources'?'none':'';if(tab==='sources'){$('count').textContent='Follow the sources';$('content').innerHTML=sources();return}const list=filtered();$('count').textContent=`${list.length} ${tab==='saved'?'saved':tab==='tracking'?'tracked':'relevant'} opportunities`;$('content').innerHTML=list.length?list.map(card).join(''):'<div class="empty"><h2>Room for new possibilities</h2><p>No sample roles match. Search this field on the source sites.</p><button id="explore" class="primary">Search this field ↗</button></div>'}
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{tab=b.dataset.tab;render()});
for(const id of ['q','region','focus','level','review','exclude','sort'])$(id).addEventListener(id==='q'?'input':'change',render);
$('reset').onclick=()=>{$('q').value='';$('region').value='ca';for(const id of ['focus','level','review'])$(id).value='all';$('exclude').checked=false;render()};
$('content').onclick=e=>{const b=e.target.closest('[data-save]');if(b){const id=b.dataset.save;state.saved=state.saved.includes(id)?state.saved.filter(s=>s!==id):[...state.saved,id];persist();render()}if(e.target.id==='explore'){tab='sources';render()}};
$('content').onchange=e=>{if(e.target.dataset.status){state.status[e.target.dataset.status]=e.target.value;persist();render();toast('Application status updated.')}};
$('skills').innerHTML=['Orbitrap · nanoLC','LC-MS/MS','TMT · LFQ · PRM','Protein interactions · PTM','RNA biology','Skyline · MaxQuant'].map(t=>`<span class="tag">${t}</span>`).join('');
$('newFocus').innerHTML=Array.from($('focus').options).filter(o=>o.value!=='all').map(o=>`<option value="${o.value}">${o.textContent}</option>`).join('');
$('add').onclick=()=>{$('error').textContent='';$('dialog').showModal()};$('cancel').onclick=()=>$('dialog').close();
$('form').onsubmit=e=>{e.preventDefault();const data=new FormData(e.target),url=safeURL(data.get('url'));if(url==='#'){$('error').textContent='Use a valid http or https URL.';return}if(jobs().some(j=>safeURL(j.url)===url)){$('error').textContent='This link is already in your garden.';return}state.custom.push({id:'manual-'+Date.now(),company:data.get('company').trim(),title:data.get('title').trim(),city:data.get('city').trim(),state:data.get('state'),level:data.get('level'),fields:[data.get('focus')],manual:true,verified:false,temp:data.has('temp'),rank:0,salary:'Compensation to verify',tags:['Manual entry'],fit:data.get('note').trim()||'CV-to-role review not completed.',gap:'Check direct MS requirements, education, industry experience, and current availability.',url,added:new Date().toLocaleDateString('en-CA',{timeZone:'America/Los_Angeles'})});persist();$('dialog').close();e.target.reset();tab='discover';$('q').value='';$('region').value='all';for(const id of ['focus','level','review'])$(id).value='all';$('exclude').checked=false;render();toast('Opportunity added.')};
render();

function connectionPanel(){
 const rows=feedInfo?.sources || ['LinkedIn','Indeed','Glassdoor','Handshake'].map(name=>({name,status:'authorization_required'}));
 return '<div class="empty" style="text-align:left"><h2>Data connections</h2><p class="muted">Company APIs synchronize once daily when the scheduled GitHub workflow is enabled. Search links below are separate from data connections.</p>'+rows.map(s=>'<div style="padding:7px 0;border-bottom:1px solid #dfe3d8"><strong>'+esc(s.name)+'</strong> · '+esc({connected:'Connected',error:'Sync failed',authorization_required:'Authorization required'}[s.status]||'Pending')+(s.status==='connected'?' · '+s.matched+' matched roles':'')+'</div>').join('')+'<p class="muted">Platform feeds require a licensed endpoint and credentials configured privately in GitHub Actions. No native platform job-search API is connected.</p></div>';
}
async function loadFeed(){
 const note=document.querySelector('.notice');
 note.textContent='Loading synchronized company jobs…';
 try{
  const res=await fetch('./data/jobs.json?t='+Date.now(),{cache:'no-store'});
  if(!res.ok) throw new Error('Feed unavailable');
  const data=await res.json();
  if(!Array.isArray(data.jobs)||!Array.isArray(data.sources))throw new Error('Invalid feed');
  feedInfo=data;liveJobs=data.jobs;
  const connected=data.sources.filter(s=>s.status==='connected').length;
  const failed=data.sources.filter(s=>s.status==='error').length;
  const active=liveJobs.filter(j=>j.active!==false).length;
  note.textContent='Last synchronization: '+(data.generatedAt?new Date(data.generatedAt).toLocaleString():'Pending first run')+' · '+connected+' sources connected · '+active+' active relevant roles'+(failed?' · '+failed+' sources failed':'')+'. New means first discovered in the last 7 days, not the posting date. Platform authorization status is shown in Search sources.';
  render();
 }catch(e){
  note.textContent='Synchronized feed is not available yet. Check the GitHub Actions run. No sample jobs are presented as live results. Manual entries and source searches remain available.';
  render();
 }
}
loadFeed();

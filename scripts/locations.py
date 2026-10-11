"""Normalize US location filters without treating all global jobs as US jobs."""
import re

STATES=dict(x.split(':') for x in '''Alabama:AL|Alaska:AK|Arizona:AZ|Arkansas:AR|California:CA|Colorado:CO|Connecticut:CT|Delaware:DE|District of Columbia:DC|Florida:FL|Georgia:GA|Hawaii:HI|Idaho:ID|Illinois:IL|Indiana:IN|Iowa:IA|Kansas:KS|Kentucky:KY|Louisiana:LA|Maine:ME|Maryland:MD|Massachusetts:MA|Michigan:MI|Minnesota:MN|Mississippi:MS|Missouri:MO|Montana:MT|Nebraska:NE|Nevada:NV|New Hampshire:NH|New Jersey:NJ|New Mexico:NM|New York:NY|North Carolina:NC|North Dakota:ND|Ohio:OH|Oklahoma:OK|Oregon:OR|Pennsylvania:PA|Rhode Island:RI|South Carolina:SC|South Dakota:SD|Tennessee:TN|Texas:TX|Utah:UT|Vermont:VT|Virginia:VA|Washington:WA|West Virginia:WV|Wisconsin:WI|Wyoming:WY'''.split('|'))
CITIES={
 'CA':['South San Francisco','San Francisco','San Diego','Carlsbad','La Jolla','San Rafael','Novato','Foster City','Thousand Oaks','Redwood City','Pasadena','Irvine','San Carlos','Santa Monica','Emeryville','Berkeley','Davis','Sacramento','Millbrae','Hayward','San Mateo','Palo Alto','Menlo Park','Brisbane','Los Angeles','San Jose','Oakland','Mountain View','San Leandro'],
 'MA':['Boston','Cambridge','Somerville','Watertown','Waltham','Lexington','Worcester','Billerica','Burlington','Norwood','Marlborough','Framingham'],
 'WA':['Seattle','Bellevue','Redmond'],
 'NC':['Durham','Raleigh','Research Triangle Park'],
 'MD':['Rockville','Bethesda','Gaithersburg','Frederick'],
 'UT':['Salt Lake City'], 'CO':['Boulder','Denver'],
 'PA':['Philadelphia'], 'NY':['New York City','New York','Tarrytown','Rensselaer','Sleepy Hollow'],
 'NJ':['Jersey City','Princeton','Rahway','East Hanover'], 'TX':['Austin','Houston'],
 'IN':['Indianapolis'], 'IL':['Chicago'], 'MO':['Kansas City'],
}
FOREIGN={'GB':r'United Kingdom|\bUK\b|England|London|Oxford|Cambridge,\s*UK',
         'CA':r'Canada|Vancouver|Toronto|Montreal|British Columbia',
         'CH':r'Switzerland|Basel|Zurich','DE':r'Germany|Munich|Berlin',
         'FR':r'France|Paris','IN':r'\bIndia\b|Bangalore|Bengaluru|Hyderabad',
         'CN':r'China|Shanghai|Beijing','SG':r'Singapore','JP':r'Japan|Tokyo'}

def annotate_location(job):
    location=str(job.get('location') or job.get('city') or '')
    country=job.get('country')
    # Explicit country and complete state names outrank ambiguous short tokens.
    explicit_us=bool(re.search(r'United States|\bUS(?:A)?\b|\bU\.S\.',location,re.I))
    foreign=[code for code,pattern in FOREIGN.items() if re.search(pattern,location,re.I)]
    full_states=[abbr for name,abbr in STATES.items() if re.search(r'\b'+re.escape(name)+r'\b',location,re.I)]
    if re.search(r'Washington,?\s+DC',location):full_states=[s for s in full_states if s!='WA']
    if not country:
        country='US' if explicit_us or full_states else (foreign[0] if foreign else None)
    state=job.get('state','')
    state=STATES.get(state,state)
    if country not in (None,'US'):
        job.update(country=country,states=[],state='')
        return job
    codes=list(dict.fromkeys(full_states))
    if not foreign or explicit_us or full_states:
        # Require uppercase state abbreviations; 'in', 'or' are ordinary words.
        codes+=re.findall(r'\b('+ '|'.join(sorted(set(STATES.values()))) +r')\b',location)
        if state in STATES.values():codes.append(state)
        for abbr,cities in CITIES.items():
            if any(re.search(r'\b'+re.escape(city)+r'\b',location,re.I) for city in cities):codes.append(abbr)
    codes=list(dict.fromkeys(codes))
    if codes and not country:country='US'
    job['country']=country or 'UNKNOWN'
    job['states']=codes if country=='US' else []
    job['state']=codes[0] if codes else ''
    # Workday often uses "United States - California - City".
    if ' - ' in location:job['city']=location.split(' - ')[-1].strip()
    return job

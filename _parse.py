#!/usr/bin/env python3
"""Reproducible canonical transcription from a single official BWB XML state."""
from pathlib import Path
import json,re,hashlib,shutil
from lxml import etree as E
P=Path(__file__).resolve().parent
raw=P/'sources/intake-version.xml'
r=E.parse(str(raw)); assert r.getroot().tag=='toestand'
W=r.find('.//wettekst')
def txt(e): return re.sub(r'\s+',' ',''.join(e.itertext())).strip()
def blocks(e):
 out=[]
 for c in e:
  if c.tag in ('meta-data','kop'):continue
  if c.tag=='lid':
   b=blocks(c);n=c.findtext('lidnr');out+=([n+' '+b[0]]+b[1:] if b else [])
  elif c.tag=='lidnr':continue
  elif c.tag=='lijst':
   for li in c:
    n=li.findtext('li.nr') or '';b=blocks(li);out+=([n+' '+b[0]]+b[1:] if b else [n])
  elif c.tag=='li.nr':continue
  elif c.tag in ('al','tabel'):out.append(txt(c))
  else:raise ValueError('Unaccounted block '+c.tag)
 return out
arts=W.findall('.//artikel');units=[]; canon=['# Auteurswet — officiële tekst, toestand 2026-01-01_0','']
chapters=[(1,'basis','Werk, maker en exploitatiehandelingen'),(2,'beperkingen-1','Pers, lenen en toegankelijkheid'),(3,'beperkingen-2','Onderwijs, kopiëren en bewaren'),(4,'beperkingen-3','Overige beperkingen en persoonlijkheidsrechten'),(5,'contracten','Exploitatieovereenkomsten'),(6,'handhaving','Civiele handhaving en technische bescherming'),(7,'strafrecht','Toezicht en strafrecht'),(8,'duur-volgrecht','Beschermingsduur en volgrecht'),(9,'licenties-film','Verruimde licenties en filmwerken'),(10,'software','Computerprogramma’s en nagelaten werken'),(11,'slot','Overgangs- en slotbepalingen')]
starts={'15':2,'16':3,'17':4,'25b':5,'26':6,'30':7,'37':8,'44':9,'45h':10,'46':11};ch=1
for a in arts:
 n=a.findtext('kop/nr');ch=starts.get(n,ch)
 structure=[' '.join(txt(x.find('kop')).split()) for x in reversed(list(a.iterancestors())) if x.tag in ('hoofdstuk','paragraaf')]
 notes=[txt(x) for x in a.findall('./meta-data/brondata/opmerkingen-inhoud/al')]
 u=dict(id='art-'+n,label='Artikel '+n,title='',chapter=ch,structure=structure,text='\n\n'.join(blocks(a)),notes=notes,official_path=a.get('bwb-ng-variabel-deel'),status=a.get('status'),effective_from=a.get('inwerking'))
 assert u['text'];units.append(u);canon+=['## '+u['label'],u['text'],'']
(P/'sources/canonical.md').write_text('\n\n'.join(canon))
(P/'units.jsonl').write_text(''.join(json.dumps(u,ensure_ascii=False)+'\n' for u in units))
meta=dict(cc='nl',lang='nl',repo=P.name,repo_dir='/Volumes/LaCie/open-commentary/nl/'+P.name,title='Commentaar op de Auteurswet',source_path=str(P/'sources/canonical.md'),intro_file='00-inleiding.md',intro_desc='Reikwijdte, methode en leeswijzer',labels=dict(text='Wettekst',chapter='Commentaarhoofdstuk',notes='Officiële redactionele aantekening'),chapters=[dict(n=n,slug=s,title=t) for n,s,t in chapters],decisive_date='2026-10-19',official_state='2026-01-01_0')
(P/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
# Independently enumerate official attributes, rather than using the units array.
expected=['art-'+a.get('label').removeprefix('Artikel ') for a in E.parse(str(raw)).xpath('//wettekst//artikel')]
parsed=[u['id'] for u in units]
annex=dict(official_bijlage_elements=len(r.findall('.//bijlage')),disposition='Geen bijlage-elementen of andere operationele bijlagen in deze officiële toestand. Aanhef en wetsluiting bewaard in raw XML, niet als artikel genummerd; alle overgangs- en slotartikelen opgenomen.',unhandled_children=[x.tag for x in W if x.tag not in ('hoofdstuk','artikel','meta-data')])
coverage=dict(official_source=dict(url='https://repository.officiele-overheidspublicaties.nl/bwb/BWBR0001886/2026-01-01_0/xml/BWBR0001886_2026-01-01_0.xml',local_raw_evidence_path='sources/intake-version.xml',sha256=hashlib.sha256(raw.read_bytes()).hexdigest()),expected_ids=expected,parsed_ids=parsed,annex_disposition=annex)
(P/'coverage-evidence.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))
report=dict(expected_count=len(expected),parsed_count=len(parsed),missing=sorted(set(expected)-set(parsed)),extra=sorted(set(parsed)-set(expected)),duplicates=[x for x in set(parsed) if parsed.count(x)>1],repealed=[u['id'] for u in units if u['status']=='vervallen'],annex_disposition=annex,source_sha256=coverage['official_source']['sha256'],paragraphs=sum(len(u['text'].split('\n\n')) for u in units),footnotes=len(r.findall('.//noot')),official_editorial_notes=sum(len(u['notes']) for u in units))
assert not report['missing'] and not report['extra'] and not report['duplicates'] and not annex['unhandled_children']
(P/'completeness-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
# Preserve intake unmodified and document substantive equality independent of layout.
src=Path('/Volumes/LaCie/law-intake/eu/nl/bwb/bwb-bwbr0001886.md');shutil.copyfile(src,P/'sources/original-intake.md')
old={m.group(1):m.group(2).strip() for m in re.finditer(r'^#### Artikel (\S+)\n(.*?)(?=^###|\Z)',src.read_text(),re.M|re.S)}
def norm(s):return re.sub(r'\s+','',s).replace('**','').replace('_','')
change=[dict(id=u['id'],intake_present=u['label'][8:] in old,text_equal_ignoring_whitespace=norm(u['text'])==norm(old.get(u['label'][8:],''))) for u in units]
(P/'sources/change-map.json').write_text(json.dumps(dict(intake_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),canonical_xml_sha256=report['source_sha256'],units=change),indent=2))

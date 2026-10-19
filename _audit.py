#!/usr/bin/env python3
"""Independent coverage and local-book checks; does not alter shared validator."""
from pathlib import Path
from lxml import etree as E
import json,re,hashlib,collections,unicodedata
P=Path(__file__).resolve().parent
units=[json.loads(x) for x in (P/'units.jsonl').read_text().splitlines() if x.strip()]
raw=P/'sources/intake-version.xml';r=E.parse(str(raw));arts=r.xpath('//wettekst//artikel')
def norm(t):return re.sub(r'\s+','',unicodedata.normalize('NFKC',t))
checks=[]
for a in arts:
 id='art-'+a.get('label').removeprefix('Artikel ');u=next(x for x in units if x['id']==id)
 b=E.fromstring(E.tostring(a))
 for e in list(b.xpath('.//meta-data'))+list(b.xpath('./kop')):
  e.getparent().remove(e)
 tokens=norm(''.join(b.itertext()));actual=norm(u['text'])
 checks.append(dict(id=id,full_normative_text_equal=tokens==actual,lids=len(b.findall('.//lid')),list_items=len(b.findall('.//li')),status=u['status']))
expected=['art-'+a.get('label').split(' ',1)[1] for a in arts];parsed=[x['id'] for x in units]
com={};duplicates=[]
for f in sorted((P/'commentary').glob('*.md')):
 for m in re.finditer(r'^=== (\S+)\n(.*?)(?=^=== |\Z)',f.read_text(),re.M|re.S):
  if m[1] in com:duplicates.append(m[1])
  com[m[1]]=m[2].strip()
paragraphs=collections.defaultdict(list)
for id,t in com.items():
 for p in t.split('\n\n'):
  if len(p)>160:paragraphs[norm(p)].append(id)
repeated=[ids for ids in paragraphs.values() if len(ids)>1]
wrong_refs=[]
for id,t in com.items():
 for n in re.findall(r'\bartikel (\d+[a-z]*)\b',t,re.I):
  if 'art-'+n not in expected and n!='95':wrong_refs.append(dict(unit=id,reference=n))
# Only local links from authored book-level files; raw captures may contain fragment conventions of source sites.
repo=Path(json.loads((P/'meta.json').read_text())['repo_dir']);broken=[];tested=0
if repo.exists():
 for f in list(repo.glob('*.md'))+list((repo/'cases').glob('*.md')):
  for target in re.findall(r'\]\(([^)]+)\)',f.read_text()):
   if re.match(r'(https?://|mailto:|#)',target):continue
   tested+=1;target=target.split('#')[0]
   if target and not (f.parent/target).exists():broken.append(dict(file=f.name,target=target))
report=dict(source_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),expected_count=len(expected),parsed_count=len(parsed),missing=sorted(set(expected)-set(parsed)),extra=sorted(set(parsed)-set(expected)),duplicate_identifiers=[x for x in set(parsed) if parsed.count(x)>1],normative_text_checks=checks,normative_text_all_equal=all(x['full_normative_text_equal'] for x in checks),official_lids=sum(x['lids'] for x in checks),official_list_items=sum(x['list_items'] for x in checks),repealed=[x['id'] for x in units if x['status']=='vervallen'],official_editorial_notes=sum(len(x.get('notes',[])) for x in units),annex_disposition=dict(bijlage_count=len(r.findall('.//bijlage')),explanation='No annex elements or other unhandled operative units in official wettekst; preamble and signature remain in raw XML. All final/transitional article slots included.'),commented_units=len(com),missing_commentary=sorted(set(expected)-set(com)),extra_commentary=sorted(set(com)-set(expected)),duplicate_commentary=duplicates,commentary_chars=sum(len(x) for x in com.values()),repeated_substantive_paragraphs=repeated,unresolved_internal_references=wrong_refs,local_links_checked=tested,broken_local_links=broken)
report['ok']=not any([report['missing'],report['extra'],report['duplicate_identifiers'],not report['normative_text_all_equal'],report['missing_commentary'],report['extra_commentary'],duplicates,repeated,wrong_refs,broken])
(P/'completeness-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='normative_text_checks'},ensure_ascii=False));assert report['ok']

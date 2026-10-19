"""Additional fresh-official-source and review-ledger checks; shared validator unchanged."""
from pathlib import Path
from lxml import etree as E,html
import json,re,hashlib,unicodedata,itertools,copy
P=Path(__file__).resolve().parent
units=[json.loads(l) for l in (P/'units.jsonl').read_text().splitlines()]
xml=P/'sources/review-state.xml';r=E.parse(str(xml));w=r.find('.//wettekst')
expected=['art-'+a.get('label').split(' ',1)[1] for a in w.findall('.//artikel')]
parsed=[x['id'] for x in units];cov=json.loads((P/'coverage-evidence.json').read_text());progress=json.loads((P/'review-progress.json').read_text())
assert expected==cov['expected_ids']==cov['parsed_ids']==parsed==progress['reviewed_ids'];assert len(set(expected))==170
assert xml.read_bytes()==(P/'sources/intake-version.xml').read_bytes()
hp=P/'sources/review-links-wetten.html';h=html.parse(str(hp));ha=h.xpath('//div[@class="artikel"]');html_ids=['art-'+x.get('id').rsplit('_Artikel',1)[1] for x in ha];assert html_ids==expected
body=' '.join(h.xpath('//body//text()'));assert 'Geldend van 01-01-2026 t/m heden.' in body
# Compare full rendered article text, excluding action menus. Repealed markers are independently checked with their dates.
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s))
html_checks=[]
for u,a in zip(units,ha):
 a=copy.deepcopy(a);header=a.find('div');assert 'article__header--law' in header.get('class','')
 if u['status']=='vervallen':
  marker=' '.join(header.xpath('./p//text()'));date='-'.join(u['effective_from'].split('-')[::-1]);equal='[Vervallen per '+date+']' in marker
  html_checks.append(dict(id=u['id'],repeal_marker_matches=equal));assert equal,u['id']
 else:
  a.remove(header);text=''.join(a.itertext());equal=norm(text)==norm(u['text'])
  html_checks.append(dict(id=u['id'],full_text_equal_ignoring_whitespace=equal))
  assert equal,(u['id'],norm(text)[:200],norm(u['text'])[:200])
com={m[1]:m[2].strip() for f in sorted((P/'commentary').glob('*.md')) for m in re.finditer(r'^=== (\S+)\n(.*?)(?=^=== |\Z)',f.read_text(),re.M|re.S)}
assert set(com)==set(expected)
sh={k:set(tuple(re.findall(r'\w+',v.lower())[i:i+5]) for i in range(max(0,len(re.findall(r'\w+',v))-4))) for k,v in com.items()}
pairs=sorted([dict(left=a,right=b,shared_5word_ratio=round(2*len(sh[a]&sh[b])/(len(sh[a])+len(sh[b])),3)) for a,b in itertools.combinations(com,2)],key=lambda x:x['shared_5word_ratio'],reverse=True)[:15]
checks=dict(official_xml_sha256=hashlib.sha256(xml.read_bytes()).hexdigest(),official_html=dict(path='sources/review-links-wetten.html',sha256=hashlib.sha256(hp.read_bytes()).hexdigest(),version_statement='Geldend van 01-01-2026 t/m heden.',expected_ids=html_ids,unit_checks=html_checks),expected_ids_from_fresh_official_labels=expected,coverage_contract_matches=True,units_match=True,reviewed_count=len(progress['reviewed_ids']),reviewed_ids=progress['reviewed_ids'],statutory_source_unchanged=True,official_chapters=len(w.findall('.//hoofdstuk')),official_paragraphs=len(w.findall('.//paragraaf')),official_lids=len(w.findall('.//lid')),official_list_items=len(w.findall('.//li')),official_notes=len(w.findall('.//opmerkingen-inhoud')),official_footnotes=len(w.findall('.//noot')),annex_elements=len(w.findall('.//bijlage')),all_body_tags=sorted({x.tag for x in w.iter()}),commentary_hashes={k:hashlib.sha256(v.encode()).hexdigest() for k,v in com.items()},similarity_method='Dice overlap of distinct five-word sequences; supplementary editorial screen, not a legal-quality test',most_similar_pairs=pairs,manual_similarity_assessment='Highest overlaps concern distinct penalty/opgave provisions (35c/35d, 0.109), repeated transitional citations and some repealed slots. All were read against their distinct statutory functions; no identical substantive stock paragraphs retained.')
(P/'second-pass-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print(json.dumps(dict(reviewed=len(expected),fresh_html_ids=len(html_ids),full_html_text_matches=sum('full_text_equal_ignoring_whitespace' in x for x in html_checks),repealed_markers_checked=sum('repeal_marker_matches' in x for x in html_checks),highest_5word_overlap=pairs[0]),ensure_ascii=False))

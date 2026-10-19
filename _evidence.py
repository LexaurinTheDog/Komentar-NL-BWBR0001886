#!/usr/bin/env python3
from pathlib import Path
import json,datetime,hashlib
from lxml import etree as E
P=Path(__file__).resolve().parent;s=P/'sources'
records=json.loads((s/'verification-attempts.json').read_text())+json.loads((s/'authority-fetches.json').read_text())
for x in records:
 b=(P/x['path']).read_bytes()
 assert hashlib.sha256(b).hexdigest()==x['sha256']
 if x['http_status']==200 and x['path'].endswith('.xml'):
  root=E.fromstring(b);x['format_validation']={'accepted':True,'root_element':root.tag,'is_xml':True}
 elif x['path']=='sources/official-index.html':
  root=E.fromstring(b);x['format_validation']={'accepted':root.tag=='work','root_element':root.tag,'is_xml':True};x['canonical_evidence_copy']='sources/official-manifest.xml'
 else:x['format_validation']={'accepted':False,'reason':'Non-success response, empty body, or error HTML; not used as statutory/case text.'}
fc=s/'cjeu-aci-adam.json';j=json.loads(fc.read_text());assert 'C‑435/12' in j['markdown'] and '| 66 |' in j['markdown'] and 'Het Hof' in j['markdown'];assert '<' in j['html']
window=json.loads((s/'aci-fetch-window.json').read_text());assert window['exit_code']==0
records.append(dict(url=j['metadata']['sourceURL'],path='sources/cjeu-aci-adam.json',accessed_at=window['completed_at'],request_started_at=window['started_at'],http_status=j['metadata']['statusCode'],transport='Firecrawl CLI; metadata reports origin status',content_type=j['metadata']['contentType'],sha256=hashlib.sha256(fc.read_bytes()).hexdigest(),format_validation=dict(accepted=True,format='JSON envelope with official HTML and full judgment markdown',paragraphs='1–66 and operative part')))
(s/'cjeu-aci-adam.txt').write_text(j['markdown'])
manifest=E.parse(str(s/'official-manifest.xml'));ex=manifest.xpath('//expression[@label="2026-01-01_0"]')[0];valid={x.tag:x.text for x in ex.find('metadata')}
selected=dict(decisive_date='2026-10-19',authoring_started='2026-10-19',state='2026-01-01_0',effective_from=valid['datum_inwerkingtreding'],effective_until=valid['einddatum'],visible_from=valid['zichtdatum_start'],visible_until=valid['zichtdatum_eind'],last_modified=valid['tijdstip_laatste_wijziging'],basis='Official work manifest has no later expression and marks this expression effective through 9999-12-31. XML state inwerkingtreding agrees. Stb.2025-392 expressly commences the 2025-352 reform on 2026-01-01.',manifest_sha512=ex.findtext('manifestation/metadata/hashcode'),manifest_sha512_matches_download=ex.findtext('manifestation/metadata/hashcode')==hashlib.sha512((s/'intake-version.xml').read_bytes()).hexdigest(),changes_since_intake='No later state in official manifest; all 170 unit texts equal intake ignoring whitespace. XML includes official editorial notes separately.',limits='Date-specific wetten.nl front end returned 404; repository XML and official work manifest used. Future/unprocessed amendments outside the official manifest are not independently inventoried.')
assert selected['manifest_sha512_matches_download']
(s/'verification.json').write_text(json.dumps(dict(verification_date='2026-10-19',selection=selected,responses=records),ensure_ascii=False,indent=2))
# Retain local corpus source records without writing into intake.
local=[]
for slug,official in [('ecli-nl-hr-2008-bc2153.md','hr-endstra.xml'),('ecli-nl-hr-2013-by1529.md','hr-stokke.xml')]:
 src=Path('/Volumes/LaCie/law-intake/eu/nl/rechtspraak/hr')/slug;dest=s/('local-'+slug);dest.write_bytes(src.read_bytes());body=src.read_text()
 local.append(dict(path=str(src),snapshot='sources/'+dest.name,sha256=hashlib.sha256(src.read_bytes()).hexdigest(),official_comparison='Full official XML separately read; local corpus used for discovery and same-ECLI cross-check.',chars=len(body)))
(s/'local-corpus-selected.json').write_text(json.dumps(local,ensure_ascii=False,indent=2))
print('Verification complete:',len(records),'HTTP records; selected state',selected['state'])

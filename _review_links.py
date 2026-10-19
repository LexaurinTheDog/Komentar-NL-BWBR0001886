from pathlib import Path
from lxml import etree as E,html
import json,urllib.request,urllib.error,datetime,hashlib
P=Path(__file__).resolve().parent;p=P/'sources';records=[]
requests=[('review-links-endstra.xml','https://data.rechtspraak.nl/uitspraken/content?id=ECLI:NL:HR:2008:BC2153','hr-endstra.xml'),('review-links-stokke.xml','https://data.rechtspraak.nl/uitspraken/content?id=ECLI:NL:HR:2013:BY1529','hr-stokke.xml'),('review-links-wetten.html','https://wetten.overheid.nl/BWBR0001886/2026-01-01',None),('review-links-amendment.html','https://zoek.officielebekendmakingen.nl/stb-2025-352.html',None),('review-links-commencement.html','https://zoek.officielebekendmakingen.nl/stb-2025-392.html',None)]
for name,url,old in requests:
 rec=dict(url=url,accessed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
 try:
  try:r=urllib.request.urlopen(url,timeout=15)
  except urllib.error.HTTPError as e:r=e
  with r:b=r.read();status=r.status;ct=r.headers.get('Content-Type');final=r.url
  (p/name).write_bytes(b)
  rec.update(final_url=final,http_status=status,content_type=ct,path='sources/'+name,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
  if name.endswith('.xml'):
   root=E.fromstring(b);assert root.tag=='open-rechtspraak';ns={'r':'http://www.rechtspraak.nl/schema/rechtspraak-1.0'}
   fresh=''.join(root.find('r:uitspraak',ns).itertext());orig=''.join(E.parse(str(p/old)).find('r:uitspraak',ns).itertext());assert fresh==orig
   rec['format_validation']=dict(accepted=status==200,root_element=root.tag,judgment_body_matches_original=True)
  else:
   root=html.fromstring(b);title=root.xpath('string(//title)');accepted=status==200 and ('Auteurswet' in title if 'wetten.html' in name else 'Staatsblad' in title)
   rec['format_validation']=dict(accepted=accepted,title=title)
 except Exception as e:rec['error']=str(e);rec.setdefault('format_validation',dict(accepted=False))
 records.append(rec);(p/'review-links.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print(name,rec.get('http_status'),rec.get('format_validation'),flush=True)
print('Recorded',len(records),'responses')

"""Explicit public-source retrieval; downloaded originals stay outside Git."""
from pathlib import Path
import datetime, hashlib, json, urllib.request
ROOT = Path(__file__).resolve().parent
SOURCES = [
 ('ATI177', 'ATI manufacturer', 'https://www.atimaterials.com/Products/Documents/datasheets/stainless-specialty-steel/precipitationhardening/ati_17-7_tds_en_v2.pdf', 'pdf'),
 ('NACA4075', 'NACA original experimental report; UNT archive', 'https://digital.library.unt.edu/ark:/67531/metadc57021/m2/1/high_res_d/19930085071.pdf', 'pdf'),
 ('HPM177', 'Hamilton Precision Metals manufacturer', 'https://www.hpmetals.com/products/materials/stainless-steel-strip-foil/ss-17-7-ph', 'html'),
 ('ELG177', 'Elgiloy Specialty Metals manufacturer', 'https://www.elgiloy.com/strip-17-7-ph-stainless-steel', 'html'),
 ('NSK51102', 'NSK manufacturer', 'https://www.nsk.com/engineering/products/bearings/ball-bearings/thrust-ball-bearings/single-direction-thrust-ball-bearings/51102-apn.html', 'html'),
 ('E21', 'ASTM publisher public abstract only', 'https://store.astm.org/standards/e21', 'html'),
 ('E328', 'ASTM publisher public abstract only', 'https://store.astm.org/e0328-26.html', 'html'),
 ('G133', 'ASTM publisher public abstract only', 'https://store.astm.org/standards/g133', 'html'),
 ('NASA1228', 'NASA original fastener reference publication', 'https://ntrs.nasa.gov/citations/19900009424', 'html'),
]

def main():
    cache = ROOT/'source_cache'; cache.mkdir(exist_ok=True)
    rows = []
    for sid, authority, url, ext in SOURCES:
        row = {'id':sid, 'authority':authority, 'url':url,
               'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        try:
            request=urllib.request.Request(url, headers={'User-Agent':'PPR-Engineering-Research/1.0'})
            with urllib.request.urlopen(request, timeout=25) as response:
                data=response.read(15000000); row['final_url']=response.geturl()
            if ext=='pdf' and not data.startswith(b'%PDF'): raise ValueError('Not a PDF')
            path=cache/(sid+'.'+ext); path.write_bytes(data)
            row.update({'status':'FETCHED','bytes':len(data),
                        'sha256':hashlib.sha256(data).hexdigest(), 'cache_file':str(path.relative_to(ROOT))})
        except Exception as exc:
            row.update({'status':'FETCH_FAILED','error_type':type(exc).__name__})
        rows.append(row); print(sid,row['status'],flush=True)
    (ROOT/'sources.json').write_text(json.dumps({'kind':'PRIMARY_SOURCE_REGISTER',
        'physical_validation':'NOT_RUN','redistribution':'Original downloads excluded from Git and package; URL/hash/derived facts only',
        'scope':'Public documents; no paid standards, registration, supplier inquiry or certificate acquisition',
        'sources':rows},indent=2)+'\n')

if __name__=='__main__': main()

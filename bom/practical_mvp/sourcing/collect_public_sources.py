"""One bounded request per public source; no authentication or bypass."""
import csv,datetime,hashlib,json,urllib.request,urllib.parse
from pathlib import Path
HERE=Path(__file__).resolve().parent
SELECT={'MEGA-1001','BTS-ICBANQ','MAX6675-COUPANG','TT-GMP60-RFQ'}

def main():
    cache=HERE/'source_cache';cache.mkdir(exist_ok=True)
    rows=[]
    with (HERE/'price_observations.csv').open(encoding='utf-8',newline='') as f:
        sources=list(csv.DictReader(f))
    for source in sources:
        if source['source_id'] not in SELECT:continue
        url=urllib.parse.quote(source['url'],safe=':/?=&%')
        record={'source_id':source['source_id'],'url':source['url'],'requested_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        try:
            with urllib.request.urlopen(url,timeout=10) as response:
                data=response.read(4000001);kind=response.headers.get('Content-Type','')
                if len(data)>4000000:raise ValueError('Response exceeds bounded capture')
            suffix='.pdf' if data.startswith(b'%PDF') else '.html'
            path=cache/(source['source_id']+suffix);path.write_bytes(data)
            record.update(status='RESPONSE_CAPTURED_NOT_CHECKOUT',bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),cache=str(path.relative_to(HERE)),content_type=kind)
        except Exception as exc:
            record.update(status='FETCH_FAILED_NO_RETRY',error_type=type(exc).__name__,http_status=getattr(exc,'code',None))
        rows.append(record);print(record['source_id'],record['status'],flush=True)
    (HERE/'access_log.json').write_text(json.dumps({'bypass_attempted':False,'cache_is_not_price_or_stock_validation':True,'requests':rows},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()

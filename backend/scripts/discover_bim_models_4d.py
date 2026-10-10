"""Read-only account catalog discovery. Never imports an inference transport."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from app.services.ai.nebius_config import resolve
    config = resolve(timeout=45)
    out = ROOT / '.cad-proof-output' / ('4d-discovery-' + uuid4().hex)
    out.mkdir(parents=True)
    result = dict(timestamp=datetime.now(timezone.utc).isoformat(), endpoint=config.url('models'),
                  inferenceRequests=0, catalogRequests=1, models=[], status='UNKNOWN')
    try:
        with httpx.Client(timeout=45, follow_redirects=False) as client:
            response = client.get(config.url('models'), headers=config.headers())
        result['httpStatus'] = response.status_code
        if response.status_code == 200:
            data = response.json().get('data')
            if not isinstance(data, list):
                raise ValueError('CATALOG_SHAPE')
            result['models'] = sorted({row['id'] for row in data if isinstance(row, dict)
                                      and isinstance(row.get('id'), str)})
            result['status'] = 'CATALOG_LISTED_NOT_INFERENCE_VERIFIED'
        else:
            result['status'] = 'CATALOG_REJECTED'
    except Exception as exc:
        # Never retain HTTP bodies, exception messages, headers or credentials.
        result['status'] = 'CATALOG_FAILED'
        result['errorType'] = type(exc).__name__
    (out / 'catalog.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(result, evidence=str(out / 'catalog.json')), indent=2))


if __name__ == '__main__':
    main()

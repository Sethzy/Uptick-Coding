from io import StringIO
from crawler.output_writer import write_record
import json

def test_write_record_jsonl():
    buf = StringIO()
    rec = {"domain": "example.com", "pages": []}
    write_record(buf, rec)
    buf.seek(0)
    line = buf.read().strip()
    assert json.loads(line)["domain"] == "example.com"

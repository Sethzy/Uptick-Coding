from io import StringIO
from crawler.output_writer import write_record, write_record_with_status
import json

def test_write_record_jsonl():
    buf = StringIO()
    rec = {"domain": "example.com", "pages": []}
    write_record(buf, rec)
    buf.seek(0)
    line = buf.read().strip()
    assert json.loads(line)["domain"] == "example.com"

def test_write_record_with_status_success():
    buf = StringIO()
    rec = {"domain": "example.com", "aggregated_context": "content", "included_urls": ["https://example.com"]}
    write_record_with_status(buf, rec, "SUCCESS", None, 2)
    buf.seek(0)
    line = buf.read().strip()
    result = json.loads(line)
    
    # Check original fields are preserved
    assert result["domain"] == "example.com"
    assert result["aggregated_context"] == "content"
    assert result["included_urls"] == ["https://example.com"]
    
    # Check new status fields
    assert result["crawl_status"] == "SUCCESS"
    assert result["failure_reason"] is None
    assert result["pages_visited"] == 2

def test_write_record_with_status_fail():
    buf = StringIO()
    rec = {"domain": "failed-domain.com", "aggregated_context": "", "included_urls": []}
    write_record_with_status(buf, rec, "FAIL", "DNS_FAIL", 0)
    buf.seek(0)
    line = buf.read().strip()
    result = json.loads(line)
    
    # Check new status fields for failure case
    assert result["crawl_status"] == "FAIL"
    assert result["failure_reason"] == "DNS_FAIL"
    assert result["pages_visited"] == 0

def test_write_record_with_status_skipped():
    buf = StringIO()
    rec = {"domain": "blocked-domain.com", "aggregated_context": "", "included_urls": []}
    write_record_with_status(buf, rec, "SKIPPED", "ROBOT_DISALLOW", 0)
    buf.seek(0)
    line = buf.read().strip()
    result = json.loads(line)
    
    # Check new status fields for skipped case
    assert result["crawl_status"] == "SKIPPED"
    assert result["failure_reason"] == "ROBOT_DISALLOW"
    assert result["pages_visited"] == 0

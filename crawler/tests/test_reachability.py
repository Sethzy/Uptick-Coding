from crawler.reachability import normalize_domain


def test_normalize_domain_basic():
    assert normalize_domain('https://Example.COM/') == 'example.com'
    assert normalize_domain('www.foo-bar.io') == 'foo-bar.io'
    assert normalize_domain('foo.bar') == 'foo.bar'


def test_normalize_domain_invalid():
    assert normalize_domain('') is None
    assert normalize_domain('not a domain') is None
    assert normalize_domain('http://') is None

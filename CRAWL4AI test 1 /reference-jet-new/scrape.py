from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin, urlparse, urlunparse
import re
import unicodedata
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from fake_useragent import UserAgent
import validators
import asyncio
import hashlib
import requests
import json


def user_agent():
    def is_desktop(user_agent):
        mobile_keywords = ['Android', 'Mobile', 'iPhone', 'iPad']
        return not any(keyword in user_agent for keyword in mobile_keywords)
    ua = UserAgent()
    desktop_ua = ua.random
    while not is_desktop(desktop_ua):
        desktop_ua = ua.random
    return desktop_ua


def url2html(url):
    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'https://' + url
    ua = user_agent()
    headers = {'User-Agent': ua}
    response = requests.get(url, headers=headers,
                            timeout=7, allow_redirects=True)
    response.raise_for_status()
    return response.text


def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")

    [s.extract() for s in soup(['code', 'script', 'style', 'noscript'])]
    comments = soup.find_all(string=lambda string: isinstance(string, Comment))
    for comment in comments:
        comment.extract()

    for img in soup.find_all('img'):
        src = img.get('src', '').strip()
        if src and not src.startswith('data:'):
            cleaned_src = urlparse(src)._replace(
                query='', fragment='').geturl()
            img['src'] = cleaned_src
        elif src.startswith('data:'):
            img.decompose()

    for svg in soup.find_all('svg'):
        for element in svg.find_all():
            if element.name not in ['title', 'desc', 'metadata', 'svg']:
                element.decompose()

    return soup.prettify()


def clean_text(text):
    return ''.join(ch for ch in unicodedata.normalize('NFKD', text) if unicodedata.category(ch)[0] != 'C' or ch in ['\n', '\t', '\r'])


def html2text(html, include_urls=False, url=None):
    soup = BeautifulSoup(html, 'html.parser')

    canonical_tag = soup.find('link', {'rel': 'canonical'})
    if url and canonical_tag and canonical_tag.get('href'):
        url = canonical_tag['href']

    [s.extract() for s in soup(['code', 'script', 'style', 'noscript'])]
    comments = soup.find_all(string=lambda string: isinstance(string, Comment))
    for comment in comments:
        comment.extract()

    if include_urls and url and not (url.startswith('http://') or url.startswith('https://')):
        url = 'https://' + url

    base_domain = None
    if url:
        base_domain = urlparse(url).netloc.lstrip('www.')

    def is_ascii(s):
        return sum(ord(c) >= 128 for c in s) / len(s) < 0.1

    def traverse(node, depth=0):
        if node is None:
            return ''
        result = ''
        for child in node.children:
            if child.name is None:  # text node
                text = child.strip()
                if text:
                    if is_ascii(text):
                        text = re.sub(r'\s+', ' ', text)
                        result += text
            else:
                if child.name == 'button':
                    href = child.get('href', '')
                    onclick = child.get('onclick', '')
                    button_text = child.get_text().strip()
                    if href or onclick:
                        result += f"[Button: {button_text} href=\"{href}\" onclick=\"{onclick}\"]"
                    else:
                        result += button_text
                if child.name == 'img':
                    alt_text = child.get('alt', '').strip()
                    title_text = child.get('title', '').strip()
                    src = child.get('src', '').strip()
                    if src and not src.startswith('data:'):
                        # Handle relative URLs
                        if url and (src.startswith('/') or not src.startswith(('http://', 'https://'))):
                            src = urljoin(url, src)
                        src = urlparse(src)._replace(
                            query='', fragment='').geturl()
                        if title_text:
                            result += f"[Image: {title_text} ({src})]"
                        elif alt_text:
                            result += f"[Image: {alt_text} ({src})]"
                        else:
                            result += f"[Image: {src}]"
                    elif alt_text:
                        result += f"[Image: {alt_text}]"

                prefix = ' ' * depth
                postfix = '\n'
                link = ''
                if child.previous_sibling and child.previous_sibling.name in ["em", "strong"]:
                    prefix = ''
                if child.name == "em":
                    prefix = '*'
                    postfix = '*'
                elif child.name == "strong":
                    prefix = '**'
                    postfix = '**'
                elif child.next_sibling and child.next_sibling.name in ["em", "strong"]:
                    postfix = ' '
                if child.name == 'a':
                    href = child.get('href')
                    if include_urls and href:
                        link = ""
                        if url:
                            href = urljoin(url, href).split('#')[0].rstrip('/')
                        if not href.startswith("javascript:void(0)"):
                            if include_urls and url and base_domain:
                                link = f"[{child.text}]({href})"
                            if url is None:
                                link = f"[{child.text}]({href})"

                child_result = traverse(child, depth + 1)
                if child_result:
                    result += f"{prefix}{child_result}{link}{postfix}"
                else:
                    result += f"{prefix}{link}{postfix}"
        return result
    text = traverse(soup)
    lines = text.split("\n")
    counts = set(len(line) - len(line.lstrip()) for line in lines)
    sorted_counts = sorted(counts)
    flattener = {count: i for i, count in enumerate(sorted_counts)}
    result = ""
    for line in lines:
        count = len(line) - len(line.lstrip())
        result += ' ' * flattener[count] + line.lstrip() + '\n'
    lines = result.split("\n")
    lines = [line for line in lines if line.strip()]
    text = "\n".join(lines)
    text = clean_text(text)
    return text


def html2hrefs(html, url, include_external_domains=True):
    soup = BeautifulSoup(html, 'html.parser')
    base_domain = urlparse(url).netloc.lstrip('www.')
    base_name = base_domain.rsplit('.', 1)[0]

    # Define social media domains to exclude
    social_media_domains = {
        'linkedin.com', 'www.linkedin.com',
        'reddit.com', 'www.reddit.com',
        'facebook.com', 'www.facebook.com',
        'instagram.com', 'www.instagram.com',
        'youtube.com', 'www.youtube.com',
        'x.com', 'www.x.com', 'twitter.com', 'www.twitter.com'
    }

    def is_social_media_url(href):
        """Check if URL is from a social media platform"""
        try:
            parsed_href = urlparse(urljoin(url, href))
            domain = parsed_href.netloc.lower().lstrip('www.')
            return domain in social_media_domains
        except:
            return False

    if include_external_domains:
        # Include all valid URLs, regardless of domain, but exclude social media
        urls = {urljoin(url, a['href']) for a in soup.find_all('a', href=True)
                if not a['href'].startswith(('javascript:', 'mailto:', 'tel:', '#'))
                and not is_social_media_url(a['href'])}
    else:
        # Only include URLs within the same domain (original behavior)
        urls = {urljoin(url, a['href']) for a in soup.find_all('a', href=True)
                if base_name in urlparse(urljoin(url, a['href'])).netloc.lower()}

    return sorted(list(urls), key=lambda x: len(x))


async def scrape(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ua = user_agent()
        context = await browser.new_context(
            user_agent=ua,
            viewport={'width': 1280, 'height': 800},
            java_script_enabled=True,
            ignore_https_errors=True,
        )
        page = await context.new_page()
        await page.goto(url, wait_until='domcontentloaded', timeout=10_000)
        html = await page.content()
        title = await page.title()
        await browser.close()

    text = html2text(html, include_urls=True, url=url)
    text = f"{title} - {url}\n\n{text}"
    urls = html2hrefs(html, url)
    return text, urls


def normalize_url(url):
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    parsed = urlparse(url)
    scheme = 'https'
    netloc = parsed.netloc or parsed.path
    netloc = netloc.lower().lstrip('www.')
    path = parsed.path if parsed.netloc else ''
    path = path.rstrip('/')
    # normalized = urlunparse((scheme, netloc, path, '', '', ''))
    return f"{netloc}{path}"


def extract_domain(url):
    """
    Extract domain from various URL formats.

    Args:
        url (str): URL string in various formats

    Returns:
        str: Extracted domain without www prefix

    Examples:
        extract_domain("https://www.example.com/path") -> "example.com"
        extract_domain("http://example.com") -> "example.com"
        extract_domain("example.com") -> "example.com"
        extract_domain("www.example.com") -> "example.com"
        extract_domain("subdomain.example.com") -> "subdomain.example.com"
    """
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    parsed = urlparse(url)
    netloc = parsed.netloc or parsed.path

    # Handle cases where the URL might be just a domain without scheme
    if not netloc and parsed.path:
        # If netloc is empty but path exists, the path might be the domain
        netloc = parsed.path.split('/')[0]

    # Clean up the domain
    domain = netloc.lower().lstrip('www.')

    # Remove any trailing slashes or paths that might have been included
    domain = domain.split('/')[0]

    return domain


async def breadth_first_scrape(url, depth=2, visited=None, n=10):
    print("breadth_first_scrape:", url, depth, visited, n)
    if visited is None:
        visited = set()

    normalized_url = normalize_url(url)
    if normalized_url in visited:
        return []

    visited.add(normalized_url)
    texts = []

    # Scrape the initial URL (depth=0)
    print("scraping initial URL:", url)
    text, urls = await scrape(url)
    text = text[:7500]
    texts.append(text)

    if len(visited) >= n:
        return texts

    # Process each depth level
    current_depth_urls = urls
    for current_depth in range(1, depth + 1):
        if len(visited) >= n or not current_depth_urls:
            break

        print(
            f"processing depth {current_depth}, URLs to process: {len(current_depth_urls)}")

        # Sort URLs by length (number of characters)
        current_depth_urls = sorted(current_depth_urls, key=lambda x: len(x))

        # Collect all URLs from this depth level
        next_depth_urls = []

        # Scrape each URL at current depth
        for url_to_scrape in current_depth_urls:
            if len(visited) >= n:
                break

            normalized_scrape_url = normalize_url(url_to_scrape)
            if normalized_scrape_url in visited:
                continue

            visited.add(normalized_scrape_url)
            print(f"scraping depth {current_depth} URL:", url_to_scrape)

            try:
                text, new_urls = await scrape(url_to_scrape)
                text = text[:7500]
                texts.append(text)

                # Collect URLs for next depth
                next_depth_urls.extend(new_urls)

            except Exception as e:
                print(f"Error scraping {url_to_scrape}: {e}")
                continue

        # Set URLs for next iteration
        current_depth_urls = next_depth_urls

    return texts


async def scrape_website(url, depth=1, n=1):
    try:
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        if not validators.url(url) and not validators.domain(url):
            raise ValueError("Invalid URL: " + url)
        for use_https, use_www in [(True, True), (True, False), (False, True), (False, False)]:
            try:
                scheme, www = 'https' if use_https else 'http', 'www.' if use_www else ''
                parsed_url = urlparse(url)
                constructed_url = urlunparse(
                    (scheme, f"{www}{parsed_url.netloc.replace('www.', '')}", parsed_url.path, '', '', ''))
                return "\n\n\n\n".join(await breadth_first_scrape(constructed_url, depth=depth, n=n))
            except Exception as e:
                print(f"Error in scrape_website: {e}")
                continue
        raise ValueError("Invalid URL")
    except Exception as e:
        return f"Failed to scrape {url}: {e}"

if __name__ == "__main__":
    async def test():
        result = await scrape_website("https://agentscale.ai", depth=3, n=15)
        # print(result)

    asyncio.run(test())

import time
import threading
from collections import deque
from urllib.parse import urljoin, urlparse

import nltk
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import close_old_connections

from crawler.models import Domain, Insight, Page

# Download NLTK data on first run
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

STOP_WORDS = set(stopwords.words('english'))


def _run_playwright_in_thread(url: str, result: dict):
    """
    Runs Playwright inside a plain OS thread so its internal event loop
    does NOT interfere with Django's sync-only ORM calls.
    Populates `result` with {'html', 'status_code'} or {'error'}.
    """
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent='Mozilla/5.0 (compatible; SEOCrawlerBot/1.0)'
        )
        try:
            response = page.goto(url, wait_until='networkidle', timeout=30_000)
            result['status_code'] = response.status if response else None
            result['html'] = page.content()
        except Exception as exc:
            result['error'] = str(exc)
        finally:
            browser.close()


class Command(BaseCommand):
    help = 'Crawl a domain and extract SEO insights for each page.'

    def add_arguments(self, parser):
        parser.add_argument('domain', type=str, help='Domain to crawl (e.g. example.com)')
        parser.add_argument('--max-pages', type=int, default=50,
                            help='Maximum number of pages to crawl (default: 50)')
        parser.add_argument('--delay', type=float, default=1.0,
                            help='Delay in seconds between requests (default: 1.0)')

    def handle(self, *args, **options):
        raw_domain = options['domain'].strip().rstrip('/')
        max_pages = options['max_pages']
        delay = options['delay']

        # Normalise domain — strip scheme if provided
        if raw_domain.startswith(('http://', 'https://')):
            parsed = urlparse(raw_domain)
            domain_name = parsed.netloc
            start_url = raw_domain
        else:
            domain_name = raw_domain
            start_url = f'https://{raw_domain}'

        self.stdout.write(self.style.SUCCESS(f'Starting crawl for: {domain_name}'))

        domain_obj, created = Domain.objects.get_or_create(domain_name=domain_name)
        self.stdout.write(
            f'{"Created new" if created else "Found existing"} domain record: {domain_name}'
        )

        disallowed_paths = self._fetch_robots_txt(start_url)
        self.stdout.write(f'Disallowed paths from robots.txt: {len(disallowed_paths)}')

        sitemap_urls = self._fetch_sitemap(start_url, domain_name)
        self.stdout.write(f'Found {len(sitemap_urls)} URLs in sitemap')

        queue = deque([start_url] + sitemap_urls)
        visited: set = set()
        crawled_count = 0

        while queue and crawled_count < max_pages:
            url = self._normalise_url(queue.popleft())

            if not url or url in visited:
                continue
            if not self._is_same_domain(url, domain_name):
                continue
            if self._is_disallowed(url, disallowed_paths):
                self.stdout.write(f'  Skipping (robots.txt): {url}')
                continue

            visited.add(url)
            self.stdout.write(f'[{crawled_count + 1}/{max_pages}] Crawling: {url}')

            # ── Playwright runs in its own thread to avoid the async-context
            #    error that occurs when sync_playwright is called from within
            #    Django's management command environment. ──────────────────
            result: dict = {}
            t = threading.Thread(target=_run_playwright_in_thread, args=(url, result))
            t.start()
            t.join()

            if 'error' in result:
                self.stdout.write(self.style.WARNING(f'  Error: {result["error"]}'))
                Page.objects.update_or_create(
                    domain=domain_obj, url=url,
                    defaults={'status_code': None},
                )
                crawled_count += 1
                time.sleep(delay)
                continue

            html = result.get('html', '')
            status_code = result.get('status_code')

            # ── All ORM calls stay on the main thread (sync-safe) ────────
            close_old_connections()
            page_obj, _ = Page.objects.update_or_create(
                domain=domain_obj,
                url=url,
                defaults={'status_code': status_code},
            )

            if html and status_code == 200:
                soup = BeautifulSoup(html, 'html.parser')
                insights = self._extract_insights(soup, domain_name)

                Insight.objects.update_or_create(
                    page=page_obj,
                    defaults=insights,
                )

                for link in self._extract_internal_links(soup, url, domain_name):
                    if link not in visited:
                        queue.append(link)

            crawled_count += 1
            time.sleep(delay)

        self.stdout.write(self.style.SUCCESS(f'Crawl complete. {crawled_count} pages processed.'))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fetch_robots_txt(self, base_url: str) -> list:
        """Return a list of disallowed path prefixes from robots.txt."""
        disallowed = []
        try:
            resp = requests.get(f'{base_url}/robots.txt', timeout=10)
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    line = line.strip()
                    if line.lower().startswith('disallow:'):
                        path = line.split(':', 1)[1].strip()
                        if path:
                            disallowed.append(path)
        except Exception:
            pass
        return disallowed

    def _fetch_sitemap(self, base_url: str, domain_name: str) -> list:
        """Return URLs found in sitemap.xml."""
        urls = []
        try:
            resp = requests.get(f'{base_url}/sitemap.xml', timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'xml')
                for loc in soup.find_all('loc'):
                    url = loc.get_text(strip=True)
                    if self._is_same_domain(url, domain_name):
                        urls.append(url)
        except Exception:
            pass
        return urls

    def _extract_insights(self, soup: BeautifulSoup, domain_name: str) -> dict:
        """Parse a BeautifulSoup object and return an insights dict."""
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else None

        meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc_tag.get('content', '').strip() if meta_desc_tag else None

        h1 = [tag.get_text(strip=True) for tag in soup.find_all('h1')]
        h2 = [tag.get_text(strip=True) for tag in soup.find_all('h2')]
        h3 = [tag.get_text(strip=True) for tag in soup.find_all('h3')]

        p_count = len(soup.find_all('p'))
        image_count = len(soup.find_all('img'))

        internal_links = 0
        external_links = 0
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if not href or href.startswith('#') or href.startswith('mailto:'):
                continue
            if href.startswith('/') or domain_name in href:
                internal_links += 1
            elif href.startswith('http'):
                external_links += 1
            else:
                internal_links += 1  # relative links

        keywords = self._extract_keywords(soup)

        return {
            'title': title,
            'meta_description': meta_description,
            'h1': h1,
            'h2': h2,
            'h3': h3,
            'p_count': p_count,
            'image_count': image_count,
            'internal_links': internal_links,
            'external_links': external_links,
            'keywords': keywords,
        }

    def _extract_keywords(self, soup: BeautifulSoup) -> list:
        """Extract top-10 keywords with density from visible page text."""
        # Remove script/style tags
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()

        text = soup.get_text(separator=' ', strip=True)
        tokens = word_tokenize(text.lower())
        # Keep only alphabetic words, remove stopwords
        words = [
            w for w in tokens
            if w.isalpha() and w not in STOP_WORDS and len(w) > 2
        ]

        if not words:
            return []

        total = len(words)
        freq: dict = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1

        top10 = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
        return [
            {'keyword': kw, 'density': round((count / total) * 100, 2)}
            for kw, count in top10
        ]

    def _extract_internal_links(self, soup: BeautifulSoup, current_url: str, domain_name: str) -> list:
        """Return a list of absolute internal URLs found on the page."""
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if not href or href.startswith('#') or href.startswith('mailto:'):
                continue
            full_url = urljoin(current_url, href)
            if self._is_same_domain(full_url, domain_name):
                links.append(self._normalise_url(full_url))
        return links

    def _is_same_domain(self, url: str, domain_name: str) -> bool:
        try:
            parsed = urlparse(url)
            return domain_name in parsed.netloc
        except Exception:
            return False

    def _is_disallowed(self, url: str, disallowed_paths: list) -> bool:
        parsed = urlparse(url)
        path = parsed.path
        for disallowed in disallowed_paths:
            if path.startswith(disallowed):
                return True
        return False

    def _normalise_url(self, url: str) -> str:
        """Strip fragments and trailing slashes for deduplication."""
        try:
            parsed = urlparse(url)
            # Drop fragment
            clean = parsed._replace(fragment='').geturl()
            return clean.rstrip('/')
        except Exception:
            return ''

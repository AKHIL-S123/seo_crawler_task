# Website SEO Crawler & Insights API

A Django-based SEO crawler that crawls a given domain, extracts key SEO insights from each page, and exposes the stored data via a REST API.

---

## Tech Stack

| Component | Library |
|-----------|---------|
| Web Framework | Django 4.x |
| REST API | Django REST Framework |
| Database | PostgreSQL (MySQL also supported) |
| JS Rendering | Playwright (Chromium) |
| HTML Parsing | BeautifulSoup4 |
| Keyword Extraction | NLTK |
| HTTP Requests | Requests |

---

## Project Structure

```
seo_crawler/
├── manage.py
├── requirements.txt
├── README.md
├── seo_crawler/            # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── crawler/                # Models + crawl management command
│   ├── admin.py
│   ├── models.py
│   └── management/
│       └── commands/
│           └── crawl.py
└── api/                    # DRF views, serializers, URLs
    ├── pagination.py
    ├── serializers.py
    ├── urls.py
    └── views.py
```

---

## Setup Instructions

### 1. Prerequisites

- Python 3.10+
- PostgreSQL (or MySQL)

### 2. Clone & Create Virtual Environment

```bash
git clone <your-repo-url>
cd seo_crawler
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

> **MySQL users:** Uncomment `mysqlclient` in `requirements.txt` and update `DATABASES` in `settings.py`.

### 4. Install Playwright Browser

```bash
playwright install chromium
```

### 5. Download NLTK Data

```bash
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"
```

### 6. Configure the Database

Create the database in PostgreSQL:

```sql
CREATE DATABASE seo_crawler_db;
```

Then set environment variables (or edit `settings.py` directly):

```bash
export DB_NAME=seo_crawler_db
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=5432
```

### 7. Run Migrations

```bash
python manage.py migrate
```

### 8. (Optional) Create a Superuser for Django Admin

```bash
python manage.py createsuperuser
```

---

## How to Run

### Start the Development Server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

### Run the Crawler

```bash
# Basic usage
python manage.py crawl example.com

# With options
python manage.py crawl www.example.com --max-pages 100 --delay 1.5

# Full URL also accepted
python manage.py crawl https://example.com --max-pages 20
```

**Crawler Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `domain` | — | Domain to crawl (required) |
| `--max-pages` | 50 | Maximum pages to crawl |
| `--delay` | 1.0 | Seconds between requests (be polite!) |

---

## API Endpoints

### `GET /domains/`
Lists all crawled domains.

**Query Parameters:** `?page=1&page_size=10`

---

### `GET /domains/{id}/pages/`
Lists all pages for a specific domain.

**Query Parameters:** `?page=1&page_size=10`

---

### `GET /pages/{id}/insights/`
Returns detailed SEO insights for a single page.

---

## Example curl Requests

### List all domains
```bash
curl -X GET "http://127.0.0.1:8000/domains/" \
  -H "Accept: application/json"
```

### List domains with pagination
```bash
curl -X GET "http://127.0.0.1:8000/domains/?page=1&page_size=5" \
  -H "Accept: application/json"
```

### List pages for domain ID 1
```bash
curl -X GET "http://127.0.0.1:8000/domains/1/pages/" \
  -H "Accept: application/json"
```

### List pages with pagination
```bash
curl -X GET "http://127.0.0.1:8000/domains/1/pages/?page=1&page_size=10" \
  -H "Accept: application/json"
```

### Get SEO insights for page ID 101
```bash
curl -X GET "http://127.0.0.1:8000/pages/101/insights/" \
  -H "Accept: application/json"
```

---

## Example API Responses

### `GET /domains/`
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    { "id": 1, "domain_name": "example.com", "created_at": "2024-01-15T10:00:00Z" },
    { "id": 2, "domain_name": "anotherdomain.org", "created_at": "2024-01-14T09:00:00Z" }
  ]
}
```

### `GET /domains/1/pages/`
```json
{
  "count": 50,
  "next": "http://127.0.0.1:8000/domains/1/pages/?page=2",
  "previous": null,
  "results": [
    { "id": 101, "url": "https://example.com/", "status_code": 200, "crawled_at": "2024-01-15T10:05:00Z" },
    { "id": 102, "url": "https://example.com/about", "status_code": 200, "crawled_at": "2024-01-15T10:06:00Z" }
  ]
}
```

### `GET /pages/101/insights/`
```json
{
  "title": "Welcome to Our Website",
  "meta_description": "We offer a wide range of services...",
  "h1": ["Welcome"],
  "h2": ["About Us", "Our Services"],
  "h3": [],
  "p_count": 15,
  "image_count": 5,
  "internal_links": 12,
  "external_links": 3,
  "keywords": [
    { "keyword": "services", "density": 2.5 },
    { "keyword": "website", "density": 1.8 }
  ]
}
```

---

## Django Admin

Visit `http://127.0.0.1:8000/admin/` to browse and manage Domains, Pages, and Insights through Django's built-in admin interface.

---

## Notes

- The crawler respects `robots.txt` — disallowed paths are skipped automatically.
- The sitemap (`/sitemap.xml`) is used to seed the initial URL queue.
- Playwright renders JavaScript before parsing, so single-page applications are fully supported.
- Keyword density is calculated as `(keyword_count / total_word_count) * 100`.
- Common English stopwords are removed before keyword analysis using NLTK.

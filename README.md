# Product Search, Comparison & Digest Generator

A modular Python web application that validates user search queries, discovers relevant vendor sources, scrapes and cleans product listings concurrently, compares matching products across vendors, filters and sorts results, generates concise summary digests, and links back to original source pages.

## Project Structure

- `app.py` — Web server and HTML/CSS user interface rendering search results, comparison tables, and digests.
- `scraper.py` — Query validation, source configuration loading, website discovery, and concurrent page fetching.
- `parser.py` — HTML cleaning/parsing, product normalization, relevance scoring, and cross-site product grouping.
- `digest_generator.py` — Filtering, sorting, comparison matrix construction, and summary digest generation.
- `generate_catalog.py` — Script to generate sample vendor HTML pages and `sources.json` catalog data.
- `sources.json` — External configuration of vendor sources, URLs, and keywords.
- `sample_sites/` — Sample multi-vendor HTML pages used for testing and local demonstrations.
- `test_suite.py` — Automated `unittest` suite (`TC01`–`TC10`).

## How to Run Locally (Windows)

1. Open PowerShell inside the `product_digest_app` folder.
2. Run the automated test suite:
   ```powershell
   py test_suite.py

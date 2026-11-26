import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from scraper import validate_query, discover_websites, scrape_websites_concurrently
from parser import parse_scraped_pages, match_products_across_sites
from digest_generator import filter_and_sort_products, build_comparison_matrix, generate_summary_digest


def render_page(query="", sort_by="price_asc", min_rating="0", only_stock=False, show_digest=False):
    status_html = digest_html = cards_html = matrix_html = ""

    if query:
        ok, msg, params = validate_query(query)
        if not ok:
            status_html = f'<div class="alert error">{html.escape(msg)}</div>'
        else:
            sites = discover_websites(params, "sources.json")
            successes, failures = scrape_websites_concurrently(sites, max_workers=6, timeout=2.0)
            records = parse_scraped_pages(successes, params["tokens"])
            filtered = filter_and_sort_products(
                records,
                max_price=params["max_price"],
                min_rating=float(min_rating or 0),
                only_in_stock=only_stock,
                sort_by=sort_by,
            )
            grouped = match_products_across_sites(filtered)
            matrix = build_comparison_matrix(grouped)

            status_html = (
                f'<div class="alert info">Found {len(sites)} matching website(s); '
                f'scraped {len(successes)} successfully ({len(failures)} unreachable). '
                f'Showing {len(filtered)} product listing(s) across {len(matrix)} unique product(s).</div>'
            )

            if show_digest:
                digest_text = generate_summary_digest(filtered, matrix, failures)
                digest_html = f'<section class="card digest"><h2>Summary Digest (FR9)</h2><p>{html.escape(digest_text)}</p></section>'

            card_items = []
            for r in filtered:
                card_items.append(f"""
                <div class="product-card">
                  <h3>{html.escape(r.title)}</h3>
                  <p class="desc">{html.escape(r.description)}</p>
                  <p><strong>Price:</strong> Rs. {r.price:.0f} | <strong>Rating:</strong> {r.rating} &#9733; ({r.reviews} reviews) | <strong>Availability:</strong> {html.escape(r.availability)}</p>
                  <a href="{html.escape(r.source_url)}" target="_blank" rel="noopener noreferrer">View original page at {html.escape(r.source_name)}</a>
                </div>""")
            cards_html = f'<section><h2>Scraped Products (FR3, FR7, FR10)</h2><div class="grid">{"".join(card_items) or "<p>No matching products.</p>"}</div></section>'

            rows = []
            for item in matrix:
                vendor_cells = "<br>".join(
                    f'{html.escape(o["source_name"])}: Rs. {o["price"]:.0f} ({o["rating"]}&#9733;, {html.escape(o["availability"])})'
                    for o in item["offers"]
                )
                rows.append(f"""
                <tr>
                  <td>{html.escape(item["product_title"])}</td>
                  <td>Rs. {item["lowest_price"]:.0f} ({html.escape(item["lowest_price_vendor"])})</td>
                  <td>{item["highest_rating"]} &#9733; ({html.escape(item["highest_rating_vendor"])})</td>
                  <td>{vendor_cells}</td>
                </tr>""")
            if rows:
                matrix_html = f"""
                <section>
                  <h2>Cross-Site Comparison Matrix (FR4, FR5, FR8)</h2>
                  <table>
                    <thead><tr><th>Product</th><th>Best Price</th><th>Top Rating</th><th>Vendor Breakdown</th></tr></thead>
                    <tbody>{"".join(rows)}</tbody>
                  </table>
                </section>"""

    stock_checked = "checked" if only_stock else ""
    split_sections = ""
    if query and ok:
        split_sections = f"""
        <div class="split-grid">
          <div>{matrix_html}</div>
          <div>{cards_html}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><title>Product Search, Comparison &amp; Digest Generator</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f0fdf4; color: #1e293b; margin: 0; }}
    header.mint-nav {{ background: #134e4a; color: #f0fdfa; padding: 16px 28px; display: flex; justify-content: space-between; align-items: center; }}
    header.mint-nav h1 {{ margin: 0; font-size: 20px; }}
    header.mint-nav span {{ background: #0f766e; padding: 4px 10px; border-radius: 6px; font-size: 12px; color: #ccfbf1; }}
    .container {{ max-width: 1220px; margin: 20px auto; padding: 0 18px; }}
    form.pill-bar {{ display: flex; flex-wrap: wrap; gap: 10px; background: #ffffff; border: 1px solid #bbf7d0; padding: 14px; border-radius: 14px; align-items: center; }}
    input[type="text"] {{ flex: 1; min-width: 240px; padding: 9px 12px; border: 1px solid #cbd5e1; border-radius: 999px; }}
    select {{ padding: 9px 12px; border: 1px solid #cbd5e1; border-radius: 999px; background: #fff; }}
    label.pill-chk {{ font-size: 13px; background: #f8fafc; border: 1px solid #e2e8f0; padding: 8px 12px; border-radius: 999px; }}
    button {{ border: none; padding: 9px 15px; border-radius: 999px; font-weight: 600; cursor: pointer; background: #0d9488; color: #fff; }}
    button[value="1"] {{ background: #1e293b; }}
    .alert {{ padding: 11px 15px; border-radius: 10px; margin: 14px 0; font-size: 14px; }}
    .info {{ background: #ccfbf1; border-left: 4px solid #0d9488; color: #115e59; }}
    .error {{ background: #fee2e2; border-left: 4px solid #dc2626; color: #991b1b; }}
    .digest {{ background: #ffffff; border: 1px solid #99f6e4; border-left: 5px solid #0f766e; padding: 14px 18px; border-radius: 10px; margin: 14px 0; }}
    .digest h2 {{ margin: 0 0 6px; font-size: 16px; color: #115e59; }}
    .split-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; margin-top: 10px; }}
    h2 {{ font-size: 17px; color: #134e4a; margin: 16px 0 10px; }}
    .grid {{ display: flex; flex-direction: column; gap: 10px; }}
    .product-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 14px; }}
    .product-card h3 {{ margin: 0 0 5px; font-size: 15px; color: #0f172a; }}
    .product-card a {{ color: #0f766e; font-weight: 600; font-size: 13px; text-decoration: none; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 10px; overflow: hidden; }}
    th, td {{ border: 1px solid #e2e8f0; padding: 8px 10px; text-align: left; vertical-align: top; font-size: 13px; }}
    th {{ background: #f0fdfa; color: #115e59; }}
    @media (max-width: 900px) {{ .split-grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header class="mint-nav">
    <h1>Product Search, Comparison &amp; Digest Generator</h1>
    <span>MULTI-SOURCE DIGEST</span>
  </header>
  <div class="container">
    <form class="pill-bar" method="GET" action="/">
      <input type="text" name="q" value="{html.escape(query)}" placeholder="Search e.g. Air Fryer, Running Shoes, Smartphone under 30000" required />
      <select name="sort">
        <option value="price_asc" {"selected" if sort_by=="price_asc" else ""}>Lowest Price</option>
        <option value="price_desc" {"selected" if sort_by=="price_desc" else ""}>Highest Price</option>
        <option value="rating_desc" {"selected" if sort_by=="rating_desc" else ""}>Highest Rating</option>
        <option value="recommended" {"selected" if sort_by=="recommended" else ""}>Recommended</option>
      </select>
      <select name="min_rating">
        <option value="0" {"selected" if min_rating=="0" else ""}>Any Rating</option>
        <option value="4.0" {"selected" if min_rating=="4.0" else ""}>Rating &ge; 4 &#9733;</option>
        <option value="4.5" {"selected" if min_rating=="4.5" else ""}>Rating &ge; 4.5 &#9733;</option>
      </select>
      <label class="pill-chk"><input type="checkbox" name="in_stock" value="1" {stock_checked}/> In Stock Only</label>
      <button type="submit" name="digest" value="0">Search</button>
      <button type="submit" name="digest" value="1">Generate Summary Report</button>
    </form>
    {status_html if not (query and ok) else ""}
    {digest_html}
    {status_html if (query and ok) else ""}
    {split_sections}
  </div>
</body>
</html>"""


class DigestRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        page = render_page(
            query=qs.get("q", [""])[0],
            sort_by=qs.get("sort", ["price_asc"])[0],
            min_rating=qs.get("min_rating", ["0"])[0],
            only_stock=qs.get("in_stock", ["0"])[0] == "1",
            show_digest=qs.get("digest", ["0"])[0] == "1",
        )
        body = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), DigestRequestHandler)
    print("Server running at http://127.0.0.1:8000")
    server.serve_forever()

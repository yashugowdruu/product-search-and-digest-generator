import unittest
from scraper import validate_query, discover_websites, scrape_websites_concurrently
from parser import parse_scraped_pages, match_products_across_sites
from digest_generator import filter_and_sort_products, build_comparison_matrix, generate_summary_digest


class TestProductDigestSystem(unittest.TestCase):
    CONFIG = "sources.json"

    def test_TC01_valid_query_and_price_extraction_FR1(self):
        ok, _, params = validate_query("Mechanical Keyboard under 6000")
        self.assertTrue(ok)
        self.assertEqual(params["max_price"], 6000.0)
        self.assertIn("keyboard", params["tokens"])

    def test_TC02_empty_and_invalid_query_FR1(self):
        ok1, _, _ = validate_query("   ")
        ok2, _, _ = validate_query("!!!")
        self.assertFalse(ok1)
        self.assertFalse(ok2)

    def test_TC03_website_discovery_and_config_FR2_NFR5(self):
        _, _, params = validate_query("Mechanical Keyboard")
        sites = discover_websites(params, self.CONFIG)
        self.assertGreaterEqual(len(sites), 3)
        names = [s["name"] for s in sites]
        self.assertIn("TechKart", names)
        self.assertIn("MegaStore", names)

    def test_TC04_concurrent_scraping_and_fault_tolerance_NFR1_NFR4(self):
        _, _, params = validate_query("Mechanical Keyboard")
        sites = discover_websites(params, self.CONFIG)
        successes, failures = scrape_websites_concurrently(sites, max_workers=6, timeout=1.0)
        self.assertEqual(len(successes), 3)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["name"], "UnreachableVendor")

    def test_TC05_html_cleaning_and_extraction_FR3_FR7_FR10(self):
        _, _, params = validate_query("Mechanical Keyboard")
        sites = discover_websites(params, self.CONFIG)
        successes, _ = scrape_websites_concurrently(sites, timeout=1.0)
        records = parse_scraped_pages(successes, params["tokens"])
        self.assertEqual(len(records), 5)
        for rec in records:
            self.assertNotIn("BUY NOW AD", rec.description)
            self.assertNotIn("Sponsored Ad", rec.description)
            self.assertGreater(rec.price, 0)
            self.assertTrue(rec.source_url.startswith("https://"))

    def test_TC06_cross_site_matching_and_comparison_FR4_FR5_FR8(self):
        _, _, params = validate_query("Mechanical Keyboard")
        sites = discover_websites(params, self.CONFIG)
        successes, _ = scrape_websites_concurrently(sites, timeout=1.0)
        records = parse_scraped_pages(successes, params["tokens"])
        grouped = match_products_across_sites(records)
        matrix = build_comparison_matrix(grouped)
        logitech = next(m for m in matrix if "Logitech" in m["product_title"])
        self.assertEqual(logitech["vendor_count"], 3)
        self.assertEqual(logitech["lowest_price"], 5700.0)
        self.assertEqual(logitech["lowest_price_vendor"], "TechKart")
        self.assertEqual(logitech["highest_rating"], 4.7)

    def test_TC07_filtering_and_sorting_FR6(self):
        _, _, params = validate_query("Mechanical Keyboard under 6000")
        sites = discover_websites(params, self.CONFIG)
        successes, _ = scrape_websites_concurrently(sites, timeout=1.0)
        records = parse_scraped_pages(successes, params["tokens"])
        filtered = filter_and_sort_products(
            records, max_price=params["max_price"], min_rating=4.0, only_in_stock=True, sort_by="price_asc"
        )
        self.assertTrue(all(r.price <= 6000 and r.rating >= 4.0 and r.availability == "In Stock" for r in filtered))
        prices = [r.price for r in filtered]
        self.assertEqual(prices, sorted(prices))

    def test_TC08_summary_digest_generation_FR9(self):
        _, _, params = validate_query("Mechanical Keyboard")
        sites = discover_websites(params, self.CONFIG)
        successes, failures = scrape_websites_concurrently(sites, timeout=1.0)
        records = parse_scraped_pages(successes, params["tokens"])
        grouped = match_products_across_sites(records)
        matrix = build_comparison_matrix(grouped)
        digest = generate_summary_digest(records, matrix, failures)
        self.assertIn("Best Price", digest)
        self.assertIn("Highest Rated", digest)
        self.assertIn("UnreachableVendor", digest)

    def test_TC09_large_catalog_min_two_comparable_websites(self):
        """Verify >=108 unique general products exist and EVERY product appears on >=2 comparable websites."""
        ok, _, params = validate_query("cheap")
        self.assertTrue(ok)
        self.assertEqual(params["tokens"], [])
        sites = discover_websites(params, self.CONFIG)
        successes, _ = scrape_websites_concurrently(sites, max_workers=6, timeout=1.0)
        records = parse_scraped_pages(successes, params["tokens"])
        grouped = match_products_across_sites(records)
        self.assertGreaterEqual(len(grouped), 113)
        for key, offers in grouped.items():
            unique_vendors = {o.source_name for o in offers}
            self.assertGreaterEqual(len(unique_vendors), 2, f"Product {key} has fewer than 2 vendors")

    def test_TC10_general_category_queries_and_stopwords(self):
        """Verify natural-language and diverse general product queries return comparable results."""
        for query in ["best smartphone under 30000", "air fryer", "running shoes", "water bottle", "smartwatch", "ssd"]:
            ok, _, params = validate_query(query)
            self.assertTrue(ok)
            sites = discover_websites(params, self.CONFIG)
            successes, _ = scrape_websites_concurrently(sites, max_workers=6, timeout=1.0)
            records = parse_scraped_pages(successes, params["tokens"])
            filtered = filter_and_sort_products(records, max_price=params["max_price"], sort_by="price_asc")
            grouped = match_products_across_sites(filtered)
            self.assertGreaterEqual(len(grouped), 1, f"No matches for {query}")
            for offers in grouped.values():
                self.assertGreaterEqual(len({o.source_name for o in offers}), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)

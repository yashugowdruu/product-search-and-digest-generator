import re
from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from typing import Dict, List


@dataclass
class ProductRecord:
    title: str
    normalized_key: str
    description: str
    price: float
    rating: float
    reviews: int
    availability: str
    source_name: str
    source_url: str
    relevance: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)


class CleanProductHTMLParser(HTMLParser):
    """FR3: Extracts product data while stripping nav, aside, footer, header, script, style, and ad blocks."""

    IGNORED_TAGS = {"script", "style", "nav", "aside", "footer", "header"}

    def __init__(self, source_name: str, default_url: str):
        super().__init__()
        self.source_name = source_name
        self.default_url = default_url
        self.ignore_depth = 0
        self.in_product = False
        self.current_field = None
        self.current_product = None
        self.products: List[Dict] = []

    def handle_starttag(self, tag: str, attrs: List):
        attr_dict = dict(attrs)
        cls = attr_dict.get("class", "").lower()
        if tag in self.IGNORED_TAGS or "ad" in cls.split() or "sidebar" in cls:
            self.ignore_depth += 1
            return
        if self.ignore_depth > 0:
            return

        if tag == "article" and "product" in cls:
            self.in_product = True
            self.current_product = {
                "title": "",
                "description": "",
                "price": float(attr_dict.get("data-price", 0.0)),
                "rating": float(attr_dict.get("data-rating", 0.0)),
                "reviews": int(attr_dict.get("data-reviews", 0)),
                "availability": attr_dict.get("data-availability", "Unknown"),
                "source_name": self.source_name,
                "source_url": self.default_url,
            }
        elif self.in_product:
            if "title" in cls:
                self.current_field = "title"
            elif "desc" in cls:
                self.current_field = "description"
            elif tag == "a" and "product-url" in cls and "href" in attr_dict:
                self.current_product["source_url"] = attr_dict["href"]

    def handle_endtag(self, tag: str):
        if self.ignore_depth > 0:
            if tag in self.IGNORED_TAGS or tag in {"div"}:
                self.ignore_depth = max(0, self.ignore_depth - 1)
            return
        if self.in_product:
            if tag == "article":
                self.products.append(self.current_product)
                self.in_product = False
                self.current_product = None
                self.current_field = None
            elif self.current_field and tag in {"h1", "h2", "h3", "p", "span"}:
                self.current_field = None

    def handle_data(self, data: str):
        if self.ignore_depth > 0 or not self.in_product or not self.current_field:
            return
        text = data.strip()
        if text:
            prev = self.current_product[self.current_field]
            self.current_product[self.current_field] = f"{prev} {text}".strip()


def normalize_product_name(title: str) -> str:
    """Create a canonical key for matching identical products across different sites (FR4)."""
    cleaned = re.sub(r"[^a-z0-9\s]", "", title.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def compute_relevance(title: str, description: str, tokens: List[str]) -> float:
    if not tokens:
        return 1.0
    haystack = f"{title} {description}".lower()
    hits = sum(1 for t in tokens if t in haystack)
    return round(hits / len(tokens), 2)


def parse_scraped_pages(pages: List[Dict], query_tokens: List[str]) -> List[ProductRecord]:
    """FR3 & FR7: Parse scraped HTML into clean ProductRecord objects."""
    records: List[ProductRecord] = []
    for page in pages:
        parser = CleanProductHTMLParser(page["name"], page["url"])
        parser.feed(page["html"])
        for item in parser.products:
            rel = compute_relevance(item["title"], item["description"], query_tokens)
            if rel == 1.0:
                records.append(ProductRecord(
                    title=item["title"],
                    normalized_key=normalize_product_name(item["title"]),
                    description=item["description"],
                    price=item["price"],
                    rating=item["rating"],
                    reviews=item["reviews"],
                    availability=item["availability"],
                    source_name=item["source_name"],
                    source_url=item["source_url"],
                    relevance=rel,
                ))
    return records


def match_products_across_sites(records: List[ProductRecord]) -> Dict[str, List[ProductRecord]]:
    """FR4: Group matching products available across different websites."""
    grouped: Dict[str, List[ProductRecord]] = {}
    for rec in records:
        grouped.setdefault(rec.normalized_key, []).append(rec)
    return grouped
